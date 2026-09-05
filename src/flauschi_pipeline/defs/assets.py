from datetime import date, timedelta
import json
import random

import dagster as dg

from flauschi_pipeline.constants import DEFAULT_FEED_URL
from flauschi_pipeline.feed import Episode, parse_feed

episode_partition = dg.DynamicPartitionsDefinition(name="episode")


class FeedEntryRunConfig(dg.Config):
    id: str
    publication_date: str
    title: str
    description: str
    audio_url: str
    duration: str

    @staticmethod
    def from_episode(e: Episode) -> "FeedEntryRunConfig":
        return FeedEntryRunConfig.model_validate_json(e.model_dump_json())

    def to_episode(self) -> Episode:
        return Episode.model_validate_strings(self.model_dump())

    def run_key(self):
        return str(hash(tuple(sorted(self.model_dump().items()))))


# start_podcast_audio
podcast_feed_entry_asset_name = "podcast_feed_entry"


@dg.asset(
    name=podcast_feed_entry_asset_name,
    partitions_def=episode_partition,
    compute_kind="python",
)
def ingest_episode(
    context: dg.AssetExecutionContext,
    config: FeedEntryRunConfig,
):
    return config.to_episode()


_job = dg.define_asset_job(
    name="ingest_episode_job",
    selection=dg.AssetSelection.assets(ingest_episode),
)


@dg.sensor(
    minimum_interval_seconds=60,
    default_status=dg.DefaultSensorStatus.RUNNING,
    job=_job,
)
def rss_feed_sensor(context: dg.SensorEvaluationContext):
    last_modified = context.cursor
    context.log.info("querying feed with cursor Last-Modified: %s", last_modified)

    episodes, new_last_modified = parse_feed(DEFAULT_FEED_URL, last_modified)
    if not episodes and last_modified == new_last_modified:
        return dg.SkipReason(f"Not modified since: {last_modified}")

    episodes = episodes[:10]
    context.log.info("total number of episodes: %s", len(episodes))

    return dg.SensorResult(
        run_requests=[
            dg.RunRequest(
                partition_key=e.slug,
                run_key=rc.run_key(),
                run_config=dg.RunConfig(
                    ops={ingest_episode.key.to_python_identifier(): rc}
                ),
            )
            for e in episodes
            if (rc := FeedEntryRunConfig.from_episode(e))
        ],
        dynamic_partitions_requests=[
            episode_partition.build_add_request([e.slug for e in episodes])
        ],
        cursor=new_last_modified,
    )
