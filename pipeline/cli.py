"""Run the pipeline: `python -m pipeline.cli` builds all assets in registry order; pass names to
build a subset. A real orchestrator would resolve the DAG from each asset's `inputs`.
"""

from __future__ import annotations

import sys

from pipeline.assets import ASSETS, BY_NAME
from pipeline.ingest._duckdb import connect, scalar


def run(names: list[str] | None = None) -> None:
    selected = ASSETS if not names else tuple(a for a in ASSETS if a.name in set(names))
    if names:
        unknown = set(names) - set(BY_NAME)
        if unknown:
            raise SystemExit(f"unknown asset(s): {sorted(unknown)}. known: {list(BY_NAME)}")
    con = connect()
    try:
        for a in selected:
            a.build(con)
            rows = scalar(con, f"SELECT count(*) FROM {a.output}")
            deps = ", ".join(a.inputs) or "-"
            print(f"[built] {a.name:14} -> {a.output:14} {rows:>8} rows   (inputs: {deps})")
    finally:
        con.close()


if __name__ == "__main__":
    run(sys.argv[1:] or None)
