import re
import unicodedata
from datetime import timedelta
from typing import Any


def slugify(*elements: Any, lower: bool = True, max_length: int | None = None) -> str:  # pyright: ignore[reportExplicitAny, reportAny]
    SEPARATOR = "-"
    UMLAUTS = str.maketrans(
        {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
            "Ä": "Ae",
            "Ö": "Oe",
            "Ü": "Ue",
            "ẞ": "SS",
        }
    )

    text = "-".join(map(str, elements))
    text = text.translate(UMLAUTS)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9]", SEPARATOR, text)
    text = re.sub(f"{SEPARATOR}+", SEPARATOR, text)
    if lower:
        text = text.lower()
    if max_length is not None:
        text = text[:max_length]
    text = text.strip(SEPARATOR)
    return text


def clamp(value: int, lower_limit: int, upper_limit: int) -> int:
    return max(lower_limit, min(value, upper_limit))


def format_timecode(d: timedelta) -> str:
    mm, ss = divmod(d.seconds, 60)
    hh, mm = divmod(mm, 60)
    if hh:
        return f"{hh:d}:{mm:02d}:{ss:02d}"
    else:
        return f"{mm:d}:{ss:02d}"
