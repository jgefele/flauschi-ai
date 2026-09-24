
import sys
from datetime import date

import click
from langchain_core.documents.base import Document
from qdrant_client.models import Filter, FieldCondition, DatetimeRange

from flauschi_pipeline.models import ChunkMetadata
from flauschi_pipeline.utils import format_timecode, CLICK_DATE_PARAM
from flauschi_pipeline.vectorstore import get_vectorstore, VECTORSTORE_METADATA_PUBLICATION_DATE

DocumentsWithScores = list[tuple[Document, float]]

def retrieve(query: str, k: int, published_after: date | None, published_before: date | None) -> DocumentsWithScores:
    vector_store = get_vectorstore()
    date_filter = Filter(
        must=[
            FieldCondition(
                key=VECTORSTORE_METADATA_PUBLICATION_DATE,  # LangChain nests payload under 'metadata'
                range=DatetimeRange(
                    gte=published_after,
                    lte=published_before,
                ),
            )
        ]
    )
    return vector_store.similarity_search_with_relevance_scores(query, k, filter=date_filter)


@click.command()
@click.argument("query", required=True)
@click.option("--k", default=10)
@click.option(
    "--published-after",
    type=CLICK_DATE_PARAM,
    default=None,
)
@click.option(
    "--published-before",
    type=CLICK_DATE_PARAM,
    default=None,
)
def main(query: str, k: int, published_after: date | None, published_before: date | None):
    """Retrieve documents matching QUERY.

    QUERY is a search string. If QUERY is "-", the query is read from stdin.
    """
    if query == "-":
        query = "\n".join(sys.stdin.readlines())

    for document, score in retrieve(query, k, published_after, published_before):
        metadata = ChunkMetadata.model_validate(document.metadata)
        print(f"# {metadata.title} ({metadata.publication_date})")
        print(f"*{format_timecode(metadata.start)}-{format_timecode(metadata.end)}*")
        print(f"*Score: {score}*")
        print()
        print(document.page_content.replace("\n", "\n\n"))
        print()
        print()


if __name__ == "__main__":
    main()
