from datetime import timedelta

import pytest

from flauschi_pipeline.chunker import TurnBasedChunker
from flauschi_pipeline.models import (
    EpisodeSentence,
    EpisodeSpeakerTurn,
    EpisodeTranscript,
)

SPEAKER_IDS = {"Jan": 0, "Olli": 1}


def make_turn(
    text: str, speaker: str, start: int = 0, end: int = 0
) -> EpisodeSpeakerTurn:
    return EpisodeSpeakerTurn(
        speaker_id=SPEAKER_IDS[speaker],
        sentences=[
            EpisodeSentence(
                start=timedelta(seconds=start),
                end=timedelta(seconds=end),
                text=text,
            )
        ],
    )


def make_transcript(*turns: EpisodeSpeakerTurn) -> EpisodeTranscript:
    # "speaker_blocks" is the validation alias for the "speaker_turns" field.
    return EpisodeTranscript(
        speakers={speaker_id: speaker for speaker, speaker_id in SPEAKER_IDS.items()},
        speaker_blocks=list(turns),
    )


def make_chunker(
    max_length_per_chunk: int, overlap_length_per_chunk: int
) -> TurnBasedChunker:
    return TurnBasedChunker(
        max_length_per_chunk=max_length_per_chunk,
        overlap_length_per_chunk=overlap_length_per_chunk,
        length_function=len,
    )


def texts(chunks: list) -> list[str]:
    return [chunk.text for chunk in chunks]


def test_empty_transcript_yields_no_chunks():
    chunker = make_chunker(100, 10)

    assert chunker.transcript_to_chunks(make_transcript()) == []


def test_single_turn_becomes_single_chunk():
    chunker = make_chunker(100, 10)

    chunks = chunker.transcript_to_chunks(
        make_transcript(make_turn("aaaa", speaker="Jan"))
    )

    assert texts(chunks) == ["Jan: aaaa"]


def test_turns_fitting_exactly_are_merged_into_one_chunk():
    first = make_turn("aaaa", speaker="Jan")
    second = make_turn("bbbb", speaker="Olli")
    max_length = len("Jan: aaaa\nOlli: bbbb")

    chunks = make_chunker(max_length, 9).transcript_to_chunks(
        make_transcript(first, second)
    )

    assert texts(chunks) == ["Jan: aaaa\nOlli: bbbb"]


def test_turn_exceeding_max_length_is_emitted_oversized():
    oversized_text = "x" * 12
    chunker = make_chunker(10, 4)

    chunks = chunker.transcript_to_chunks(
        make_transcript(make_turn(oversized_text, speaker="Jan"))
    )

    assert texts(chunks) == [f"Jan: {oversized_text}"]


def test_oversized_turn_after_normal_turn_gets_own_chunk():
    oversized_text = "x" * 12
    chunker = make_chunker(10, 4)

    chunks = chunker.transcript_to_chunks(
        make_transcript(
            make_turn("aaaa", speaker="Jan"),
            make_turn(oversized_text, speaker="Olli"),
        )
    )

    assert texts(chunks) == [
        "Jan: aaaa",
        f"Olli: {oversized_text}",
    ]


def test_one_over_limit_splits_into_disjoint_chunks():
    first = make_turn("aaaa", speaker="Jan")
    second = make_turn("bbbb", speaker="Olli")
    max_length = len("Jan: aaaa\nOlli: bbbb") - 1

    chunks = make_chunker(max_length, 0).transcript_to_chunks(
        make_transcript(first, second)
    )

    assert texts(chunks) == ["Jan: aaaa", "Olli: bbbb"]


def test_zero_overlap_produces_disjoint_chunks():
    turns = [
        make_turn("aaaa", speaker="Jan"),
        make_turn("bbbb", speaker="Olli"),
        make_turn("cccc", speaker="Jan"),
    ]

    chunks = make_chunker(14, 0).transcript_to_chunks(make_transcript(*turns))

    assert texts(chunks) == [
        "Jan: aaaa",
        "Olli: bbbb",
        "Jan: cccc",
    ]


def test_overlap_can_contain_multiple_turns():
    turns = [
        make_turn("aaaa", speaker="Jan"),
        make_turn("bbb", speaker="Olli"),
        make_turn("cccc", speaker="Jan"),
        make_turn("ddd", speaker="Olli"),
        make_turn("xxxxxxxxx", speaker="Jan"),
    ]
    chunker = make_chunker(30, 20)

    chunks = chunker.transcript_to_chunks(make_transcript(*turns))

    assert texts(chunks) == [
        "Jan: aaaa\nOlli: bbb\nJan: cccc",
        "Olli: bbb\nJan: cccc\nOlli: ddd",
        "Olli: ddd\nJan: xxxxxxxxx",
    ]


def test_chunk_time_span_covers_first_and_last_sentence_of_turns():
    chunker = make_chunker(100, 0)
    turn = EpisodeSpeakerTurn(
        speaker_id=SPEAKER_IDS["Jan"],
        sentences=[
            EpisodeSentence(
                start=timedelta(seconds=0),
                end=timedelta(seconds=5),
                text="Hello",
            ),
            EpisodeSentence(
                start=timedelta(seconds=5),
                end=timedelta(seconds=10),
                text="world",
            ),
        ],
    )
    second_turn = make_turn("Hi", speaker="Olli", start=10, end=20)

    chunks = chunker.transcript_to_chunks(make_transcript(turn, second_turn))

    assert texts(chunks) == ["Jan: Hello world\nOlli: Hi"]
    assert chunks[0].start == timedelta(0)
    assert chunks[0].end == timedelta(seconds=20)


def test_chunk_time_span_is_preserved_across_overlap():
    chunker = make_chunker(22, 10)
    turns = [
        make_turn("aaaa", speaker="Jan", start=0, end=10),
        make_turn("bbbb", speaker="Olli", start=10, end=20),
        make_turn("cccc", speaker="Jan", start=20, end=30),
    ]

    chunks = chunker.transcript_to_chunks(make_transcript(*turns))

    assert texts(chunks) == [
        "Jan: aaaa\nOlli: bbbb",
        "Olli: bbbb\nJan: cccc",
    ]
    assert (chunks[0].start, chunks[0].end) == (
        timedelta(0),
        timedelta(seconds=20),
    )
    assert (chunks[1].start, chunks[1].end) == (
        timedelta(seconds=10),
        timedelta(seconds=30),
    )


def test_sentences_within_turn_are_joined_and_speaker_prefixed():
    chunker = make_chunker(100, 0)
    turn = EpisodeSpeakerTurn(
        speaker_id=SPEAKER_IDS["Jan"],
        sentences=[
            EpisodeSentence(
                start=timedelta(0),
                end=timedelta(seconds=5),
                text="Hello",
            ),
            EpisodeSentence(
                start=timedelta(seconds=5),
                end=timedelta(seconds=10),
                text="world",
            ),
        ],
    )

    chunks = chunker.transcript_to_chunks(
        make_transcript(turn, make_turn("Hi", speaker="Olli"))
    )

    assert texts(chunks) == ["Jan: Hello world\nOlli: Hi"]


@pytest.mark.timeout(5)
def test_overlap_always_leaves_room_for_separator():
    chunker = make_chunker(20, 10)
    turns = [
        make_turn("aaaa", speaker="Jan"),
        make_turn("bbbb", speaker="Olli"),
        make_turn("ccccc", speaker="Jan"),
    ]

    chunks = chunker.transcript_to_chunks(make_transcript(*turns))

    assert texts(chunks) == [
        "Jan: aaaa\nOlli: bbbb",
        "Jan: ccccc",
    ]
