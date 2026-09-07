from datetime import date, timedelta

import feedparser
from pydantic import BaseModel

from flauschi_pipeline.utils import slugify


class EpisodeMetadata(BaseModel):
    id: str
    publication_date: date
    title: str
    description: str
    audio_url: str
    duration: timedelta

    @property
    def slug(self) -> str:
        return slugify(f"{self.publication_date.isoformat()}-{self.title}")


class FeedMalformedException(Exception):
    pass


def _get_pubdate(entry) -> date:
    y, m, d, *_ = entry.published_parsed
    return date(y, m, d)


def _get_audio_url(entry) -> str:
    audio_hrefs: list[str] = [
        link.href
        for link in entry.get("enclosures") or []
        if link["type"] == "audio/mpeg"
    ]
    if audio_hrefs:
        return audio_hrefs[0]
    else:
        raise FeedMalformedException("No audio file present")


def parse_feed(
    url: str, last_modified: str | None
) -> tuple[list[EpisodeMetadata], str]:
    feed = feedparser.parse(url, modified=last_modified)

    episodes = (
        EpisodeMetadata(
            title=entry.title,
            description=entry.description,
            publication_date=_get_pubdate(entry),
            duration=timedelta(seconds=int(entry.itunes_duration)),
            audio_url=_get_audio_url(entry),
            id=entry.id,
        )
        for entry in feed.entries
    )

    return (
        sorted(episodes, key=lambda r: r.publication_date, reverse=True),
        feed.get("modified"),
    )
