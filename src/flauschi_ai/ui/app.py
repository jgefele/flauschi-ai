from datetime import date

import streamlit as st
from langchain_core.documents import Document

from flauschi_ai.models import ChunkMetadata
from flauschi_ai.vectorstore import FlauschiVectorStore
from flauschi_ai.utils import format_timecode

st.set_page_config(
    page_title="Flauschi retrieval", page_icon=":material/mic:", layout="wide"
)

st.session_state.setdefault("results", None)
st.session_state.setdefault("last_params", None)
st.session_state.setdefault("searched", False)


@st.cache_resource(show_spinner="Loading vector store…")
def get_vector_store() -> FlauschiVectorStore:
    return FlauschiVectorStore.default()


@st.cache_data(ttl="1h", max_entries=100, show_spinner="Retrieving chunks…")
def cached_retrieve(
    query: str, k: int, published_after: date | None, published_before: date | None
) -> list[Document]:
    return get_vector_store().retrieve(query, k, published_after, published_before)


st.title("Flauschi retrieval", icon=":material/mic:")
st.caption("Search podcast transcript chunks via hybrid retrieval with Qdrant.")

with st.form("search_form", border=False):
    query = st.text_input(
        "Query",
        type="search",
        key="query",
        placeholder="Ask something about the podcast…",
        label_visibility="collapsed",
        bind="query-params",
    )
    k = st.slider(
        "Number of results",
        key="k",
        min_value=1,
        max_value=50,
        value=10,
        bind="query-params",
    )
    publication_range = st.date_input(
        "Publication date range",
        key="publication_range",
        value=[],
        format="YYYY-MM-DD",
        bind="query-params",
    )
    published_after = publication_range[0] if len(publication_range) >= 1 else None
    published_before = publication_range[1] if len(publication_range) == 2 else None
    submitted = st.form_submit_button(
        "Search", type="primary", icon=":material/search:"
    )

query = query.strip()
params = (query, k, published_after, published_before)
results: list[Document] | None = st.session_state["results"]
last_params = st.session_state["last_params"]

should_search = bool(query) and (
    submitted
    or (st.session_state["searched"] and last_params != params)
    or st.query_params.get("submit") == "true"
)

if submitted and not query:
    st.warning("Please enter a query.")

results_slot = st.container()

if should_search:
    with results_slot.skeleton():
        try:
            results = cached_retrieve(query, k, published_after, published_before)
        except Exception as exc:  # noqa: BLE001
            results = None
            results_slot.error(
                "Retrieval failed. Check your OPENROUTER_API_KEY and vectorstore setup."
            )
            results_slot.exception(exc)
    st.session_state["last_params"] = params
    st.session_state["results"] = results
    st.session_state["searched"] = True

if not st.session_state["searched"]:
    with results_slot:
        st.caption("Enter a query and press *Search* to retrieve transcript chunks.")
    st.stop()

assert results is not None
if not results:
    with results_slot:
        st.info(
            "No chunks found for this query and date range.",
            icon=":material/search_off:",
        )
    st.stop()

with results_slot:
    st.subheader(f"{len(results)} chunks", icon=":material/article:")
    for rank, document in enumerate(results, start=1):
        metadata = ChunkMetadata.model_validate(document.metadata)
        with st.container(border=True):
            st.markdown(f"#### {rank}. {metadata.title}")
            st.caption(
                f"{metadata.publication_date.isoformat()} · "
                f"{format_timecode(metadata.start)} – {format_timecode(metadata.end)}"
            )
            st.markdown(document.page_content.replace("\n", "\n\n"))
