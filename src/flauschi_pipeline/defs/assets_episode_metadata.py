import dagster as dg

from flauschi_pipeline.constants import DEFAULT_FEED_URL
from flauschi_pipeline.defs.common import episode_partition
from flauschi_pipeline.feed import parse_feed
from flauschi_pipeline.models.episode_metadata import EpisodeMetadata


@dg.asset(
    partitions_def=episode_partition,
)
def episode_metadata(
    context: dg.AssetExecutionContext,
) -> EpisodeMetadata:
    episode_slug_to_find = context.partition_key
    episodes, _ = parse_feed(DEFAULT_FEED_URL, None)
    try:
        return next(e for e in episodes if e.slug == episode_slug_to_find)
    except StopIteration as e:
        raise ValueError(f"no episode with slug {episode_slug_to_find} found!") from e
