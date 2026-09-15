"""dim_org: billing entities (Group PAC IDs) providers reassign benefits to.

Grain: one row per Group PAC ID (a Medicare billing entity, not a physical site).
Run: uv run python -m pipeline.model.dim_org
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("stg_reassignment",)
OUTPUT = "dim_org"
OUTPUT_COLUMNS = {
    "group_pac_id": "VARCHAR",
    "group_name": "VARCHAR",
    "group_state": "VARCHAR",
}
REBUILD_IN_TEST = True  # pure SQL over committed tables

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


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    n = con.execute("SELECT count(*) FROM dim_org").fetchone()
    print(f"dim_org: {n[0] if n else 0} groups")
    con.close()


if __name__ == "__main__":
    main()
