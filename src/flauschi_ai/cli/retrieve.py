import sys
from datetime import date

import click

from flauschi_ai.cli.params import CLICK_DATE_PARAM
from flauschi_ai.cli.utils import read_query
from flauschi_ai.constants import DEFAULT_TOP_K
from flauschi_ai.models import ChunkMetadata
from flauschi_ai.vectorstore import FlauschiVectorStore
from flauschi_ai.utils import format_timecode


@click.command(name="retrieve")
@click.argument("query", required=True)
@click.option("--top_k", default=DEFAULT_TOP_K)
@click.option(
    "--published-after",
    type=CLICK_DATE_PARAM,
    default=None,
)
@click.option(
    "--published-before",
    type=CLICK_DATE_PARAM,
    default=None,
)
def retrieve_command(query: str, top_k: int, published_after: date | None, published_before: date | None):
    """Retrieve documents matching QUERY.

    QUERY is a search string. If QUERY is "-", the query is read from stdin.
    """
    query = read_query(query)
    store = FlauschiVectorStore.default()
    for document, score in store.retrieve(query, top_k, published_after, published_before):
        metadata = ChunkMetadata.model_validate(document.metadata)
        print(f"# {metadata.title} ({metadata.publication_date})")
        print(f"*{format_timecode(metadata.start)}-{format_timecode(metadata.end)}*")
        print(f"*Score: {score}*")
        print()
        print(document.page_content.replace("\n", "\n\n"))
        print()
        print()