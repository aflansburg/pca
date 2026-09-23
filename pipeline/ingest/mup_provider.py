"""Ingest MUP by-Provider -> stg_mup_provider: per-NPI Medicare totals (volume + spend).

Feeds Q2/Q3/Q5. Suppression flags (Drug_Sprsn_Ind/Med_Sprsn_Ind); drug vs medical split kept
for de-skewing. Amounts kept as text (parsed downstream).
Run: uv run python -m pipeline.ingest.mup_provider
"""

from __future__ import annotations

from pipeline.asset import StageAsset
from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select
from pipeline.sources import MUP_PROVIDER

_COLUMNS = {
    "Rndrng_NPI": "npi",
    "Rndrng_Prvdr_State_Abrvtn": "state",
    "Rndrng_Prvdr_Type": "provider_type",
    "Rndrng_Prvdr_Crdntls": "credentials",
    "Rndrng_Prvdr_Ent_Cd": "entity_code",
    "Tot_Benes": "tot_benes",
    "Tot_Srvcs": "tot_srvcs",
    "Tot_Sbmtd_Chrg": "tot_sbmtd_chrg",
    "Tot_Mdcr_Alowd_Amt": "tot_mdcr_alowd_amt",
    "Tot_Mdcr_Pymt_Amt": "tot_mdcr_pymt_amt",
    "Tot_Mdcr_Stdzd_Amt": "tot_mdcr_stdzd_amt",
    "Drug_Sprsn_Ind": "drug_sprsn_ind",
    "Drug_Tot_Srvcs": "drug_tot_srvcs",
    "Drug_Mdcr_Pymt_Amt": "drug_mdcr_pymt_amt",
    "Med_Sprsn_Ind": "med_sprsn_ind",
    "Med_Tot_Srvcs": "med_tot_srvcs",
    "Med_Mdcr_Pymt_Amt": "med_mdcr_pymt_amt",
}

ASSET = StageAsset(
    name="mup_provider",
    output="stg_mup_provider",
    inputs=(),
    output_columns={
        "npi": "VARCHAR",
        "state": "VARCHAR",
        "provider_type": "VARCHAR",
        "tot_srvcs": "VARCHAR",
        "tot_mdcr_pymt_amt": "VARCHAR",
    },
    rebuild_in_test=False,  # reads the raw MUP file (not in CI)
    source=MUP_PROVIDER,
    select=build_select(_COLUMNS),
)


def main() -> None:
    ASSET.run(lambda con, r: print(f"stg_mup_provider: {r[0]} rows (state={STATE}) | schema {r[1]}"))


if __name__ == "__main__":
    main()
