"""Ingest DAC -> stg_dac: in-state Medicare clinicians with group (PAC ID) linkage.

Fan-out preserved (NPI x enrollment x group x location); dedupe happens downstream.
Run: uv run python -m pipeline.ingest.dac
"""

from __future__ import annotations

from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select, connect, scalar, stage
from pipeline.sources import DAC

# Keys are DKAN machine column names (differ from the bulk file's display names).
_COLUMNS = {
    "npi": "npi",
    "ind_pac_id": "ind_pac_id",
    "ind_enrl_id": "ind_enrl_id",
    "gndr": "gender",
    "cred": "cred",
    "pri_spec": "pri_spec",
    "sec_spec_all": "sec_spec_all",
    "facility_name": "facility_name",
    "org_pac_id": "org_pac_id",
    "num_org_mem": "num_org_mem",
    "adr_ln_1": "address_1",
    "adr_ln_2": "address_2",
    "citytown": "city",
    "state": "state",
    "zip_code": "zip_code",
    "adrs_id": "adrs_id",
    "ind_assgn": "ind_assgn",
    "grp_assgn": "grp_assgn",
}


INPUTS: tuple[str, ...] = ()
OUTPUT = "stg_dac"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "state": "VARCHAR",
    "pri_spec": "VARCHAR",
    "org_pac_id": "VARCHAR",
    "ind_pac_id": "VARCHAR",
    "adrs_id": "VARCHAR",
}
REBUILD_IN_TEST = False  # needs the 800 MB raw file; not available in CI


def build(con) -> tuple[int, str]:
    return stage(con, DAC, STATE, build_select(_COLUMNS))


def main() -> None:
    con = connect()
    rows, schema_hash = build(con)
    uniq = scalar(con, "SELECT count(DISTINCT npi) FROM stg_dac")
    print(f"stg_dac: {rows} rows (state={STATE}) | {uniq} unique NPIs | schema {schema_hash}")
    con.close()


if __name__ == "__main__":
    main()
