"""dim_org: billing entities (Group PAC IDs) providers reassign benefits to.

Grain: one row per Group PAC ID (a Medicare billing entity, not a physical site).
Run: uv run python -m pipeline.model.dim_org
"""

from __future__ import annotations

from duckdb import DuckDBPyConnection

from pipeline.asset import SqlAsset

_SQL = """
CREATE OR REPLACE TABLE dim_org AS
WITH name_counts AS (
    -- Most frequent legal name per PAC ID; ties broken alphabetically (deterministic).
    SELECT group_pac_id, group_name
    FROM stg_reassignment
    WHERE group_pac_id IS NOT NULL AND group_name IS NOT NULL
    GROUP BY group_pac_id, group_name
    QUALIFY row_number() OVER (PARTITION BY group_pac_id ORDER BY count(*) DESC, group_name) = 1
),
states AS (
    SELECT group_pac_id, max(group_state) AS group_state
    FROM stg_reassignment WHERE group_pac_id IS NOT NULL GROUP BY group_pac_id
)
SELECT s.group_pac_id, n.group_name, s.group_state
FROM states s LEFT JOIN name_counts n USING (group_pac_id)
"""


ASSET = SqlAsset(
    name="dim_org",
    output="dim_org",
    inputs=("stg_reassignment",),
    output_columns={
        "group_pac_id": "VARCHAR",
        "group_name": "VARCHAR",
        "group_state": "VARCHAR",
    },
    rebuild_in_test=True,  # pure SQL over committed tables
    sql=_SQL,
)


def _summary(con: DuckDBPyConnection, _) -> None:
    n = con.execute("SELECT count(*) FROM dim_org").fetchone()
    print(f"dim_org: {n[0] if n else 0} groups")


def main() -> None:
    ASSET.run(_summary)


if __name__ == "__main__":
    main()
