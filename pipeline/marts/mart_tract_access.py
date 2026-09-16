"""mart_tract_access: "which areas are truly underserved", at census-tract grain.

One row per DE tract. Underserved = a tract-level 'Census Tract' MUA OR a whole-county 'Single
County' MUA (Sussex, Kent). New Castle's 'County Subdivision' MUAs are not tract-placed (documented
limitation). imu_score = worst applicable IMU (lower = worse); provider counts are census-matched only.
Run: uv run python -m pipeline.marts.mart_tract_access
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("ref_tract_geom", "ref_county_population", "stg_mua", "dim_provider", "dim_location")
OUTPUT = "mart_tract_access"
OUTPUT_COLUMNS = {
    "tract_fips": "VARCHAR",
    "county_fips": "VARCHAR",
    "county_name": "VARCHAR",
    "is_mua": "BOOLEAN",
    "is_mua_tract": "BOOLEAN",
    "imu_score": "DOUBLE",
    "pc_provider_count": "BIGINT",
    "is_underserved": "BOOLEAN",
}
REBUILD_IN_TEST = True  # pure SQL over committed reference + staging tables

_SQL = """
CREATE OR REPLACE TABLE mart_tract_access AS
WITH tract_mua AS (
    -- Tract-specific MUAs (valid 11-digit census tract).
    SELECT tract_fips, min(TRY_CAST(imu_score AS DOUBLE)) AS imu
    FROM stg_mua
    WHERE status = 'Designated' AND regexp_full_match(tract_fips, '[0-9]{11}')
    GROUP BY 1
),
county_mua AS (
    -- Only 'Single County' MUAs (Sussex, Kent) cover the whole county. 'County Subdivision'
    -- components (Middletown-Odessa) are not tract-placed -- a documented limitation.
    SELECT county_fips, min(TRY_CAST(imu_score AS DOUBLE)) AS imu
    FROM stg_mua
    WHERE status = 'Designated' AND comp_type = 'Single County'
    GROUP BY 1
),
prov AS (
    -- Individual clinicians only: org NPIs are practices, not people (they still map as points).
    SELECT l.tract_fips, count(*) AS pc_provider_count
    FROM dim_provider p JOIN dim_location l USING (location_key)
    WHERE p.is_primary_care AND NOT p.is_organization AND l.tract_fips IS NOT NULL
    GROUP BY 1
)
SELECT
    g.tract_fips,
    substr(g.tract_fips, 1, 5) AS county_fips,
    cp.county_name,
    (tm.tract_fips IS NOT NULL OR cm.county_fips IS NOT NULL) AS is_mua,
    (tm.tract_fips IS NOT NULL) AS is_mua_tract,
    least(tm.imu, cm.imu) AS imu_score,  -- worst applicable IMU (least ignores NULLs in DuckDB)
    coalesce(prov.pc_provider_count, 0) AS pc_provider_count,
    (tm.tract_fips IS NOT NULL OR cm.county_fips IS NOT NULL) AS is_underserved
FROM ref_tract_geom g
LEFT JOIN tract_mua tm USING (tract_fips)
LEFT JOIN county_mua cm ON cm.county_fips = substr(g.tract_fips, 1, 5)
LEFT JOIN prov USING (tract_fips)
LEFT JOIN ref_county_population cp ON cp.county_fips = substr(g.tract_fips, 1, 5)
ORDER BY is_underserved DESC, imu_score ASC NULLS LAST, pc_provider_count ASC
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    print(
        con.execute(
            "SELECT tract_fips, county_name, is_mua, imu_score, pc_provider_count "
            "FROM mart_tract_access WHERE is_underserved ORDER BY imu_score LIMIT 10"
        )
        .fetchdf()
        .to_string(index=False)
    )
    con.close()


if __name__ == "__main__":
    main()
