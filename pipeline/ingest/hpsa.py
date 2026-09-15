"""Ingest HRSA Primary Care HPSA -> stg_hpsa: in-state shortage-area designations.

All statuses (active filter applies downstream); one designation fans across component rows.
Run: uv run python -m pipeline.ingest.hpsa
"""

from __future__ import annotations

from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select, connect, stage
from pipeline.sources import HPSA

_COLUMNS = {
    "HPSA ID": "hpsa_id",
    "HPSA Name": "hpsa_name",
    "Designation Type": "designation_type",
    "HPSA Status": "hpsa_status",
    "HPSA Score": "hpsa_score",
    "HPSA Population Type": "population_type",
    "Primary State Abbreviation": "state_abbr",
    "Common County Name": "county_name",
    "State and County Federal Information Processing Standard Code": "county_fips",
    "HPSA Estimated Underserved Population": "est_underserved_population",
    "HPSA Designation Population": "designation_population",
    "Latitude": "lat",
    "Longitude": "lon",
    "Rural Status": "rural_status",
}

INPUTS: tuple[str, ...] = ()
OUTPUT = "stg_hpsa"
OUTPUT_COLUMNS = {
    "hpsa_id": "VARCHAR",
    "state_abbr": "VARCHAR",
    "hpsa_status": "VARCHAR",
    "designation_type": "VARCHAR",
    "hpsa_score": "VARCHAR",
    "county_fips": "VARCHAR",
}
REBUILD_IN_TEST = False  # reads the raw HRSA file (not in CI)


def build(con) -> tuple[int, str]:
    return stage(con, HPSA, STATE, build_select(_COLUMNS))


def main() -> None:
    con = connect()
    rows, schema_hash = build(con)
    print(f"stg_hpsa: {rows} rows (state={STATE}) | schema {schema_hash}")
    con.close()


if __name__ == "__main__":
    main()
