from datetime import date, timedelta

from pydantic import BaseModel

from flauschi_ai.utils import slugify


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
