"""mart_county_geo: mart_county_access joined to county geometry, for the overlay.

Adds the county's worst IMU. Served by /api/counties/geojson.
Run: uv run python -m pipeline.marts.mart_county_geo
"""

from __future__ import annotations

from duckdb import DuckDBPyConnection

from pipeline.asset import SqlAsset

_SQL = """
CREATE OR REPLACE TABLE mart_county_geo AS
WITH imu AS (
    SELECT county_fips, min(imu_score) AS worst_imu
    FROM mart_tract_access GROUP BY 1
)
SELECT c.county_fips, c.county_name, c.pc_provider_count, c.pc_per_10k,
       imu.worst_imu,
       (imu.worst_imu IS NOT NULL) AS is_underserved,
       g.geometry_json
FROM mart_county_access c
JOIN ref_county_geom g USING (county_fips)
LEFT JOIN imu USING (county_fips)
"""


ASSET = SqlAsset(
    name="mart_county_geo",
    output="mart_county_geo",
    inputs=("mart_county_access", "mart_tract_access", "ref_county_geom"),
    output_columns={
        "county_fips": "VARCHAR",
        "county_name": "VARCHAR",
        "pc_provider_count": "BIGINT",
        "pc_per_10k": "DOUBLE",
        "worst_imu": "DOUBLE",
        "is_underserved": "BOOLEAN",
        "geometry_json": "VARCHAR",
    },
    rebuild_in_test=True,  # pure SQL over committed tables
    sql=_SQL,
)


def _summary(con: DuckDBPyConnection, _) -> None:
    print(
        con.execute("SELECT county_name, pc_per_10k, worst_imu, is_underserved FROM mart_county_geo")
        .fetchdf()
        .to_string(index=False)
    )


def main() -> None:
    ASSET.run(_summary)


if __name__ == "__main__":
    main()
