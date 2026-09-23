from langchain_core.vectorstores.base import VectorStoreRetriever


import sys

import click
from langchain_core.documents.base import Document

from flauschi_pipeline.ingest import ChunkMetadata
from flauschi_pipeline.utils import format_timecode
from flauschi_pipeline.vectorstore import get_vectorstore

DocumentsWithScores = list[tuple[Document, float]]


def retrieve(query: str, k: int = 4) -> DocumentsWithScores:
    vector_store = get_vectorstore()
    return vector_store.similarity_search_with_relevance_scores(query, k)


@click.command()
@click.argument("query", required=True)
def main(query: str):
    """Retrieve documents matching QUERY.

    QUERY is a search string. If QUERY is "-", the query is read from stdin.
    """
    if query == "-":
        query = "\n".join(sys.stdin.readlines())

    for document, score in retrieve(query):
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
