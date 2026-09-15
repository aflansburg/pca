"""Ingest Revalidation Reassignment -> stg_reassignment: individual -> billing-group links.

Many individual NPIs sharing a Group PAC ID bill together. State-scoped by Individual State Code.
Run: uv run python -m pipeline.ingest.reassignment
"""

from __future__ import annotations

from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select, connect, stage
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

INPUTS: tuple[str, ...] = ()
OUTPUT = "stg_reassignment"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "individual_state": "VARCHAR",
    "group_pac_id": "VARCHAR",
    "group_name": "VARCHAR",
}
REBUILD_IN_TEST = False  # reads the raw reassignment file (not in CI)


def build(con) -> tuple[int, str]:
    return stage(con, REASSIGNMENT, STATE, build_select(_COLUMNS))


def main() -> None:
    con = connect()
    rows, schema_hash = build(con)
    print(f"stg_reassignment: {rows} rows (state={STATE}) | schema {schema_hash}")
    con.close()


if __name__ == "__main__":
    main()
