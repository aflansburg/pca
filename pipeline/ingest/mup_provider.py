"""Ingest MUP by-Provider -> stg_mup_provider: per-NPI Medicare totals (volume + spend).

Feeds Q2/Q3/Q5. Suppression flags (Drug_Sprsn_Ind/Med_Sprsn_Ind); drug vs medical split kept
for de-skewing. Amounts kept as text (parsed downstream).
Run: uv run python -m pipeline.ingest.mup_provider
"""

from __future__ import annotations

from pipeline.config import STATE
from pipeline.ingest._duckdb import build_select, connect, stage
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

INPUTS: tuple[str, ...] = ()
OUTPUT = "stg_mup_provider"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "state": "VARCHAR",
    "provider_type": "VARCHAR",
    "tot_srvcs": "VARCHAR",
    "tot_mdcr_pymt_amt": "VARCHAR",
}
REBUILD_IN_TEST = False  # reads the raw MUP file (not in CI)


def build(con) -> tuple[int, str]:
    return stage(con, MUP_PROVIDER, STATE, build_select(_COLUMNS))


def main() -> None:
    con = connect()
    rows, schema_hash = build(con)
    print(f"stg_mup_provider: {rows} rows (state={STATE}) | schema {schema_hash}")
    con.close()


if __name__ == "__main__":
    main()
