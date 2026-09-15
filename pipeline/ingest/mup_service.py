"""Ingest MUP by-Provider-and-Service -> stg_mup_service: per-NPI x HCPCS billing detail.

Feeds Q2/Q5. Dollars are per-service averages: service total = avg_mdcr_pymt_amt * tot_srvcs.
Amounts kept as text (parsed downstream). Run: uv run python -m pipeline.ingest.mup_service
"""

from __future__ import annotations

from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select, connect, stage
from pipeline.sources import MUP_SERVICE

_COLUMNS = {
    "Rndrng_NPI": "npi",
    "Rndrng_Prvdr_State_Abrvtn": "state",
    "Rndrng_Prvdr_Type": "provider_type",
    "HCPCS_Cd": "hcpcs_cd",
    "HCPCS_Desc": "hcpcs_desc",
    "HCPCS_Drug_Ind": "hcpcs_drug_ind",
    "Place_Of_Srvc": "place_of_srvc",
    "Tot_Benes": "tot_benes",
    "Tot_Srvcs": "tot_srvcs",
    "Avg_Sbmtd_Chrg": "avg_sbmtd_chrg",
    "Avg_Mdcr_Alowd_Amt": "avg_mdcr_alowd_amt",
    "Avg_Mdcr_Pymt_Amt": "avg_mdcr_pymt_amt",
}

INPUTS: tuple[str, ...] = ()
OUTPUT = "stg_mup_service"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "state": "VARCHAR",
    "hcpcs_cd": "VARCHAR",
    "tot_srvcs": "VARCHAR",
    "avg_mdcr_pymt_amt": "VARCHAR",
}
REBUILD_IN_TEST = False  # reads the ~3.3 GB raw MUP file (not in CI)


def build(con) -> tuple[int, str]:
    return stage(con, MUP_SERVICE, STATE, build_select(_COLUMNS))


def main() -> None:
    con = connect()
    rows, schema_hash = build(con)
    print(f"stg_mup_service: {rows} rows (state={STATE}) | schema {schema_hash}")
    con.close()


if __name__ == "__main__":
    main()
