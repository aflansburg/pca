"""mart_practice_groups: primary-care providers grouped by shared billing entity.

One row per group (PAC ID) with >= 2 PC members; roster from bridge_provider_org.
Run: uv run python -m pipeline.marts.mart_practice_groups
"""

from __future__ import annotations

from duckdb import DuckDBPyConnection

from pipeline.asset import SqlAsset

_SQL = """
CREATE OR REPLACE TABLE mart_practice_groups AS
SELECT
    o.group_pac_id, o.group_name, o.group_state,
    count(DISTINCT b.npi) AS pc_member_count,
    count(DISTINCT CASE WHEN d.provider_category = 'Physician' THEN b.npi END) AS physician_count,
    count(DISTINCT CASE WHEN d.provider_category IN ('NP', 'PA', 'CNS') THEN b.npi END) AS app_provider_count
FROM bridge_provider_org b
JOIN dim_org o USING (group_pac_id)
JOIN dim_provider d ON b.npi = d.npi
GROUP BY 1, 2, 3
HAVING count(DISTINCT b.npi) >= 2
ORDER BY pc_member_count DESC
"""


ASSET = SqlAsset(
    name="mart_practice_groups",
    output="mart_practice_groups",
    inputs=("bridge_provider_org", "dim_org", "dim_provider"),
    output_columns={
        "group_pac_id": "VARCHAR",
        "group_name": "VARCHAR",
        "group_state": "VARCHAR",
        "pc_member_count": "BIGINT",
        "physician_count": "BIGINT",
        "app_provider_count": "BIGINT",
    },
    rebuild_in_test=True,  # pure SQL over committed tables
    sql=_SQL,
)


def _summary(con: DuckDBPyConnection, _) -> None:
    print("Largest primary-care practice groups (DE):")
    print(
        con.execute(
            "SELECT group_name, pc_member_count, physician_count, app_provider_count FROM mart_practice_groups LIMIT 8"
        )
        .fetchdf()
        .to_string(index=False)
    )


def main() -> None:
    ASSET.run(_summary)


if __name__ == "__main__":
    main()
