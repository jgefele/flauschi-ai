import re

TIMESTAMP_LINK_PATTERN = re.compile(
    r"""
    (?P<timestamp_display>
        \[
            (?P<hour>\d?\d:)?         # Optional hour
            (?P<minute>\d?\d)          # Required minute
            :
            (?P<second>\d?\d)          # Required second
        \]
    )
    \(
        \#                        # Literal '#' initiating the ID
        (?P<slug>
            \d{4}-\d{2}-\d{2}-    # Date prefix YYYY-MM-DD
            [^)]+                 # Trailing ID payload
        )
    \)
    """,
    re.VERBOSE,
)


class LinkReplacer:
    def __init__(self):
        self._mapping: dict[str, str] = {}

    def set_mapping(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def replace_links(self, markdown: str) -> str:
        return TIMESTAMP_LINK_PATTERN.sub(self._replace_link, markdown)

    def _replace_link(self, match: re.Match[str]) -> str:
        slug = match.group("slug")
        spotify_id = self._mapping.get(slug)
        timestamp_display = match.group("timestamp_display")

        if not spotify_id:
            return timestamp_display

        raw_hour = match.group("hour")  # e.g., "1:" or None
        hours = int(raw_hour.rstrip(":")) if raw_hour else 0
        minutes = int(match.group("minute"))
        seconds = int(match.group("second"))
        total_seconds = (hours * 3600) + (minutes * 60) + seconds

        return f"{timestamp_display}(https://open.spotify.com/episode/{spotify_id}?t={total_seconds})"
