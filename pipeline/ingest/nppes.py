"""Ingest NPPES -> stg_nppes: all in-state providers (identity, location, taxonomy).

State-scoped; the primary-care scope applies downstream, so re-scoping never re-ingests.
Run: uv run python -m pipeline.ingest.nppes
"""

from __future__ import annotations

from pipeline.asset import StageAsset
from pipeline.config import STATE
from pipeline.sources import NPPES

_IDENT = {
    "NPI": "npi",
    "Entity Type Code": "entity_type_code",
    "Provider Organization Name (Legal Business Name)": "org_name",
    "Provider Last Name (Legal Name)": "last_name",
    "Provider First Name": "first_name",
    "Provider First Line Business Practice Location Address": "address",
    "Provider Business Practice Location Address City Name": "city",
    "Provider Business Practice Location Address State Name": "state",
    "Provider Business Practice Location Address Postal Code": "postal_code",
    "NPI Deactivation Date": "npi_deactivation_date",
}


def _build_select() -> str:
    parts = [f'"{src}" AS {dst}' for src, dst in _IDENT.items()]
    # Keep all 15 taxonomy slots raw, for auditability.
    for i in range(1, 16):
        parts.append(f'"Healthcare Provider Taxonomy Code_{i}" AS taxonomy_{i}')
        parts.append(f'"Healthcare Provider Primary Taxonomy Switch_{i}" AS taxonomy_switch_{i}')
    # Primary taxonomy = the first slot whose switch is 'Y'.
    case = " ".join(
        f'WHEN "Healthcare Provider Primary Taxonomy Switch_{i}" = \'Y\' THEN "Healthcare Provider Taxonomy Code_{i}"'
        for i in range(1, 16)
    )
    parts.append(f"CASE {case} END AS primary_taxonomy")
    return ", ".join(parts)


ASSET = StageAsset(
    name="nppes",
    output="stg_nppes",
    inputs=(),
    output_columns={
        "npi": "VARCHAR",
        "entity_type_code": "VARCHAR",
        "state": "VARCHAR",
        "primary_taxonomy": "VARCHAR",
    },
    rebuild_in_test=False,  # needs the 11.7 GB raw file; not available in CI
    source=NPPES,
    select=_build_select(),
)


def main() -> None:
    ASSET.run(lambda con, r: print(f"stg_nppes: {r[0]} rows (state={STATE}) | schema {r[1]}"))


if __name__ == "__main__":
    main()
