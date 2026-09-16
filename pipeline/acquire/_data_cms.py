"""data.cms.gov data-api client (JSON:API): resolve a dataset UUID, page DE-filtered rows.

Preserves display column names. Two API distributions share the newest vintage, so the pick is
deterministic; the resolved UUID is recorded in provenance (new UUID per release).
"""

from __future__ import annotations

import re

from ._http import get_json

CATALOG = "https://data.cms.gov/data.json"
BASE = "https://data.cms.gov/data-api/v1/dataset"
PAGE = 5000  # data-api caps `size` at 5000

_UUID = re.compile(r"/dataset/([0-9a-f-]{36})")
_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_catalog_cache: dict | None = None


def _catalog() -> dict:
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = get_json(CATALOG)
    return _catalog_cache


def _uuid_of(dist: dict) -> str | None:
    for key in ("identifier", "accessURL", "downloadURL", "@id"):
        val = dist.get(key)
        if isinstance(val, str):
            match = _UUID.search(val)
            if match:
                return match.group(1)
    return None


def _vintage_of(dist: dict) -> str:
    match = _DATE.search(dist.get("title", ""))
    return match.group(1) if match else ""


def resolve(title: str) -> tuple[str, str]:
    """Return (uuid, vintage) for the newest API distribution of the dataset named `title`."""
    for dataset in _catalog().get("dataset", []):
        if dataset.get("title") != title:
            continue
        api = [d for d in dataset.get("distribution", []) if d.get("format") == "API"]
        if not api:
            break
        best = max(api, key=_vintage_of)
        uuid = _uuid_of(best)
        if uuid:
            return uuid, _vintage_of(best)
        break
    raise RuntimeError(f"no API distribution found in catalog for dataset: {title!r}")


def fetch_schema(uuid: str) -> list[str]:
    """Return the live column names (one-row probe)."""
    rows = get_json(f"{BASE}/{uuid}/data", {"size": 1})
    return list(rows[0].keys()) if rows else []


def fetch_state_rows(uuid: str, state_col: str, state: str) -> list[dict]:
    """Page every row where state_col == state. requests encodes the filter[...] key."""
    out: list[dict] = []
    offset = 0
    while True:
        page = get_json(
            f"{BASE}/{uuid}/data",
            {f"filter[{state_col}]": state, "size": PAGE, "offset": offset},
        )
        out.extend(page)
        if len(page) < PAGE:
            return out
        offset += PAGE
