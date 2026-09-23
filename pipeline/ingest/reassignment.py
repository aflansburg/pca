"""Ingest Revalidation Reassignment -> stg_reassignment: individual -> billing-group links.

Many individual NPIs sharing a Group PAC ID bill together. State-scoped by Individual State Code.
Run: uv run python -m pipeline.ingest.reassignment
"""

from __future__ import annotations

from pipeline.asset import StageAsset
from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select
from pipeline.sources import REASSIGNMENT

_COLUMNS = {
    "Individual NPI": "npi",
    "Individual PAC ID": "individual_pac_id",
    "Group PAC ID": "group_pac_id",
    "Group Legal Business Name": "group_name",
    "Group State Code": "group_state",
    "Individual State Code": "individual_state",
    "Individual Specialty Description": "individual_specialty",
    "Individual First Name": "first_name",
    "Individual Last Name": "last_name",
}

ASSET = StageAsset(
    name="reassignment",
    output="stg_reassignment",
    inputs=(),
    output_columns={
        "npi": "VARCHAR",
        "individual_state": "VARCHAR",
        "group_pac_id": "VARCHAR",
        "group_name": "VARCHAR",
    },
    rebuild_in_test=False,  # reads the raw reassignment file (not in CI)
    source=REASSIGNMENT,
    select=build_select(_COLUMNS),
)


def main() -> None:
    ASSET.run(lambda con, r: print(f"stg_reassignment: {r[0]} rows (state={STATE}) | schema {r[1]}"))


if __name__ == "__main__":
    main()
