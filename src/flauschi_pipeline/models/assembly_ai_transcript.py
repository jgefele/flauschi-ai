import assemblyai as aai
from pydantic import Field


class AssemblyAiTranscript(aai.types.TranscriptResponse):
    sentences: list[aai.types.Sentence]
    text: None = Field(None, exclude=True)
    utterances: None = Field(None, exclude=True)
    words: None = Field(None, exclude=True)

    @staticmethod
    def from_transcript_and_sentences(
        transcript: aai.Transcript, sentences: list[aai.types.Sentence]
    ) -> "AssemblyAiTranscript":
        stripped_transcript_dict = transcript.json_response | dict(
            text=None, utterances=None, words=None
        )

        t = AssemblyAiTranscript(
            **stripped_transcript_dict,
            sentences=sentences,
        )

        return t
