import dagster as dg
from pydantic import BaseModel

from .common import episode_partition
from flauschi_ai.models import Episode
from ...vectorstore import FlauschiVectorStore


class IdList(BaseModel):
    ids: list[str]


@dg.asset(
    partitions_def=episode_partition,
    automation_condition=dg.AutomationCondition.on_missing().replace(
        "handled",
        dg.AutomationCondition.newly_requested()
        | dg.AutomationCondition.newly_updated(),
    ),
)
def vector_database(
    episode: Episode,
) -> IdList:
    ids = FlauschiVectorStore.default().add_episode(episode)
    return IdList(ids=ids)
