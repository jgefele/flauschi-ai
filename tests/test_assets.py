from datetime import date, timedelta

from flauschi_pipeline.defs.assets import IngestEpisodeRunConfig
from flauschi_pipeline.feed import Episode


def test_episode_feedentryrunconfig_roundtrip() -> None:
    episode = Episode(
        id="episode-123",
        publication_date=date(2024, 7, 15),
        title="Ein Test Episode",
        description="Eine Testbeschreibung",
        audio_url="https://example.com/audio/episode-123.mp3",
        duration=timedelta(hours=1, minutes=2, seconds=3),
    )

    config = IngestEpisodeRunConfig.from_episode(episode)
    assert config.id == episode.id
    assert config.publication_date == "2024-07-15"
    assert config.title == episode.title
    assert config.description == episode.description
    assert config.audio_url == episode.audio_url
    assert config.duration == "PT1H2M3S"

    assert config.to_episode() == episode
