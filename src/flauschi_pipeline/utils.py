import re
import unicodedata


def slugify(text: str, lower: bool = True, max_length: int | None = None) -> str:
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
