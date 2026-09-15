"""mart_provider_peer_comparison: a provider's billing vs same-specialty peers.

Peer group = same primary_taxonomy. Percentile rank on services, beneficiaries, and medical paid
(drug excluded); low_confidence flags < 10 peers.
Run: uv run python -m pipeline.marts.mart_provider_peer_comparison
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("stg_mup_provider", "dim_provider")
OUTPUT = "mart_provider_peer_comparison"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "provider_name": "VARCHAR",
    "provider_category": "VARCHAR",
    "primary_taxonomy": "VARCHAR",
    "taxonomy_label": "VARCHAR",
    "city": "VARCHAR",
    "total_services": "BIGINT",
    "total_beneficiaries": "BIGINT",
    "medical_medicare_paid": "DOUBLE",
    "peer_group_size": "BIGINT",
    "pct_services": "DOUBLE",
    "pct_beneficiaries": "DOUBLE",
    "pct_medical_paid": "DOUBLE",
    "low_confidence": "BOOLEAN",
}
REBUILD_IN_TEST = True  # pure SQL over committed tables

_SQL = """
CREATE OR REPLACE TABLE mart_provider_peer_comparison AS
WITH base AS (
    SELECT
        d.npi, d.provider_name, d.provider_category, d.primary_taxonomy, d.taxonomy_label, d.city,
        TRY_CAST(m.tot_srvcs AS BIGINT) AS total_services,
        TRY_CAST(m.tot_benes AS BIGINT) AS total_beneficiaries,
        TRY_CAST(m.med_mdcr_pymt_amt AS DOUBLE) AS medical_medicare_paid
    FROM stg_mup_provider m
    JOIN dim_provider d USING (npi)
    WHERE d.is_primary_care
)
SELECT
    npi, provider_name, provider_category, primary_taxonomy, taxonomy_label, city,
    total_services, total_beneficiaries, medical_medicare_paid,
    count(*) OVER peer AS peer_group_size,
    round(100 * percent_rank() OVER (PARTITION BY primary_taxonomy ORDER BY total_services), 0)
        AS pct_services,
    round(100 * percent_rank() OVER (PARTITION BY primary_taxonomy ORDER BY total_beneficiaries), 0)
        AS pct_beneficiaries,
    round(100 * percent_rank() OVER (PARTITION BY primary_taxonomy ORDER BY medical_medicare_paid), 0)
        AS pct_medical_paid,
    (count(*) OVER peer < 10) AS low_confidence
FROM base
WINDOW peer AS (PARTITION BY primary_taxonomy)
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    print("Peer-group sizes (top specialties):")
    print(
        con.execute(
            "SELECT taxonomy_label, any_value(peer_group_size) AS peers, "
            "any_value(low_confidence) AS low_conf "
            "FROM mart_provider_peer_comparison GROUP BY 1 ORDER BY peers DESC LIMIT 8"
        )
        .fetchdf()
        .to_string(index=False)
    )
    con.close()


if __name__ == "__main__":
    main()
