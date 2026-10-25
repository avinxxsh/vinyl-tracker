import json
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.models import Setting

CACHE_KEY = "exchange_rates"
MAX_AGE = timedelta(hours=12)
API_URL = "https://open.er-api.com/v6/latest/USD"


def _fetch() -> dict | None:
    try:
        resp = httpx.get(API_URL, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("result") != "success":
            return None
        return data.get("rates") or None
    except httpx.HTTPError:
        return None


def _load_cache(db: Session) -> dict | None:
    setting = db.get(Setting, CACHE_KEY)
    if not setting or not setting.value:
        return None
    try:
        return json.loads(setting.value)
    except (json.JSONDecodeError, TypeError):
        return None


def _save_cache(db: Session, rates: dict) -> None:
    payload = json.dumps({"rates": rates, "fetched_at": datetime.utcnow().isoformat()})
    setting = db.get(Setting, CACHE_KEY)
    if setting:
        setting.value = payload
    else:
        db.add(Setting(key=CACHE_KEY, value=payload))
    db.commit()


def get_rates(db: Session, force: bool = False) -> dict:
    """Return a {currency_code: rate_vs_usd} dict, refreshing from the API
    if the cache is missing or stale (older than MAX_AGE). Falls back to a
    stale cache, or an empty dict, if the API can't be reached, so a record
    whose currency matches the display currency still works offline."""
    cached = _load_cache(db)
    is_stale = True
    if cached:
        try:
            fetched_at = datetime.fromisoformat(cached["fetched_at"])
            is_stale = datetime.utcnow() - fetched_at > MAX_AGE
        except (KeyError, ValueError):
            is_stale = True

    if force or is_stale:
        fresh = _fetch()
        if fresh:
            _save_cache(db, fresh)
            return fresh

    return cached["rates"] if cached else {}


def last_updated(db: Session) -> datetime | None:
    cached = _load_cache(db)
    if not cached:
        return None
    try:
        return datetime.fromisoformat(cached["fetched_at"])
    except (KeyError, ValueError):
        return None


def convert(amount: float | None, from_code: str | None, to_code: str, rates: dict) -> float | None:
    if amount is None:
        return None
    from_code = from_code or to_code
    if from_code == to_code:
        return amount
    if from_code not in rates or to_code not in rates:
        return None
    usd_amount = amount / rates[from_code]
    return usd_amount * rates[to_code]
