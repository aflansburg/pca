"""mart_tract_geo: mart_tract_access joined to tract geometry, for the choropleth.

Served as a FeatureCollection by /api/tracts/geojson.
Run: uv run python -m pipeline.marts.mart_tract_geo
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("mart_tract_access", "ref_tract_geom")
OUTPUT = "mart_tract_geo"
OUTPUT_COLUMNS = {
    "tract_fips": "VARCHAR",
    "county_name": "VARCHAR",
    "is_underserved": "BOOLEAN",
    "is_mua": "BOOLEAN",
    "imu_score": "DOUBLE",
    "pc_provider_count": "BIGINT",
    "geometry_json": "VARCHAR",
}
REBUILD_IN_TEST = True  # pure SQL over committed tables

_SQL = """
CREATE OR REPLACE TABLE mart_tract_geo AS
SELECT a.tract_fips, a.county_name, a.is_underserved, a.is_mua, a.imu_score,
       a.pc_provider_count, g.geometry_json
FROM mart_tract_access a
JOIN ref_tract_geom g USING (tract_fips)
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    n = con.execute("SELECT count(*) FROM mart_tract_geo").fetchone()
    print(f"mart_tract_geo: {n[0] if n else 0} tracts")
    con.close()


if __name__ == "__main__":
    main()
