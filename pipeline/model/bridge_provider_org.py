"""bridge_provider_org: many-to-many links between primary-care NPIs and billing groups.

Grain: distinct (npi, group_pac_id). The join for "who works together" (same group_pac_id).
Run: uv run python -m pipeline.model.bridge_provider_org
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("stg_reassignment", "dim_provider")
OUTPUT = "bridge_provider_org"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "group_pac_id": "VARCHAR",
}
REBUILD_IN_TEST = True  # pure SQL over committed tables

_SQL = """
CREATE OR REPLACE TABLE bridge_provider_org AS
SELECT DISTINCT r.npi, r.group_pac_id
FROM stg_reassignment r
JOIN dim_provider d ON r.npi = d.npi
WHERE d.is_primary_care AND r.group_pac_id IS NOT NULL
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    row = con.execute(
        "SELECT count(*), count(DISTINCT npi), count(DISTINCT group_pac_id) FROM bridge_provider_org"
    ).fetchone()
    if row:
        print(f"bridge_provider_org: {row[0]} links | {row[1]} providers | {row[2]} groups")
    con.close()


if __name__ == "__main__":
    main()
