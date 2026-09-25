from pathlib import Path

DEFAULT_COLLECTION_NAME = "default_embeddings"
DEFAULT_EMBEDDING_MODEL = "openai/text-embedding-3-small"
DEFAULT_EMBEDDING_SIZE = 1536
DEFAULT_TOKENIZATION_MODEL = "Qwen/Qwen3-Embedding-8B"
DEFAULT_MAX_TOKENS_PER_CHUNK = 1000
DEFAULT_OVERLAP_TOKENS_PER_CHUNK = 250
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DEFAULT_FEED_URL = "https://feeds.megaphone.fm/GLT4060321204"
RSS_FEED_CHECK_INTERVAL_SECONDS = 10 * 60
PROJECT_PATH = Path(__file__).parent.parent.parent.absolute()
DATA_PATH = PROJECT_PATH / "data"
EPISODE_PATH = DATA_PATH / "episode"
QDRANT_PATH = DATA_PATH / "qdrant"
DEFAULT_TOP_K = 10