import re
from collections.abc import Generator
from datetime import date, timedelta
from typing import Annotated

import click
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from pydantic import BaseModel, BeforeValidator, PlainSerializer

from flauschi_pipeline.chunker import Chunk, TurnBasedChunker
from flauschi_pipeline.constants import EPISODE_PATH
from flauschi_pipeline.models import Episode
from flauschi_pipeline.persistence import load_episode
from flauschi_pipeline.vectorstore import get_vectorstore


def parse_timedelta_seconds(v: float | timedelta) -> timedelta:
    if isinstance(v, timedelta):
        return v
    return timedelta(seconds=v)


def serialize_timedelta_seconds(td: timedelta) -> float:
    return td.total_seconds()


TimedeltaAsTotalSecondsInt = Annotated[
    timedelta,
    BeforeValidator(parse_timedelta_seconds),
    PlainSerializer(serialize_timedelta_seconds),
]


class ChunkMetadata(BaseModel):
    publication_date: date
    title: str
    start: TimedeltaAsTotalSecondsInt
    end: TimedeltaAsTotalSecondsInt


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


@click.command()
@click.option(
    "--pattern",
    default="2026.*",
    help="Regex pattern for episode json files to index (default: 2026.*)",
)
def main(pattern: str):
    vector_store = get_vectorstore()
    chunker = TurnBasedChunker.from_huggingface_tokenizer(
        model_name="Qwen/Qwen3-Embedding-8B",
        max_tokens_per_chunk=1000,
        overlap_tokens_per_chunk=250,
    )
    for e in load_episodes(pattern):
        _ids = index_episode(e, chunker, vector_store)


if __name__ == "__main__":
    main()
