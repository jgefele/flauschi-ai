from pathlib import Path

from flauschi_ai.models import Episode


def load_episode(file: Path) -> Episode:
    return Episode.model_validate_json(file.read_text(encoding="utf8"))
