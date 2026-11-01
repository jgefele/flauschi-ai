from datetime import date, timedelta

from pydantic import BaseModel, RootModel

from flauschi_ai.utils import slugify


class SpotifyEpisodeMetadata(BaseModel):
    id: str
    publication_date: date
    title: str
    description: str
    duration: timedelta

    @property
    def slug(self) -> str:
        return slugify(self.publication_date.isoformat(), self.title)


SpotifyEpisodeMetadataCollection = RootModel[dict[str, SpotifyEpisodeMetadata]]
