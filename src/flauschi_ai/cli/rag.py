import json
from collections.abc import Iterator
from datetime import date
from typing import Literal, cast

import click
from langchain_core.messages import AIMessageChunk

from flauschi_ai.chain import build_rag_chain, build_runnable_config
from flauschi_ai.cli.params import CLICK_DATE_PARAM
from flauschi_ai.cli.utils import read_query
from flauschi_ai.constants import DEFAULT_TOP_K


@click.command("rag")
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
def rag_command(
    query: str, top_k: int, published_after: date | None, published_before: date | None
):
    """Answer questions for QUERY.

    QUERY is a search string. If QUERY is "-", the query is read from stdin.
    """
    query = read_query(query)

    chain = build_rag_chain()
    config = build_runnable_config(top_k, published_after, published_before)

    state: Literal["INIT", "REASONING", "ANSWER"] = "INIT"
    full_response: AIMessageChunk | None = None
    for chunk in cast(Iterator[AIMessageChunk], chain.stream(query, config)):
        full_response = full_response + chunk if full_response else chunk

        if reasoning := cast(str, chunk.additional_kwargs.get("reasoning_content")):
            assert state in ("INIT", "REASONING")
            if state == "INIT":
                print("## Reasoning\n")
                state = "REASONING"
            print(reasoning, end="", flush=True)

        if chunk.content:
            if state in ("INIT", "REASONING"):
                print("\n\n## Answer\n")
                state = "ANSWER"

            print(chunk.content, end="", flush=True)

    print("\n")

    if full_response:
        print("## Meta")
        print("```json")
        print(json.dumps(full_response.response_metadata, indent=2))
        print("```")