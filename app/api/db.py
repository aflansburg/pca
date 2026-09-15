"""Read-only DuckDB access for the API (never takes the write lock, so it never blocks a run)."""

from __future__ import annotations

from typing import Any

import duckdb

from pipeline.sources import DB_PATH


def get_con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


def fetch_dicts(sql: str, params: list | None = None) -> list[dict]:
    """Run a read-only query and return rows as dicts (one connection per call)."""
    con = get_con()
    try:
        rows = con.execute(sql, params or []).fetchall()
        cols = [d[0] for d in con.description]
    finally:
        con.close()
    return [dict(zip(cols, row, strict=True)) for row in rows]


def fetch_df(sql: str, params: list | None = None) -> Any:
    """Run a read-only query and return a pandas DataFrame (for chart specs)."""
    con = get_con()
    try:
        return con.execute(sql, params or []).df()
    finally:
        con.close()
