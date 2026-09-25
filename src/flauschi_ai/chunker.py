import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import cast

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
from transformers import AutoTokenizer, PreTrainedTokenizerBase

from flauschi_ai.constants import EPISODE_PATH
from flauschi_ai.models import EpisodeTranscript
from flauschi_ai.persistence import load_episode
from flauschi_ai.utils import clamp


@dataclass
class Chunk:
    text: str
    length: int
    start: timedelta
    end: timedelta


class TurnBasedChunker:
    TURN_SEPARATOR: str = "\n"
    TURN_SEPARATOR_LENGTH: int = 1  # TODO: this is not always right. E.g. ' ' often is no extra token, but '\n' is.

    max_length_per_chunk: int
    overlap_length_per_chunk: int
    length_function: Callable[[str], int]

    def __init__(
        self,
        max_length_per_chunk: int,
        overlap_length_per_chunk: int,
        length_function: Callable[[str], int],
    ):
        self.max_length_per_chunk = max_length_per_chunk
        self.overlap_length_per_chunk = overlap_length_per_chunk
        self.length_function = length_function

    def _take_chunks_with_length_limit(
        self, chunks: list[Chunk], max_length: int, take_at_least_one: bool
    ):
        taken: list[Chunk] = []
        total_length = 0
        for i, entry in enumerate(chunks):
            sep_length = self.TURN_SEPARATOR_LENGTH if taken else 0
            added_length = sep_length + entry.length
            allow_overflow = take_at_least_one and not taken
            if total_length + added_length > max_length and not allow_overflow:
                return taken, chunks[i:]
            taken.append(entry)
            total_length += added_length
        return taken, list[Chunk]()

    def _merge_chunks(self, chunks: list[Chunk]) -> Chunk:
        return Chunk(
            text=self.TURN_SEPARATOR.join(e.text for e in chunks),
            length=sum(c.length for c in chunks)
            + (len(chunks) - 1) * self.TURN_SEPARATOR_LENGTH,
            start=chunks[0].start,
            end=chunks[-1].end,
        )

    def _transcript_to_speaker_turn_chunks(
        self, transcript: EpisodeTranscript
    ) -> list[Chunk]:
        entries: list[Chunk] = []
        for block in transcript.speaker_turns:
            speaker = transcript.speakers[block.speaker_id]
            sentences = " ".join(s.text for s in block.sentences)
            text = f"{speaker}: {sentences}"
            entries.append(
                Chunk(
                    text=text,
                    length=self.length_function(text),
                    start=block.start,
                    end=block.end,
                )
            )
        return entries

    def _build_overlap(
        self, previous_chunks: list[Chunk], next_chunk: Chunk
    ) -> list[Chunk]:
        overlap_limit = clamp(
            self.max_length_per_chunk
            - (next_chunk.length + self.TURN_SEPARATOR_LENGTH),
            lower_limit=0,
            upper_limit=self.overlap_length_per_chunk,
        )

        overlap_chunks, _ = self._take_chunks_with_length_limit(
            list(reversed(previous_chunks)), overlap_limit, take_at_least_one=False
        )
        overlap_chunks.reverse()
        return overlap_chunks

    def transcript_to_chunks(self, transcript: EpisodeTranscript) -> list[Chunk]:
        remaining_chunks = self._transcript_to_speaker_turn_chunks(transcript)
        merged_chunks: list[Chunk] = []
        while remaining_chunks:
            chunk_entries, rest = self._take_chunks_with_length_limit(
                remaining_chunks, self.max_length_per_chunk, take_at_least_one=True
            )
            merged_chunks.append(self._merge_chunks(chunk_entries))

            if not rest:
                break

            overlap = self._build_overlap(chunk_entries, rest[0])
            remaining_chunks = overlap + rest
        return merged_chunks

    @classmethod
    def from_huggingface_tokenizer(
        cls,
        model_name: str,
        max_tokens_per_chunk: int,
        overlap_tokens_per_chunk: int,
    ):
        tokenizer = cast(
            PreTrainedTokenizerBase,
            AutoTokenizer.from_pretrained(model_name),
        )

        def token_count(s: str) -> int:
            result = tokenizer(s)
            token_ids = cast(list[int], result["input_ids"])
            return len(token_ids)

        return cls(
            max_length_per_chunk=max_tokens_per_chunk,
            overlap_length_per_chunk=overlap_tokens_per_chunk,
            length_function=token_count,
        )


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        episode_path = Path(sys.argv[1])
    else:
        episode_path = max(EPISODE_PATH.glob("*.json"))
        print(f"No episode given: using {episode_path}")
    episode = load_episode(episode_path)

    chunker = TurnBasedChunker.from_huggingface_tokenizer(
        model_name="Qwen/Qwen3-Embedding-8B",
        max_tokens_per_chunk=1000,
        overlap_tokens_per_chunk=250,
    )

    noop_chunker = TurnBasedChunker.from_huggingface_tokenizer(
        model_name="Qwen/Qwen3-Embedding-8B",
        max_tokens_per_chunk=9999999999999,
        overlap_tokens_per_chunk=0,
    )

    chunks = chunker.transcript_to_chunks(episode.transcript)

    for chunk in chunks:
        print(
            "-" * 20,
            chunk.length,
            chunk.start,
            chunk.end,
        )
        print(chunk.text)

    chunk_token_counts = sorted(chunk.length for chunk in chunks)
    num_chunks = len(chunks)
    total_token_count = noop_chunker.transcript_to_chunks(episode.transcript)[0].length
    print(
        "\n" * 3,
        "#chunks",
        num_chunks,
        "min",
        min(chunk_token_counts),
        "median",
        chunk_token_counts[num_chunks // 2],
        "max",
        max(chunk_token_counts),
        "token count (chunked with overlap)",
        sum(chunk_token_counts),
        "token count (original text)",
        total_token_count,
    )
