"""Ingest MUP by-Provider-and-Service -> stg_mup_service: per-NPI x HCPCS billing detail.

Feeds Q2/Q5. Dollars are per-service averages: service total = avg_mdcr_pymt_amt * tot_srvcs.
Amounts kept as text (parsed downstream). Run: uv run python -m pipeline.ingest.mup_service
"""

from __future__ import annotations

from pipeline.asset import StageAsset
from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select
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

ASSET = StageAsset(
    name="mup_service",
    output="stg_mup_service",
    inputs=(),
    output_columns={
        "npi": "VARCHAR",
        "state": "VARCHAR",
        "hcpcs_cd": "VARCHAR",
        "tot_srvcs": "VARCHAR",
        "avg_mdcr_pymt_amt": "VARCHAR",
    },
    rebuild_in_test=False,  # reads the ~3.3 GB raw MUP file (not in CI)
    source=MUP_SERVICE,
    select=build_select(_COLUMNS),
)


def main() -> None:
    ASSET.run(lambda con, r: print(f"stg_mup_service: {r[0]} rows (state={STATE}) | schema {r[1]}"))


if __name__ == "__main__":
    main()
