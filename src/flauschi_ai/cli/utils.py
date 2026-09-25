import sys


def read_query(query: str) -> str:
    if query == "-":
        return "\n".join(sys.stdin.readlines())
    return query