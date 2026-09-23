"""Ingest DAC -> stg_dac: in-state Medicare clinicians with group (PAC ID) linkage.

Fan-out preserved (NPI x enrollment x group x location); dedupe happens downstream.
Run: uv run python -m pipeline.ingest.dac
"""

from __future__ import annotations

from duckdb import DuckDBPyConnection

from pipeline.asset import StageAsset
from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select, scalar
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


ASSET = StageAsset(
    name="dac",
    output="stg_dac",
    inputs=(),
    output_columns={
        "npi": "VARCHAR",
        "state": "VARCHAR",
        "pri_spec": "VARCHAR",
        "org_pac_id": "VARCHAR",
        "ind_pac_id": "VARCHAR",
        "adrs_id": "VARCHAR",
    },
    rebuild_in_test=False,  # needs the 800 MB raw file; not available in CI
    source=DAC,
    select=build_select(_COLUMNS),
)


def _summary(con: DuckDBPyConnection, result) -> None:
    rows, schema_hash = result
    uniq = scalar(con, "SELECT count(DISTINCT npi) FROM stg_dac")
    print(f"stg_dac: {rows} rows (state={STATE}) | {uniq} unique NPIs | schema {schema_hash}")


def main() -> None:
    ASSET.run(_summary)


if __name__ == "__main__":
    main()
