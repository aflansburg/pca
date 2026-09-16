"""JSON GET with a timeout and a few retries, shared by the acquisition clients."""

from __future__ import annotations

import time

import requests

_TIMEOUT = 120  # seconds; paging pulls thousands of rows per page
_RETRIES = 3


def get_json(url: str, params: dict | None = None):
    """GET `url` and return parsed JSON. Retry a few times on transient network errors."""
    last: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last = exc
            time.sleep(2**attempt)  # 1s, 2s, 4s backoff
    raise RuntimeError(f"GET failed after {_RETRIES} attempts: {url}") from last
