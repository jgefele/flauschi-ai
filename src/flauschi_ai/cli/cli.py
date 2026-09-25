import click

from flauschi_ai.cli.rag import rag_command as ask
from flauschi_ai.cli.ingest import ingest_command as ingest
from flauschi_ai.cli.retrieve import retrieve_command


@click.group()
def cli():
    """flauschi-ai command line interface."""


cli.add_command(ingest)
cli.add_command(retrieve_command)
cli.add_command(ask)