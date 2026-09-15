"""mart_provider_volume: per-provider Medicare volume + spend ("highest-volume").

One row per PC provider in MUP; carries all three ranking metrics (services, beneficiaries,
medical_medicare_paid -- drug excluded as pass-through).
Run: uv run python -m pipeline.marts.mart_provider_volume
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("stg_mup_provider", "dim_provider")
OUTPUT = "mart_provider_volume"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "provider_name": "VARCHAR",
    "provider_category": "VARCHAR",
    "taxonomy_label": "VARCHAR",
    "city": "VARCHAR",
    "total_services": "BIGINT",
    "total_beneficiaries": "BIGINT",
    "total_medicare_paid": "DOUBLE",
    "medical_medicare_paid": "DOUBLE",
    "drug_medicare_paid": "DOUBLE",
}
REBUILD_IN_TEST = True  # pure SQL over committed tables

_SQL = """
CREATE OR REPLACE TABLE mart_provider_volume AS
SELECT
    d.npi, d.provider_name, d.provider_category, d.taxonomy_label, d.city,
    TRY_CAST(m.tot_srvcs AS BIGINT) AS total_services,
    TRY_CAST(m.tot_benes AS BIGINT) AS total_beneficiaries,
    TRY_CAST(m.tot_mdcr_pymt_amt AS DOUBLE) AS total_medicare_paid,
    TRY_CAST(m.med_mdcr_pymt_amt AS DOUBLE) AS medical_medicare_paid,
    TRY_CAST(m.drug_mdcr_pymt_amt AS DOUBLE) AS drug_medicare_paid
FROM stg_mup_provider m
JOIN dim_provider d USING (npi)
WHERE d.is_primary_care
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    for metric in ("total_services", "total_beneficiaries", "medical_medicare_paid"):
        print(f"\nTop 3 by {metric}:")
        print(
            con.execute(
                f"SELECT provider_name, provider_category, {metric} FROM mart_provider_volume "
                f"ORDER BY {metric} DESC NULLS LAST LIMIT 3"
            )
            .fetchdf()
            .to_string(index=False)
        )
    con.close()


if __name__ == "__main__":
    main()
