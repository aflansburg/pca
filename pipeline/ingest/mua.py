"""Ingest HRSA MUA/P -> stg_mua: in-state medically-underserved areas (tract grain).

Derives tract_fips to join dim_location.tract_fips.
Run: uv run python -m pipeline.ingest.mua
"""

from __future__ import annotations

from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select, connect, stage
from pipeline.sources import MUA

_COLUMNS = {
    "MUA/P ID": "mua_id",
    "MUA/P Service Area Name": "service_area",
    "Designation Type": "designation_type",
    "MUA/P Status Description": "status",
    "IMU Score": "imu_score",
    "State Abbreviation": "state_abbr",
    "State and County Federal Information Processing Standard Code": "county_fips",
    "Census Tract": "census_tract",
    "Complete County Name": "county_name",
    # comp_type = HRSA footprint: 'Single County' | 'Census Tract' | 'County Subdivision'.
    # Placed correctly downstream, not blanket-fanned to the county.
    "Medically Underserved Area/Population (MUA/P) Component Geographic Type Description": "comp_type",
    "County Subdivision Name": "county_subdivision",
}

INPUTS: tuple[str, ...] = ()
OUTPUT = "stg_mua"
OUTPUT_COLUMNS = {
    "mua_id": "VARCHAR",
    "state_abbr": "VARCHAR",
    "status": "VARCHAR",
    "imu_score": "VARCHAR",
    "county_fips": "VARCHAR",
    "census_tract": "VARCHAR",
    "tract_fips": "VARCHAR",
    "comp_type": "VARCHAR",
    "county_subdivision": "VARCHAR",
}
REBUILD_IN_TEST = False  # reads the raw HRSA file (not in CI)


def build(con) -> tuple[int, str]:
    return stage(
        con,
        MUA,
        STATE,
        build_select(
            _COLUMNS,
            # 11-digit tract FIPS = 5-digit state+county FIPS ++ 6-digit census tract.
            ['"State and County Federal Information Processing Standard Code" || "Census Tract" AS tract_fips'],
        ),
    )


def main() -> None:
    con = connect()
    rows, schema_hash = build(con)
    print(f"stg_mua: {rows} rows (state={STATE}) | schema {schema_hash}")
    con.close()


if __name__ == "__main__":
    main()
