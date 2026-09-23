from dotenv import load_dotenv
from langchain_core.utils import secret_from_env
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, Modifier, SparseVectorParams, VectorParams

from flauschi_pipeline.constants import DATA_PATH, QDRANT_PATH

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


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

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
        retrieval_mode=RetrievalMode.HYBRID,
        sparse_embedding=FastEmbedSparse(),
    )

    return vector_store
