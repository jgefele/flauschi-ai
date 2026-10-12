import dagster as dg
from pydantic import BaseModel

from flauschi_ai.models import Episode

from ...vectorstore import FlauschiVectorStore
from .common import episode_partition, on_missing_with_unlimited_backfill


class IdList(BaseModel):
    ids: list[str]


@dg.asset(
    partitions_def=episode_partition,
    automation_condition=on_missing_with_unlimited_backfill,
)
def vector_database(
    episode: Episode,
) -> IdList:
    ids = FlauschiVectorStore.default().add_episode(episode)
    return IdList(ids=ids)
