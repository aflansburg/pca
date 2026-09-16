"""Acquire source snapshots before staging: API -> DE CSV + provenance sidecar; bulk -> stream a
pinned file; static -> skipped. Run: uv run python -m pipeline.acquire.run [--source KEY ...]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from pipeline.acquire import _data_cms, _provider_data, bulk
from pipeline.config import STATE
from pipeline.sources import ALL_SOURCES, Source


def _write_csv(path: Path, rows: list[dict]) -> list[str]:
    """Write rows as CSV. Columns = first row's keys, plus any extra keys seen later."""
    columns = list(rows[0].keys())
    seen = set(columns)
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return columns


def _write_provenance(src: Source, uuid: str, vintage: str, columns: list[str], rows: int) -> None:
    schema_hash = hashlib.sha256("\x1f".join(columns).encode()).hexdigest()[:16]
    prov = {
        "source": src.key,
        "acquire": src.acquire,
        "dataset_title": src.api_keyword,
        "uuid": uuid,
        "vintage": vintage,
        "release": src.release,
        "state": STATE,
        "row_count": rows,
        "columns": columns,
        "schema_hash": schema_hash,
        "fetched_at": datetime.now(tz=UTC).isoformat(),
    }
    sidecar = src.path.with_suffix(src.path.suffix + ".provenance.json")
    sidecar.write_text(json.dumps(prov, indent=2))


def acquire(src: Source) -> None:
    if src.acquire == "bulk":
        bulk.fetch(src)
        print(f"{src.key}: bulk fetched -> {src.path.name}")
        return
    if src.acquire == "api_data_cms":
        assert src.api_keyword, f"{src.key}: api source needs api_keyword"
        uuid, vintage = _data_cms.resolve(src.api_keyword)
        rows = _data_cms.fetch_state_rows(uuid, src.state_col, STATE)
    elif src.acquire == "api_provider_data":
        assert src.api_keyword, f"{src.key}: api source needs api_keyword"
        uuid, vintage = _provider_data.resolve(src.api_keyword), ""
        rows = _provider_data.fetch_state_rows(uuid, src.state_col, STATE)
    else:
        print(f"{src.key}: static; nothing to fetch")
        return
    if not rows:
        raise RuntimeError(f"{src.key}: API returned 0 rows for state {STATE}")
    columns = _write_csv(src.path, rows)
    _write_provenance(src, uuid, vintage, columns, len(rows))
    print(f"{src.key}: {len(rows)} {STATE} rows -> {src.path.name} (uuid {uuid} vintage {vintage or 'n/a'})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch source snapshots before staging.")
    parser.add_argument("--source", nargs="*", help="source keys to fetch (default: all non-static)")
    args = parser.parse_args()
    keys = set(args.source or [])
    for src in ALL_SOURCES:
        if keys:
            if src.key in keys:
                acquire(src)
        elif src.acquire != "static":
            acquire(src)


if __name__ == "__main__":
    main()
