import dagster as dg

from flauschi_pipeline.defs.common import episode_partition
from flauschi_pipeline.episode import export_episode
from flauschi_pipeline.models import (
    AssemblyAiTranscript,
    AudioArchiveMetadata,
    Episode,
    EpisodeMetadata,
)


@dg.asset(
    partitions_def=episode_partition,
    automation_condition=dg.AutomationCondition.on_missing().replace(
        "handled",
        dg.AutomationCondition.newly_requested()
        | dg.AutomationCondition.newly_updated(),
    ),
)
def episode(
    episode_metadata: EpisodeMetadata,
    audio_archive: AudioArchiveMetadata,
    assembly_ai_transcript: AssemblyAiTranscript,
) -> Episode:
    return export_episode(episode_metadata, audio_archive, assembly_ai_transcript)
