import click

from flauschi_ai.cli.rag import rag_command
from flauschi_ai.cli.ingest import ingest_command, ingest_test_command
from flauschi_ai.cli.retrieve import retrieve_command


@click.group()
def cli():
    """flauschi-ai command line interface."""


cli.add_command(ingest_command)
cli.add_command(ingest_test_command)
cli.add_command(retrieve_command)
cli.add_command(rag_command)