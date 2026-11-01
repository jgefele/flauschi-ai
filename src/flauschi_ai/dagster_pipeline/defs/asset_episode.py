import dagster as dg

from flauschi_ai.episode import export_episode
from flauschi_ai.models import (
    AssemblyAiTranscript,
    AudioArchiveMetadata,
    Episode,
    EpisodeMetadata,
    SpotifyEpisodeMetadata,
)

from .common import episode_partition, on_missing_with_unlimited_backfill


@dg.asset(
    partitions_def=episode_partition,
    automation_condition=on_missing_with_unlimited_backfill,
)
def episode(
    episode_metadata: EpisodeMetadata,
    audio_archive: AudioArchiveMetadata,
    assembly_ai_transcript: AssemblyAiTranscript,
    spotify_episode_metadata: SpotifyEpisodeMetadata,
) -> Episode:
    return export_episode(
        episode_metadata, audio_archive, assembly_ai_transcript, spotify_episode_metadata
    )
