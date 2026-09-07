from pydantic import BaseModel


class AudioArchiveMetadata(BaseModel):
    source_url: str
    redirected_url: str
    content_type: str | None
    archive_url: str
    file_size: int
