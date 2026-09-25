from pathlib import Path

DEFAULT_FEED_URL = "https://feeds.megaphone.fm/GLT4060321204"
RSS_FEED_CHECK_INTERVAL_SECONDS = 10 * 60
PROJECT_PATH = Path(__file__).parent.parent.parent.absolute()
DATA_PATH = PROJECT_PATH / "data"
EPISODE_PATH = DATA_PATH / "episode"
QDRANT_PATH = DATA_PATH / "qdrant"
DEFAULT_TOP_K = 10