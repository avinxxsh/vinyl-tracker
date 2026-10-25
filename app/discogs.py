import os
import re

import httpx

USER_AGENT = "VinylTracker/1.0"
DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN")

# Discogs appends a disambiguation suffix like "Charles (2)" to artist names
# that collide with another artist in their database.
_DISAMBIGUATION_SUFFIX = re.compile(r"\s*\(\d+\)$")


def _auth_params() -> dict:
    return {"token": DISCOGS_TOKEN} if DISCOGS_TOKEN else {}


def get_release(release_id: int) -> dict | None:
    """Fetch full details for a single Discogs release.

    Returns None on any failure (missing id, network error, not found) so
    callers can treat this as best-effort and keep going.
    """
    if not release_id:
        return None

    try:
        resp = httpx.get(
            f"https://api.discogs.com/releases/{release_id}",
            headers={"User-Agent": USER_AGENT},
            params=_auth_params(),
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
    artists = data.get("artists") or []

    artist = ", ".join(
        _DISAMBIGUATION_SUFFIX.sub("", a.get("name", "").strip())
        for a in artists
        if a.get("name")
    ) or None

    return {
        "artist": artist,
        "title": data.get("title") or None,
        "genre": ", ".join(genres + styles) or None,
        "cover_url": images[0]["uri"] if images else None,
        "label": labels[0].get("name") if labels else None,
        "pressing_year": data.get("year") or None,
        "discogs_release_id": release_id,
    }


def fetch_release(release_id: int) -> dict | None:
    """Backfill genre/cover/label/year for a record that already has
    artist and title filled in. Thin wrapper around get_release()."""
    return get_release(release_id)


def search_releases(query: str, per_page: int = 10) -> list[dict] | None:
    """Search Discogs releases by free text. Returns None if no API token
    is configured, since the search endpoint requires authentication."""
    if not DISCOGS_TOKEN:
        return None
    if not query.strip():
        return []

    try:
        resp = httpx.get(
            "https://api.discogs.com/database/search",
            headers={"User-Agent": USER_AGENT},
            params={
                "q": query.strip(),
                "type": "release",
                "per_page": per_page,
                **_auth_params(),
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
    except httpx.HTTPError:
        return []

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "year": item.get("year"),
                "label": (item.get("label") or [None])[0],
                "thumb": item.get("thumb") or item.get("cover_image"),
            }
        )
    return results
