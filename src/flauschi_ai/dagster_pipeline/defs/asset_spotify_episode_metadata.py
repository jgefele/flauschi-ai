import dagster as dg

from flauschi_ai.dagster_pipeline.defs.common import episode_partition
from flauschi_ai.models import SpotifyEpisodeMetadata, SpotifyEpisodeMetadataCollection
from flauschi_ai.spotify import fetch_episodes

from .common import episode_partition, on_missing_with_unlimited_backfill


@dg.asset()
def spotify_episode_metadata_dict() -> SpotifyEpisodeMetadataCollection:
    client_id = dg.EnvVar("SPOTIFY_CLIENT_ID").get_value()
    client_key = dg.EnvVar("SPOTIFY_CLIENT_KEY").get_value()

    assert client_id is not None and client_key is not None, (
        "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_KEY in .env"
    )

    return SpotifyEpisodeMetadataCollection(
        fetch_episodes(client_id, client_key)
    )


@dg.asset(
    partitions_def=episode_partition,
    automation_condition=on_missing_with_unlimited_backfill,
)
def spotify_episode_metadata(
    context: dg.AssetExecutionContext,
    spotify_episode_metadata_dict: SpotifyEpisodeMetadataCollection,
) -> SpotifyEpisodeMetadata:
    partition_key = context.partition_key

    if (episode := spotify_episode_metadata_dict.root.get(partition_key)) is not None:
        return episode
    else:
        raise dg.RetryRequested(max_retries=5, seconds_to_wait=600)
