from flauschi_ai import constants
from flauschi_ai.vectorstore import FlauschiVectorStore

import click


@click.command("ingest")
@click.option(
    "--pattern",
    default="2026.*",
    help="Regex pattern for episode json files to index (default: 2026.*)",
)
def ingest_command(pattern: str):
    """Index episodes into the vector store."""
    FlauschiVectorStore.default().ingest(pattern)



@click.command("ingest-test")
@click.option(
    "--pattern",
    default="2026-09.*",
)
@click.option(
    "--max_tokens_per_chunk",
    default=constants.DEFAULT_MAX_TOKENS_PER_CHUNK,
)
@click.option(
    "--overlap_tokens_per_chunk",
    default=constants.DEFAULT_OVERLAP_TOKENS_PER_CHUNK,
)
def ingest_test_command(pattern: str, max_tokens_per_chunk: int, overlap_tokens_per_chunk: int):
    vs = FlauschiVectorStore(
        collection_name="test",
        embedding_model="qwen/qwen3-embedding-8b",
        embedding_size=4096,
        tokenization_model=constants.DEFAULT_TOKENIZATION_MODEL,
        max_tokens_per_chunk=max_tokens_per_chunk,
        overlap_tokens_per_chunk=overlap_tokens_per_chunk,

    )
    vs.drop_collection_if_exists()
    vs.ingest(pattern)