"""provider-data DKAN datastore client: resolve UUID, page DE-filtered rows.

Machine column names (npi, state, ...). `limit` caps at 1000; a bare-equals condition sends no
operator ("==" fails validation).
"""

from __future__ import annotations

from ._http import get_json

METASTORE = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"
QUERY = "https://data.cms.gov/provider-data/api/1/datastore/query"
PAGE = 1000  # DKAN caps `limit` at 1000


def resolve(title: str) -> str:
    """Return the dataset UUID for the metastore item named `title`."""
    for item in get_json(METASTORE, {"show-reference-ids": "false"}):
        if item.get("title") == title:
            return item["identifier"]
    raise RuntimeError(f"dataset not found in provider-data metastore: {title!r}")


def fetch_schema(uuid: str) -> list[str]:
    """Return the live column names (one-row probe)."""
    res = get_json(f"{QUERY}/{uuid}/0", {"limit": 1})
    results = res.get("results", [])
    return list(results[0].keys()) if results else []


def fetch_state_rows(uuid: str, state_col: str, state: str) -> list[dict]:
    """Page every row where state_col == state (default-equals condition)."""
    out: list[dict] = []
    offset = 0
    while True:
        res = get_json(
            f"{QUERY}/{uuid}/0",
            {
                "conditions[0][property]": state_col,
                "conditions[0][value]": state,
                "limit": PAGE,
                "offset": offset,
            },
        )
        rows = res.get("results", [])
        out.extend(rows)
        if len(rows) < PAGE:
            return out
        offset += PAGE
