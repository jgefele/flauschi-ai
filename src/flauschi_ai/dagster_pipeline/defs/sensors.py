import hashlib
import json

import dagster as dg

from flauschi_ai.constants import (
    DEFAULT_FEED_URL,
    RSS_FEED_CHECK_INTERVAL_SECONDS,
)
from flauschi_ai.feed import parse_feed
from flauschi_ai.models import EpisodeMetadata
from flauschi_ai.spotify import fetch_episodes

from .asset_episode_metadata import episode_metadata
from .asset_spotify_episode_metadata import spotify_episode_metadata_dict
from .common import episode_partition


@dg.sensor(
    minimum_interval_seconds=RSS_FEED_CHECK_INTERVAL_SECONDS,
    default_status=dg.DefaultSensorStatus.RUNNING,
    asset_selection=dg.AssetSelection.assets(episode_metadata),
)
def rss_feed_sensor(context: dg.SensorEvaluationContext):
    last_modified = context.cursor
    context.log.info("querying feed with cursor Last-Modified: %s", last_modified)

    all_episodes, new_last_modified = parse_feed(DEFAULT_FEED_URL, last_modified)
    if not all_episodes and (
        last_modified == new_last_modified or new_last_modified is None
    ):
        return dg.SkipReason(f"Not modified since: {last_modified}")
    context.log.info("total number of episodes: %s", len(all_episodes))

    backfill_episodes = all_episodes[:10]

    def _run_request(e: EpisodeMetadata) -> dg.RunRequest:
        payload = json.dumps(e.model_dump(mode="json"), sort_keys=True)
        return dg.RunRequest(
            partition_key=e.slug,
            run_key=hashlib.sha256(payload.encode()).hexdigest(),
        )

    return dg.SensorResult(
        run_requests=[_run_request(e) for e in backfill_episodes],
        dynamic_partitions_requests=[
            episode_partition.build_add_request([e.slug for e in all_episodes])
        ],
        cursor=new_last_modified,
    )


@dg.sensor(
    minimum_interval_seconds=RSS_FEED_CHECK_INTERVAL_SECONDS,
    default_status=dg.DefaultSensorStatus.RUNNING,
    asset_selection=dg.AssetSelection.assets(spotify_episode_metadata_dict),
)
def spotify_feed_sensor(context: dg.SensorEvaluationContext):
    last_publication_date = context.cursor
    context.log.info(
        "querying episode list with last_publication_date: %s", last_publication_date
    )

    client_id = dg.EnvVar("SPOTIFY_CLIENT_ID").get_value()
    client_key = dg.EnvVar("SPOTIFY_CLIENT_KEY").get_value()

    assert client_id is not None and client_key is not None, (
        "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_KEY in .env"
    )

    try:
        latest_episode = fetch_episodes(client_id, client_key, 1).popitem()[1]
    except KeyError:
        return dg.SkipReason("Empty list")

    latest_episode_publication_date = latest_episode.publication_date.isoformat()

    if latest_episode_publication_date == last_publication_date:
        return dg.SkipReason(f"Not modified since: {last_publication_date}")

    context.log.info("New episode from : %s", latest_episode_publication_date)
    return dg.SensorResult(
        run_requests=[dg.RunRequest()],
        cursor=latest_episode_publication_date,
    )
