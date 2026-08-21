"""Hotel collector call and the date arithmetic around it."""
from __future__ import annotations

import os
import time
from datetime import date, timedelta
from typing import Any

import requests

BASE = "https://api.quanticdata.io/v1"
_s = requests.Session()


def _h() -> dict[str, str]:
    key = os.environ.get("QUANTICDATA_API_KEY")
    if not key:
        raise SystemExit("set QUANTICDATA_API_KEY — https://app.quanticdata.io/register")
    return {"Authorization": f"Bearer {key}"}


def future_date(days_ahead: int) -> str:
    """YYYY-MM-DD, N days from today. Scheduled jobs must never request the past."""
    return (date.today() + timedelta(days=days_ahead)).isoformat()


def stay(check_in: str, nights: int) -> tuple[str, str]:
    start = date.fromisoformat(check_in)
    if start <= date.today():
        raise SystemExit(f"check-in {check_in} is not in the future")
    return check_in, (start + timedelta(days=nights)).isoformat()


def hotels(location: str, check_in: str, check_out: str, *, adults: int = 2,
           currency: str | None = None, country: str = "us", lang: str = "en",
           max_results: int = 30) -> list[dict]:
    body: dict[str, Any] = {
        "location": location,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "country": country,
        "lang": lang,
        "max_results": max_results,
    }
    if currency:
        body["currency"] = currency

    r = _s.post(f"{BASE}/scraper/collectors/hotels/run", json=body, headers=_h(), timeout=300)
    data = r.json()
    if data.get("type") == "error" or not r.ok:
        raise RuntimeError(f"hotels ({r.status_code}): {data.get('message')}")

    run = data.get("payload", {})
    while run.get("status") in ("queued", "running"):
        time.sleep(3)
        run = _s.get(f"{BASE}/scraper/collectors/runs/{run['run_id']}",
                     headers=_h(), timeout=60).json().get("payload", {})
    return run.get("results") or []
