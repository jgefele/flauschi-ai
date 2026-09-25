from datetime import date

import click

from flauschi_ai.chain import build_formatted_retriever_chain, build_runnable_config
from flauschi_ai.cli.params import CLICK_DATE_PARAM
from flauschi_ai.cli.utils import read_query
from flauschi_ai.constants import DEFAULT_TOP_K


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
def retrieve_command(
    query: str, top_k: int, published_after: date | None, published_before: date | None
):
    """Retrieve documents matching QUERY.

    QUERY is a search string. If QUERY is "-", the query is read from stdin.
    """
    query = read_query(query)
    chain = build_formatted_retriever_chain()
    config = build_runnable_config(top_k, published_after, published_before)
    print(chain.invoke(query, config))
