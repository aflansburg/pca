"""Shared ingest helpers: connection, schema contract, zip streaming, provenance."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime

import duckdb
from duckdb import DuckDBPyConnection

from pipeline.sources import DB_PATH, Source


class SchemaDriftError(RuntimeError):
    """Raised when a source is missing a column the pipeline depends on."""


def connect() -> DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def scalar(con: DuckDBPyConnection, sql: str, params: list | None = None):
    """Run a query and return its single scalar value."""
    row = con.execute(sql, params or []).fetchone()
    assert row is not None, f"expected a row from: {sql}"
    return row[0]


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def build_select(columns: dict[str, str], extra: list[str] | None = None) -> str:
    """Render a staging SELECT list (`"Source Col" AS dst`), plus any extra expressions."""
    parts = [f'"{src}" AS {dst}' for src, dst in columns.items()]
    if extra:
        parts.extend(extra)
    return ", ".join(parts)


def read_header(src: Source) -> list[str]:
    """Return the CSV header columns without loading the file."""
    if src.kind == "zip":
        assert src.member is not None, "zip source requires a member"
        proc = subprocess.Popen(["unzip", "-p", str(src.path), src.member], stdout=subprocess.PIPE)
        assert proc.stdout is not None
        line = proc.stdout.readline().decode(src.encoding, errors="replace")
        proc.stdout.close()
        proc.terminate()
        proc.wait()
    else:
        with open(src.path, encoding=src.encoding) as f:
            line = f.readline()
    return next(csv.reader([line]))


def assert_schema(actual: list[str], required: tuple[str, ...]) -> None:
    missing = [c for c in required if c not in actual]
    if missing:
        raise SchemaDriftError(
            f"schema drift: required columns absent from source: {missing}. "
            f"Pinned release may have changed upstream — review before re-pinning."
        )


@contextmanager
def _fifo_from_zip(src: Source):
    """Stream a zip member through a named pipe so DuckDB reads it without full extraction."""
    assert src.member is not None, "zip source requires a member"
    d = tempfile.mkdtemp()
    fifo = os.path.join(d, "stream.csv")
    os.mkfifo(fifo)
    # The child blocks writing the FIFO until DuckDB opens it to read.
    proc = subprocess.Popen(["bash", "-c", 'unzip -p "$1" "$2" > "$3"', "_", str(src.path), src.member, fifo])
    try:
        yield fifo
    finally:
        proc.wait()
        os.remove(fifo)
        os.rmdir(d)


def stage(con: DuckDBPyConnection, src: Source, state_value: str, select_sql: str) -> tuple[int, str]:
    """CREATE OR REPLACE stg_<key> from the source, filtered to state_value. Records provenance."""
    actual = read_header(src)
    assert_schema(actual, src.required_columns)
    schema_hash = hashlib.sha256("\x1f".join(actual).encode()).hexdigest()[:16]

    if src.lenient:
        # HRSA files are ragged: null_padding tolerates them; parallel=false (it breaks the
        # parallel scan on quoted newlines). Avoid ignore_errors -- it drops rows silently.
        reader = (
            "read_csv(?, delim=',', quote='\"', header=true, all_varchar=true, "
            f"sample_size=-1, encoding='{src.encoding}', strict_mode=false, "
            "null_padding=true, parallel=false)"
        )
    else:
        # NPPES/DAC are well-formed: a parallel scan is safe here.
        reader = f"read_csv(?, all_varchar=true, header=true, sample_size=-1, encoding='{src.encoding}')"
    sql = (
        f"CREATE OR REPLACE TABLE stg_{src.key} AS "
        f"SELECT {select_sql} FROM {reader} "
        f"WHERE {_quote_ident(src.state_col)} = ?"
    )
    if src.kind == "zip":
        with _fifo_from_zip(src) as fifo:
            con.execute(sql, [fifo, state_value])
    else:
        con.execute(sql, [str(src.path), state_value])

    row_count = scalar(con, f"SELECT count(*) FROM stg_{src.key}")
    _record_manifest(con, src, schema_hash, row_count)
    return row_count, schema_hash


def _record_manifest(con: DuckDBPyConnection, src: Source, schema_hash: str, row_count: int) -> None:
    con.execute(
        """CREATE TABLE IF NOT EXISTS _manifest(
            source VARCHAR, kind VARCHAR, source_ref VARCHAR, release VARCHAR,
            fetch_ts TIMESTAMP, row_count BIGINT, schema_hash VARCHAR, run_ts TIMESTAMP)"""
    )
    fetch_ts = datetime.fromtimestamp(src.path.stat().st_mtime, tz=UTC)
    con.execute("DELETE FROM _manifest WHERE source = ?", [src.key])
    con.execute(
        "INSERT INTO _manifest VALUES (?,?,?,?,?,?,?,?)",
        [src.key, src.kind, src.path.name, src.release, fetch_ts, row_count, schema_hash, datetime.now(tz=UTC)],
    )
