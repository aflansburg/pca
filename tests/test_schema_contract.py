"""Schema-contract test: our pipeline's output tables carry the columns/types the app depends on.

Deterministic, no raw CMS files needed. Guards against a transform dropping/renaming a
depended-on column. (Upstream CMS drift is the separate drift-watch, HISTORY 011.)

It copies the committed atlas.duckdb to a temp file, rebuilds the CI-rebuildable model assets
from the committed staging tables (so model edits are actually exercised, not read stale),
then asserts each asset's declared OUTPUT_COLUMNS are present and correctly typed.
"""

from __future__ import annotations

import shutil

import duckdb
import pytest

from pipeline.assets import ASSETS
from pipeline.sources import DB_PATH


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    assert DB_PATH.exists(), "data/db/atlas.duckdb must be committed for the contract test"
    tmp = tmp_path_factory.mktemp("db") / "atlas.duckdb"
    shutil.copy(DB_PATH, tmp)
    connection = duckdb.connect(str(tmp))
    # Rebuild the assets whose inputs are committed (reference file + staging tables),
    # so edits to those transforms are tested rather than read stale.
    for asset in ASSETS:
        if asset.rebuild_in_test:
            asset.build(connection)
    yield connection
    connection.close()


def _actual_columns(connection, table: str) -> dict[str, str]:
    return {name: typ for name, typ, *_ in connection.execute(f"DESCRIBE {table}").fetchall()}


@pytest.mark.parametrize("asset", ASSETS, ids=lambda a: a.name)
def test_output_columns_present_and_typed(con, asset):
    actual = _actual_columns(con, asset.output)
    for column, expected_type in asset.output_columns.items():
        assert column in actual, f"{asset.output} missing required column '{column}'"
        assert actual[column] == expected_type, f"{asset.output}.{column} is {actual[column]}, expected {expected_type}"
