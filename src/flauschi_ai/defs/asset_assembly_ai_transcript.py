import assemblyai
import dagster as dg
from assemblyai.prerecorded.v2.transcript import Transcript

from flauschi_ai.defs.common import episode_partition
from flauschi_ai.defs.resources import AssemblyAIResource
from flauschi_ai.models import (
    AssemblyAiTranscript,
    AudioArchiveMetadata,
)


@dg.asset(
    pool="assembly_ai_api",
    partitions_def=episode_partition,
    automation_condition=dg.AutomationCondition.on_missing().replace(
        "handled",
        dg.AutomationCondition.newly_requested()
        | dg.AutomationCondition.newly_updated(),
    ),
)
def assembly_ai_transcript(
    context: dg.AssetExecutionContext,
    audio_archive: AudioArchiveMetadata,
    aai: AssemblyAIResource,
):
    transcriber = aai.get_client()
    config = assemblyai.TranscriptionConfig(
        language_code=assemblyai.LanguageCode.de,
        temperature=0,
        speech_models=["universal-3-5-pro"],
        speaker_labels=True,
        speech_understanding=assemblyai.SpeechUnderstandingRequest(
            request=assemblyai.SpeechUnderstandingFeatureRequests(
                speaker_identification=assemblyai.SpeakerIdentificationRequest(
                    speaker_type=assemblyai.SpeakerType.name,
                    known_values=["Jan", "Olli", "Werbung", "Gast"],
                )
            )
        ),
    )
    url = audio_archive.archive_url
    context.log.info(f"transcribing {url}...")

    transcript: Transcript = transcriber.transcribe(url, config=config)
    sentences = transcript.get_sentences()

    return AssemblyAiTranscript.from_transcript_and_sentences(transcript, sentences)
