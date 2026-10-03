import asyncio

from dotenv import load_dotenv
import streamlit as st
from langchain_core.output_parsers import StrOutputParser

from flauschi_ai.chain import build_rag_chain, build_runnable_config
from flauschi_ai.constants import DEFAULT_TOP_K
from flauschi_ai.telemetry import setup_telemetry

st.set_page_config(page_title="Flauschi AI", page_icon=":material/mic:")


@st.cache_resource
def init_app():
    load_dotenv()
    setup_telemetry()


init_app()


async def run(frage: str):
    docs_box = st.empty()
    antwort_box = st.empty()
    text = ""

    chain = build_rag_chain() | StrOutputParser()
    config = build_runnable_config(DEFAULT_TOP_K, None, None)

    async for ev in chain.astream_events(frage, version="v2", config=config):
        kind = ev["event"]

        if kind == "on_retriever_end":
            doc_titles = list(
                set(d.metadata.get("title") for d in ev["data"]["output"])
            )
            docs_box.markdown(
                "Durchsuchte Episoden: "
                + " ".join(f":orange-badge[{dt}]" for dt in doc_titles)
            )

        elif kind == "on_chat_model_stream":
            text += ev["data"]["chunk"].content
            antwort_box.markdown(text + "▌")

    antwort_box.markdown(text)


st.title("Flauschi AI")

with st.form("frage_form", border=False):
    frage = st.text_area(
        "Stelle mir alle Fragen über deinen Lieblingspodcast", height="content"
    )
    _, senden_box = st.columns([1, 0.2], vertical_alignment="bottom")
    senden = senden_box.form_submit_button(
        "Senden", icon=":material/send:", type="primary", use_container_width=True
    )

if frage and senden:
    asyncio.run(run(frage))