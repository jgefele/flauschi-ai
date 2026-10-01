import re
from collections.abc import Generator
from pathlib import Path

from flauschi_ai.constants import EPISODE_PATH
from flauschi_ai.models import Episode


def load_episode(file: Path) -> Episode:
    return Episode.model_validate_json(file.read_text(encoding="utf8"))


def load_episodes(pattern: str | None) -> Generator[Episode]:
    for f in sorted(EPISODE_PATH.glob("*.json")):
        if f.is_file() and (pattern is None or re.search(pattern, f.name)):
            yield load_episode(f)
