"""drift-watch: poll upstream CMS schemas vs Source.required_columns; exit 1 on a missing column.

Non-gating scheduled Action (opens an issue on drift). Covers the four API-backed sources.
Run: uv run python -m pipeline.driftwatch
"""

from __future__ import annotations

import hashlib
import json
import sys

from pipeline.acquire import _data_cms, _provider_data
from pipeline.sources import ALL_SOURCES, Source

_API_ACQUIRE = {"api_data_cms", "api_provider_data"}


def _live_columns(src: Source) -> tuple[str, str, list[str]]:
    """Return (uuid, vintage, live column names) for an API source."""
    assert src.api_keyword, f"{src.key}: api source needs api_keyword"
    if src.acquire == "api_data_cms":
        uuid, vintage = _data_cms.resolve(src.api_keyword)
        return uuid, vintage, _data_cms.fetch_schema(uuid)
    uuid = _provider_data.resolve(src.api_keyword)
    return uuid, "", _provider_data.fetch_schema(uuid)


def _pinned_hash(src: Source) -> str | None:
    sidecar = src.path.with_suffix(src.path.suffix + ".provenance.json")
    if sidecar.exists():
        return json.loads(sidecar.read_text()).get("schema_hash")
    return None


def check(src: Source) -> list[str]:
    """Print one status line. Return the list of drift problems (empty = clean)."""
    try:
        _uuid, vintage, live = _live_columns(src)
    except Exception as exc:  # network, missing dataset, bad payload — all are drift signals
        print(f"[ERROR] {src.key}: could not resolve/fetch schema: {exc}")
        return [f"{src.key}: could not resolve/fetch schema: {exc}"]

    missing = [c for c in src.required_columns if c not in live]
    present = len(src.required_columns) - len(missing)
    live_hash = hashlib.sha256("\x1f".join(live).encode()).hexdigest()[:16]
    pinned = _pinned_hash(src)
    note = ""
    if pinned and pinned != live_hash:
        note = f"  (schema changed since last acquire: {pinned} -> {live_hash})"

    status = "DRIFT" if missing else "OK"
    print(
        f"[{status}] {src.key}: {len(live)} cols upstream, "
        f"required present {present}/{len(src.required_columns)}, "
        f"vintage {vintage or 'n/a'}{note}"
    )
    if missing:
        return [f"{src.key}: required columns missing upstream: {missing}"]
    return []


def main() -> int:
    problems: list[str] = []
    for src in ALL_SOURCES:
        if src.acquire in _API_ACQUIRE:
            problems.extend(check(src))
    if problems:
        print("\nDRIFT DETECTED:", file=sys.stderr)
        for problem in problems:
            print(f" - {problem}", file=sys.stderr)
        return 1
    print("\nNo drift: every required column is present upstream.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
