"""mart_provider_locations: primary-care provider map points + underserved flags.

One row per mappable PC provider. in_mua_tract flags a tract-level MUA; county HPSA presence is
omitted (every DE county has one, so it is a non-signal).
Run: uv run python -m pipeline.marts.mart_provider_locations
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("dim_provider", "dim_location", "stg_mua")
OUTPUT = "mart_provider_locations"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "provider_name": "VARCHAR",
    "provider_category": "VARCHAR",
    "taxonomy_label": "VARCHAR",
    "is_organization": "BOOLEAN",
    "city": "VARCHAR",
    "lat": "DOUBLE",
    "lon": "DOUBLE",
    "location_source": "VARCHAR",
    "county_fips": "VARCHAR",
    "tract_fips": "VARCHAR",
    "in_mua_tract": "BOOLEAN",
}
REBUILD_IN_TEST = True  # pure SQL over committed tables

_SQL = """
CREATE OR REPLACE TABLE mart_provider_locations AS
-- in_mua_tract: provider sits in a tract-level MUA ('Census Tract' component).
WITH mua AS (
    SELECT DISTINCT tract_fips FROM stg_mua
    WHERE status = 'Designated' AND regexp_full_match(tract_fips, '[0-9]{11}')
)
SELECT
    p.npi, p.provider_name, p.provider_category, p.taxonomy_label, p.is_organization,
    p.city, l.lat, l.lon, l.location_source, l.county_fips, l.tract_fips,
    (l.tract_fips IN (SELECT tract_fips FROM mua)) AS in_mua_tract
FROM dim_provider p
JOIN dim_location l USING (location_key)
WHERE p.is_primary_care AND l.lat IS NOT NULL
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    print(
        con.execute(
            "SELECT location_source, count(*) n, count(*) FILTER(WHERE in_mua_tract) in_mua "
            "FROM mart_provider_locations GROUP BY 1 ORDER BY n DESC"
        )
        .fetchdf()
        .to_string(index=False)
    )
    con.close()


if __name__ == "__main__":
    main()
