"""mart_provider_spending: primary-care Medicare spending by provider type.

One row per provider category, over PC providers who billed Medicare. Keeps the drug/medical split
(drug is pass-through); suppressed sub-amounts -> NULL (a labeled lower bound). ~121 MUP-DE NPIs
lack an NPPES DE address and drop from the join (tracked by tests).
Run: uv run python -m pipeline.marts.mart_provider_spending
"""

from __future__ import annotations

from duckdb import DuckDBPyConnection

from pipeline.asset import SqlAsset

_SQL = """
CREATE OR REPLACE TABLE mart_provider_spending AS
SELECT
    d.provider_category,
    count(*) AS provider_count,
    sum(TRY_CAST(m.tot_srvcs AS BIGINT))::BIGINT AS total_services,
    sum(TRY_CAST(m.tot_mdcr_pymt_amt AS DOUBLE)) AS total_medicare_paid,
    sum(TRY_CAST(m.tot_mdcr_alowd_amt AS DOUBLE)) AS total_medicare_allowed,
    sum(TRY_CAST(m.med_mdcr_pymt_amt AS DOUBLE)) AS medical_paid,
    sum(TRY_CAST(m.drug_mdcr_pymt_amt AS DOUBLE)) AS drug_paid,
    round(100 * sum(TRY_CAST(m.tot_mdcr_pymt_amt AS DOUBLE))
          / sum(sum(TRY_CAST(m.tot_mdcr_pymt_amt AS DOUBLE))) OVER (), 1) AS pct_of_paid
FROM stg_mup_provider m
JOIN dim_provider d USING (npi)
WHERE d.is_primary_care
GROUP BY 1
ORDER BY total_medicare_paid DESC
"""


ASSET = SqlAsset(
    name="mart_provider_spending",
    output="mart_provider_spending",
    inputs=("stg_mup_provider", "dim_provider"),
    output_columns={
        "provider_category": "VARCHAR",
        "provider_count": "BIGINT",
        "total_services": "BIGINT",
        "total_medicare_paid": "DOUBLE",
        "total_medicare_allowed": "DOUBLE",
        "medical_paid": "DOUBLE",
        "drug_paid": "DOUBLE",
        "pct_of_paid": "DOUBLE",
    },
    rebuild_in_test=True,  # pure SQL over committed tables
    sql=_SQL,
)


def _summary(con: DuckDBPyConnection, _) -> None:
    print(con.execute("SELECT * FROM mart_provider_spending").fetchdf().to_string(index=False))


def main() -> None:
    ASSET.run(_summary)


if __name__ == "__main__":
    main()
