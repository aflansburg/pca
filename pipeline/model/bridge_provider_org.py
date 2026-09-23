"""bridge_provider_org: many-to-many links between primary-care NPIs and billing groups.

Grain: distinct (npi, group_pac_id). The join for "who works together" (same group_pac_id).
Run: uv run python -m pipeline.model.bridge_provider_org
"""

from __future__ import annotations

from duckdb import DuckDBPyConnection

from pipeline.asset import SqlAsset

_SQL = """
CREATE OR REPLACE TABLE bridge_provider_org AS
SELECT DISTINCT r.npi, r.group_pac_id
FROM stg_reassignment r
JOIN dim_provider d ON r.npi = d.npi
WHERE d.is_primary_care AND r.group_pac_id IS NOT NULL
"""


ASSET = SqlAsset(
    name="bridge_provider_org",
    output="bridge_provider_org",
    inputs=("stg_reassignment", "dim_provider"),
    output_columns={
        "npi": "VARCHAR",
        "group_pac_id": "VARCHAR",
    },
    rebuild_in_test=True,  # pure SQL over committed tables
    sql=_SQL,
)


def _summary(con: DuckDBPyConnection, _) -> None:
    row = con.execute(
        "SELECT count(*), count(DISTINCT npi), count(DISTINCT group_pac_id) FROM bridge_provider_org"
    ).fetchone()
    if row:
        print(f"bridge_provider_org: {row[0]} links | {row[1]} providers | {row[2]} groups")


def main() -> None:
    ASSET.run(_summary)


if __name__ == "__main__":
    main()
