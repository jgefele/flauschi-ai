from datetime import date, timedelta
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, PlainSerializer


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
