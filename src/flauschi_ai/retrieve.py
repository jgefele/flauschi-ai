from datetime import date

from langchain_core.documents.base import Document
from qdrant_client.models import Filter, FieldCondition, DatetimeRange

from flauschi_ai.vectorstore import get_vectorstore, VECTORSTORE_METADATA_PUBLICATION_DATE

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