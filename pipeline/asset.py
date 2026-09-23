"""Asset types: the DAG's nodes as data.

Each pipeline step is one Asset instance. `Asset` holds the contract every step shares --
name, output table, inputs, the output-column schema, and the CI-rebuild flag -- so the
registry (`pipeline/assets.py`) and a real orchestrator read one uniform shape. A subclass
carries the build logic:

- SqlAsset   -- one SQL statement (models, marts, committed-file loaders).
- StageAsset -- ingest a CMS source into stg_<key>, state-filtered.
- FuncAsset  -- escape hatch for a custom Python build (e.g. the geocoding dim_location).

Each step module declares its instance as `ASSET`; the contract stays liftable to
Dagster @asset(deps=inputs) or Airflow with no rewrite.

Note: `pipeline/asset.py` (this file) holds the types; `pipeline/assets.py` holds the registry.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from duckdb import DuckDBPyConnection

from pipeline.config import STATE
from pipeline.ingest._duckdb import connect, stage
from pipeline.sources import Source


@dataclass(frozen=True)
class Asset:
    name: str
    output: str
    inputs: tuple[str, ...]
    output_columns: dict[str, str]
    rebuild_in_test: bool

    def build(self, con: DuckDBPyConnection) -> object:
        raise NotImplementedError(f"{type(self).__name__} must implement build()")

    def run(self, summary: Callable[[DuckDBPyConnection, Any], None] | None = None) -> None:
        """Standalone entry for one asset: connect, build, run an optional summary, always close.

        `summary` is a callback. run() owns the lifecycle and invokes it once, after build(), as
        `summary(con, result)` -- the open connection plus whatever build() returned. Each module's
        `main()` passes its own diagnostic (a lambda, or a named function for multi-line output);
        run() decides when the callback fires and what it receives.
        """
        con = connect()
        try:
            result = self.build(con)
            if summary is not None:
                summary(con, result)
        finally:
            con.close()


@dataclass(frozen=True)
class SqlAsset(Asset):
    """Built by one SQL statement. `params` binds `?` placeholders (e.g. a file path or scope list)."""

    sql: str
    params: tuple = ()

    def build(self, con: DuckDBPyConnection) -> None:
        con.execute(self.sql, list(self.params))


@dataclass(frozen=True)
class StageAsset(Asset):
    """Ingest a CMS source into stg_<key>, filtered to the configured STATE.

    build() returns (row_count, schema_hash) from stage(). `select` is the staging SELECT list.
    """

    source: Source
    select: str

    def build(self, con: DuckDBPyConnection) -> tuple[int, str]:
        return stage(con, self.source, STATE, self.select)


@dataclass(frozen=True)
class FuncAsset(Asset):
    """Escape hatch: build delegated to a module function (custom Python that SQL can't express)."""

    fn: Callable[[DuckDBPyConnection], object]

    def build(self, con: DuckDBPyConnection) -> object:
        return self.fn(con)
