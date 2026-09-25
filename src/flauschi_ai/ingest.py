import re
from collections.abc import Generator

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from flauschi_ai.chunker import Chunk, TurnBasedChunker
from flauschi_ai.constants import EPISODE_PATH
from flauschi_ai.models import Episode, ChunkMetadata
from flauschi_ai.persistence import load_episode
from flauschi_ai.vectorstore import get_vectorstore


def _to_document(episode: Episode, chunk: Chunk) -> Document:
    metadata = ChunkMetadata(
        publication_date=episode.publication_date,
        title=episode.title,
        start=chunk.start,
        end=chunk.end,
    )
    return Document(page_content=chunk.text, metadata=metadata.model_dump())


def index_episode(
    episode: Episode, chunker: TurnBasedChunker, vector_store: VectorStore
) -> list[str]:
    chunks = chunker.transcript_to_chunks(episode.transcript)
    print(
        f"Adding {len(chunks)} chunks from {episode.slug} to the vector store...",
        end="",
    )
    documents = [_to_document(episode, chunk) for chunk in chunks]
    ids = vector_store.add_documents(documents)
    print("done")
    return ids


def load_episodes(pattern: str | None) -> Generator[Episode]:
    for f in EPISODE_PATH.glob("*.json"):
        if f.is_file() and (pattern is None or re.search(pattern, f.name)):
            yield load_episode(f)

def ingest(pattern: str):
    """Index episodes into the vector store."""
    vector_store = get_vectorstore()
    chunker = TurnBasedChunker.from_huggingface_tokenizer(
        model_name="Qwen/Qwen3-Embedding-8B",
        max_tokens_per_chunk=1000,
        overlap_tokens_per_chunk=250,
    )
    for e in load_episodes(pattern):
        index_episode(e, chunker, vector_store)