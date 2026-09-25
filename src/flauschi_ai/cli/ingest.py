from flauschi_ai.ingest import ingest

import click


@click.command("ingest")
@click.option(
    "--pattern",
    default="2026.*",
    help="Regex pattern for episode json files to index (default: 2026.*)",
)
def ingest_command(pattern: str):
    """Index episodes into the vector store."""
    ingest(pattern)