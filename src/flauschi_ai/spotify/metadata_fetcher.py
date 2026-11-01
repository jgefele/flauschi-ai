import sys
from datetime import date, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from flauschi_ai.models import SpotifyEpisodeMetadata
from flauschi_ai.utils import clamp


def _create_session_with_retries() -> requests.Session:
    session = requests.Session()

    retries = Retry(
        total=5,  # Maximum number of retries
        backoff_factor=1,  # Wait 1s, 2s, 4s, 8s, 10s... between retries
        status_forcelist=[500, 502, 503, 504],  # Retry on these server error codes
        raise_on_status=False,  # Do not raise an exception immediately on these codes
        allowed_methods=[
            "GET",
            "POST",
        ],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def _get_access_token(
    session: requests.Session, client_id: str, client_key: str
) -> str:
    response = session.post(
        "https://accounts.spotify.com/api/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_key,
        },
    )
    response.raise_for_status()
    access_token: str = response.json()["access_token"]

    return access_token


def fetch_episodes(
    client_id: str, client_key: str, max_count: int = sys.maxsize
) -> dict[str, SpotifyEpisodeMetadata]:
    session = _create_session_with_retries()
    access_token = _get_access_token(session, client_id, client_key)

    episodes_dict: dict[str, SpotifyEpisodeMetadata] = {}
    limit = clamp(max_count, 1, 50)
    next_url = f"https://api.spotify.com/v1/shows/1OLcQdw2PFDPG1jo3s0wbp/episodes?limit={limit}"
    while next_url and len(episodes_dict) < max_count:
        response = session.get(
            next_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        episode_page = response.json()

        for episode in episode_page["items"]:
            if episode is None:
                continue

            episode_meta = SpotifyEpisodeMetadata(
                id=episode["id"],
                publication_date=date.fromisoformat(episode["release_date"]),
                title=episode["name"],
                description=episode["description"],
                duration=timedelta(milliseconds=episode["duration_ms"]),
            )

            episodes_dict[episode_meta.slug] = episode_meta

        next_url = episode_page.get("next")

    return episodes_dict
