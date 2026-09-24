from dotenv import load_dotenv
from langchain_core.utils import secret_from_env
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, Modifier, SparseVectorParams, VectorParams, PayloadSchemaType

from flauschi_pipeline.constants import QDRANT_PATH
from flauschi_pipeline.models import ChunkMetadata

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CHUNK_METADATA_PUBLICATION_DATE = "publication_date"
VECTORSTORE_METADATA_PUBLICATION_DATE = f"metadata.{CHUNK_METADATA_PUBLICATION_DATE}"


def get_vectorstore() -> QdrantVectorStore:
    assert load_dotenv()

    embeddings = OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        #        model="qwen/qwen3-embedding-8b",
        base_url=OPENROUTER_BASE_URL,
        api_key=secret_from_env("OPENROUTER_API_KEY")(),
    )
    #    embeding_size = 4096
    embeding_size = 1536

    client = QdrantClient(path=str(QDRANT_PATH))
    collection_name = "default_embeddings"

    if collection_name not in (c.name for c in client.get_collections().collections):
        assert client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embeding_size, distance=Distance.COSINE),
            sparse_vectors_config={
                "langchain-sparse": SparseVectorParams(modifier=Modifier("idf"))
            },
        )

    assert CHUNK_METADATA_PUBLICATION_DATE in ChunkMetadata.model_fields
    client.create_payload_index(
        collection_name=collection_name,
        field_name=VECTORSTORE_METADATA_PUBLICATION_DATE,
        field_schema=PayloadSchemaType.DATETIME,
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
        retrieval_mode=RetrievalMode.HYBRID,
        sparse_embedding=FastEmbedSparse(),
    )

    return vector_store
