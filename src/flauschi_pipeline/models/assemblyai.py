from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssemblyAiWord(BaseModel):
    confidence: float
    end: int
    speaker: str = Field(
        description="short labels such as 'A' or 'B' mapped to real names by AssemblyAiSpeakerIdentificationResponse.mapping"
    )
    start: int
    text: str


class AssemblyAiSentence(BaseModel):
    confidence: float
    end: int
    speaker: str = Field(
        description="short labels such as 'A' or 'B' mapped to real names by AssemblyAiSpeakerIdentificationResponse.mapping"
    )
    start: int
    text: str
    words: list[AssemblyAiWord]


class AssemblyAiParagraph(BaseModel):
    confidence: float
    end: int
    start: int
    text: str
    words: list[AssemblyAiWord]


class AssemblyAiUtterance(BaseModel):
    confidence: float
    end: int
    speaker: str = Field(
        description="short labels such as 'A' or 'B' mapped to real names by AssemblyAiSpeakerIdentificationResponse.mapping"
    )
    start: int
    text: str
    words: list[AssemblyAiWord]


class AssemblyAiSpeakerIdentificationRequest(BaseModel):
    known_values: list[str]
    speaker_type: str


class AssemblyAiSpeakerIdentificationResponse(BaseModel):
    mapping: dict[str, str]
    status: str


class AssemblyAiSpeechUnderstandingRequest(BaseModel):
    speaker_identification: AssemblyAiSpeakerIdentificationRequest


class AssemblyAiSpeechUnderstandingResponse(BaseModel):
    speaker_identification: AssemblyAiSpeakerIdentificationResponse


class AssemblyAiSpeechUnderstanding(BaseModel):
    request: AssemblyAiSpeechUnderstandingRequest
    response: AssemblyAiSpeechUnderstandingResponse


class AssemblyAiStatusSummaryResult(BaseModel):
    results: list[dict[str, Any]]
    status: str
    summary: dict[str, Any]


class AssemblyAiTranscript(BaseModel):
    model_config = ConfigDict(extra="allow")

    acoustic_model: str
    audio_duration: int
    audio_end_at: int | None
    audio_start_from: int | None
    audio_url: str
    auto_chapters: bool
    auto_highlights: bool
    auto_highlights_result: dict[str, Any] | None
    boost_param: str | None
    chapters: list[dict[str, Any]] | None
    confidence: float
    content_safety: bool
    content_safety_labels: AssemblyAiStatusSummaryResult
    custom_spelling: list[dict[str, Any]] | None
    custom_topics: bool
    custom_topics_results: list[dict[str, Any]] | None
    disfluencies: bool
    dual_channel: bool
    entities: list[dict[str, Any]] | None
    entity_detection: bool
    filter_profanity: bool
    format_text: bool
    iab_categories: bool
    iab_categories_result: AssemblyAiStatusSummaryResult
    id: str
    is_deleted: bool | None
    keyterms_prompt: list[str]
    language_code: str
    language_confidence: float | None
    language_confidence_threshold: float | None
    language_detection: bool
    language_detection_options: dict[str, Any] | None
    language_detection_results: dict[str, Any] | None
    language_model: str
    multichannel: bool | None
    paragraphs: list[AssemblyAiParagraph]
    project_id: int
    prompt: str | None
    punctuate: bool
    redact_pii: bool
    redact_pii_audio: bool
    redact_pii_audio_options: dict[str, Any] | None
    redact_pii_audio_quality: str | None
    redact_pii_policies: list[str] | None
    redact_pii_sub: str | None
    sentences: list[AssemblyAiSentence]
    sentiment_analysis: bool
    sentiment_analysis_results: list[dict[str, Any]] | None
    speaker_labels: bool
    speaker_options: dict[str, Any] | None
    speakers_expected: int | None
    speech_model: str | None
    speech_model_used: str
    speech_models: list[str]
    speech_threshold: float | None
    speech_understanding: AssemblyAiSpeechUnderstanding
    speed_boost: bool
    status: str
    summarization: bool
    summary: str | None
    summary_model: str | None
    summary_type: str | None
    temperature: float
    text: str
    throttled: bool
    token_id: int
    topics: list[dict[str, Any]]
    translated_texts: dict[str, Any] | None
    utterances: list[AssemblyAiUtterance]
    webhook_auth: bool
    webhook_auth_header_name: str | None
    webhook_status_code: int | None
    webhook_url: str | None
    word_boost: list[str]
    words: list[AssemblyAiWord]
