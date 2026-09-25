import logging
from datetime import date
from functools import cached_property
from typing import cast

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.utils import secret_from_env
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.models import (
    DatetimeRange,
    Distance,
    FieldCondition,
    Filter,
    Modifier,
    PayloadSchemaType,
    SparseVectorParams,
    VectorParams,
)

from flauschi_ai.chunker import Chunk, TurnBasedChunker
from flauschi_ai.constants import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_SIZE,
    DEFAULT_MAX_TOKENS_PER_CHUNK,
    DEFAULT_OVERLAP_TOKENS_PER_CHUNK,
    DEFAULT_TOKENIZATION_MODEL,
    OPENROUTER_BASE_URL,
    QDRANT_PATH,
)
from flauschi_ai.models import ChunkMetadata, Episode
from flauschi_ai.persistence import load_episodes

CHUNK_METADATA_PUBLICATION_DATE = "publication_date"
VECTORSTORE_METADATA_PUBLICATION_DATE = f"metadata.{CHUNK_METADATA_PUBLICATION_DATE}"

DocumentsWithScores = list[tuple[Document, float]]


class FlauschiVectorStore:
    def __init__(
        self,
        collection_name: str,
        embedding_model: str,
        embedding_size: int,
        tokenization_model: str,
        max_tokens_per_chunk: int,
        overlap_tokens_per_chunk: int,
    ):
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_size = embedding_size
        self.tokenization_model = tokenization_model
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.overlap_tokens_per_chunk = overlap_tokens_per_chunk

    @classmethod
    def default(cls) -> "FlauschiVectorStore":
        return cls(
            collection_name=DEFAULT_COLLECTION_NAME,
            embedding_model=DEFAULT_EMBEDDING_MODEL,
            embedding_size=DEFAULT_EMBEDDING_SIZE,
            tokenization_model=DEFAULT_TOKENIZATION_MODEL,
            max_tokens_per_chunk=DEFAULT_MAX_TOKENS_PER_CHUNK,
            overlap_tokens_per_chunk=DEFAULT_OVERLAP_TOKENS_PER_CHUNK,
        )

    def _collection_metadata(self) -> dict:
        return {
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model,
            "embedding_size": self.embedding_size,
            "tokenization_model": self.tokenization_model,
            "max_tokens_per_chunk": self.max_tokens_per_chunk,
            "overlap_tokens_per_chunk": self.overlap_tokens_per_chunk,
        }

    def drop_collection_if_exists(self) -> bool:
        client = QdrantClient(path=str(QDRANT_PATH))
        if client.collection_exists(self.collection_name):
            client.delete_collection(collection_name=self.collection_name)
            return True
        return False

    def _load(self) -> QdrantVectorStore:
        assert load_dotenv()

        client = QdrantClient(path=str(QDRANT_PATH))
        expected_metadata = self._collection_metadata()

        if not client.collection_exists(self.collection_name):
            assert client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_size, distance=Distance.COSINE
                ),
                sparse_vectors_config={
                    "langchain-sparse": SparseVectorParams(modifier=Modifier("idf"))
                },
                metadata=expected_metadata,
            )
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name=VECTORSTORE_METADATA_PUBLICATION_DATE,
                field_schema=PayloadSchemaType.DATETIME,
            )
        else:
            stored = client.get_collection(self.collection_name).config.metadata
            stored = dict(stored) if stored else {}
            if not stored:
                logging.warning(
                    "Collection %s was created without metadata; cannot validate "
                    "configuration against it.",
                    self.collection_name,
                )
            else:
                differing = sorted(
                    key
                    for key in set(stored) | set(expected_metadata)
                    if stored.get(key) != expected_metadata.get(key)
                )
                if differing:
                    details = ", ".join(
                        f"{key}: stored={stored.get(key)!r} expected={expected_metadata.get(key)!r}"
                        for key in differing
                    )
                    raise ValueError(
                        f"Collection {self.collection_name} was created with a "
                        f"different configuration: {details}"
                    )

        embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            base_url=OPENROUTER_BASE_URL,
            api_key=secret_from_env("OPENROUTER_API_KEY")(),
            # length check doesn't work with non-OpenAI embeddings via OpenRouter as it uses wrong tokenizer
            check_embedding_ctx_length=True if self.embedding_model.startswith("openai/") else False,
        )
        return QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            sparse_embedding=FastEmbedSparse(),
        )

    @cached_property
    def _qdrant_vector_store(self) -> QdrantVectorStore:
        return self._load()

    @property
    def vector_store(self) -> VectorStore:
        return cast(VectorStore, self._qdrant_vector_store)

    @cached_property
    def _chunker(self) -> TurnBasedChunker:
        return TurnBasedChunker.from_huggingface_tokenizer(
            model_name=self.tokenization_model,
            max_tokens_per_chunk=self.max_tokens_per_chunk,
            overlap_tokens_per_chunk=self.overlap_tokens_per_chunk,
        )

    @staticmethod
    def _to_document(episode: Episode, chunk: Chunk) -> Document:
        metadata = ChunkMetadata(
            publication_date=episode.publication_date,
            title=episode.title,
            start=chunk.start,
            end=chunk.end,
        )
        return Document(page_content=chunk.text, metadata=metadata.model_dump())

    def _ingest_episode(self, episode: Episode) -> list[str]:
        chunks = self._chunker.transcript_to_chunks(episode.transcript)
        print(
            f"Adding {len(chunks)} chunks from {episode.slug} to the vector store...",
            end="",
        )
        documents = [self._to_document(episode, chunk) for chunk in chunks]
        ids = self.vector_store.add_documents(documents)
        print("done")
        return ids

    def ingest(self, pattern: str):
        """Index episodes into the vector store."""
        for episode in load_episodes(pattern):
            self._ingest_episode(episode)

    def retrieve(
        self,
        query: str,
        k: int,
        published_after: date | None,
        published_before: date | None,
    ) -> DocumentsWithScores:
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
        return self.vector_store.similarity_search_with_relevance_scores(
            query, k, filter=date_filter
        )
