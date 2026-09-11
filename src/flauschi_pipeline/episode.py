from datetime import timedelta

from flauschi_pipeline.models import (
    AssemblyAiTranscript,
    AudioArchiveMetadata,
    Episode,
    EpisodeMetadata,
    EpisodeSentence,
    EpisodeSpeakerBlock,
    EpisodeTranscript,
)


def export_episode(
    metadata: EpisodeMetadata,
    audio_archive: AudioArchiveMetadata,
    transcript: AssemblyAiTranscript,
) -> Episode:
    try:
        speaker_mapping: dict[str, str] = (
            transcript.speech_understanding.response.speaker_identification.mapping  # pyright: ignore[reportOptionalMemberAccess]
            or {}
        )
    except TypeError:  # somewhere a None in the attribute chain
        speaker_mapping: dict[str, str] = {}

    speaker_ids: dict[str, int] = {}
    speakers: dict[int, str] = {}

    def speaker_id_for(label: str) -> int:
        if label not in speaker_ids:
            index = len(speaker_ids)
            speaker_ids[label] = index
            speakers[index] = speaker_mapping.get(label, label)
        return speaker_ids[label]

    speaker_blocks: list[EpisodeSpeakerBlock] = []
    current: EpisodeSpeakerBlock | None = None

    for sentence in transcript.sentences:
        sentence_model = EpisodeSentence(
            start=timedelta(milliseconds=sentence.start),
            end=timedelta(milliseconds=sentence.end),
            text=sentence.text,
        )
        label = sentence.speaker or "?"
        sid = speaker_id_for(label)

        if current is None or current.speaker_id != sid:
            current = EpisodeSpeakerBlock(
                speaker_id=sid,
                sentences=[sentence_model],
            )
            speaker_blocks.append(current)
        else:
            current.sentences.append(sentence_model)

    return Episode(
        id=metadata.id,
        publication_date=metadata.publication_date,
        title=metadata.title,
        description=metadata.description,
        audio_url=metadata.audio_url,
        duration=metadata.duration,
        duration_with_ads=timedelta(seconds=transcript.audio_duration or 0),
        audio_archive_url=audio_archive.archive_url,
        transcript=EpisodeTranscript(
            speakers=speakers,
            speaker_blocks=speaker_blocks,
        ),
    )
