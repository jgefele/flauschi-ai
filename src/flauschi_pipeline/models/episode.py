from datetime import timedelta

from pydantic import BaseModel, Field

from flauschi_pipeline.models.episode_metadata import EpisodeMetadata


class EpisodeSentence(BaseModel):
    start: timedelta
    end: timedelta
    text: str


class EpisodeSpeakerTurn(BaseModel):
    speaker_id: int
    sentences: list[EpisodeSentence]

    @property
    def start(self) -> timedelta:
        return self.sentences[0].start

    @property
    def end(self) -> timedelta:
        return self.sentences[-1].end

    @property
    def text(self) -> str:
        return " ".join(s.text for s in self.sentences)


class EpisodeTranscript(BaseModel):
    speakers: dict[int, str]
    speaker_turns: list[EpisodeSpeakerTurn] = Field(validation_alias="speaker_blocks")


class Episode(EpisodeMetadata):
    transcript: EpisodeTranscript

    audio_archive_url: str

    duration_with_ads: timedelta
