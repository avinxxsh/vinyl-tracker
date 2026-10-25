import os

import httpx

USER_AGENT = "VinylTracker/1.0"
DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN")


def fetch_release(release_id: int) -> dict | None:
    """Look up a release on Discogs to backfill genre and cover art.

    Returns None on any failure (missing id, network error, rate limit) so
    callers can treat enrichment as best-effort and keep going.
    """
    if not release_id:
        return None

    headers = {"User-Agent": USER_AGENT}
    params = {}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN

    try:
        resp = httpx.get(
            f"https://api.discogs.com/releases/{release_id}",
            headers=headers,
            params=params,
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
    except httpx.HTTPError:
        return None

    genres = data.get("genres") or []
    styles = data.get("styles") or []
    images = data.get("images") or []
    labels = data.get("labels") or []

    return {
        "genre": ", ".join(genres + styles) or None,
        "cover_url": images[0]["uri"] if images else None,
        "label": labels[0].get("name") if labels else None,
        "pressing_year": data.get("year") or None,
    }
