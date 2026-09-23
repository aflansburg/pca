"""Ingest HRSA Primary Care HPSA -> stg_hpsa: in-state shortage-area designations.

All statuses (active filter applies downstream); one designation fans across component rows.
Run: uv run python -m pipeline.ingest.hpsa
"""

from __future__ import annotations

from pipeline.asset import StageAsset
from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select
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

ASSET = StageAsset(
    name="hpsa",
    output="stg_hpsa",
    inputs=(),
    output_columns={
        "hpsa_id": "VARCHAR",
        "state_abbr": "VARCHAR",
        "hpsa_status": "VARCHAR",
        "designation_type": "VARCHAR",
        "hpsa_score": "VARCHAR",
        "county_fips": "VARCHAR",
    },
    rebuild_in_test=False,  # reads the raw HRSA file (not in CI)
    source=HPSA,
    select=build_select(_COLUMNS),
)


def main() -> None:
    ASSET.run(lambda con, r: print(f"stg_hpsa: {r[0]} rows (state={STATE}) | schema {r[1]}"))


if __name__ == "__main__":
    main()
