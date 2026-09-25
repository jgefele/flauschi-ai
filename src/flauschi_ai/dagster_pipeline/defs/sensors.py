import dagster as dg

from flauschi_ai.constants import (
    DEFAULT_FEED_URL,
    RSS_FEED_CHECK_INTERVAL_SECONDS,
)
from .assets_episode_metadata import episode_metadata
from .common import episode_partition
from flauschi_ai.feed import parse_feed
from flauschi_ai.models import EpisodeMetadata


@dg.sensor(
    minimum_interval_seconds=RSS_FEED_CHECK_INTERVAL_SECONDS,
    default_status=dg.DefaultSensorStatus.RUNNING,
    asset_selection=dg.AssetSelection.assets(episode_metadata),
)
def rss_feed_sensor(context: dg.SensorEvaluationContext):
    last_modified = context.cursor
    context.log.info("querying feed with cursor Last-Modified: %s", last_modified)

    all_episodes, new_last_modified = parse_feed(DEFAULT_FEED_URL, last_modified)
    if not all_episodes and last_modified == new_last_modified:
        return dg.SkipReason(f"Not modified since: {last_modified}")
    context.log.info("total number of episodes: %s", len(all_episodes))

    backfill_episodes = all_episodes[:10]

    def _run_key(e: EpisodeMetadata) -> dg.RunRequest:
        return dg.RunRequest(
            partition_key=e.slug,
            run_key=str(hash(tuple(sorted(e.model_dump().items())))),
        )

    return dg.SensorResult(
        run_requests=[_run_key(e) for e in backfill_episodes],
        dynamic_partitions_requests=[
            episode_partition.build_add_request([e.slug for e in all_episodes])
        ],
        cursor=new_last_modified,
    )
