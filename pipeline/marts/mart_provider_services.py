"""mart_provider_services: per-provider x HCPCS billing detail ("what they bill for").

One row per PC provider x HCPCS x place-of-service. MUP dollars are averages, so
total_medicare_paid = avg_mdcr_pymt_amt * services.
Run: uv run python -m pipeline.marts.mart_provider_services
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("stg_mup_service", "dim_provider")
OUTPUT = "mart_provider_services"
OUTPUT_COLUMNS = {
    "npi": "VARCHAR",
    "hcpcs_cd": "VARCHAR",
    "hcpcs_desc": "VARCHAR",
    "hcpcs_drug_ind": "VARCHAR",
    "place_of_srvc": "VARCHAR",
    "services": "BIGINT",
    "beneficiaries": "BIGINT",
    "avg_medicare_paid": "DOUBLE",
    "total_medicare_paid": "DOUBLE",
}
REBUILD_IN_TEST = True  # pure SQL over committed tables

_SQL = """
CREATE OR REPLACE TABLE mart_provider_services AS
SELECT
    s.npi, s.hcpcs_cd, s.hcpcs_desc, s.hcpcs_drug_ind, s.place_of_srvc,
    TRY_CAST(s.tot_srvcs AS BIGINT) AS services,
    TRY_CAST(s.tot_benes AS BIGINT) AS beneficiaries,
    TRY_CAST(s.avg_mdcr_pymt_amt AS DOUBLE) AS avg_medicare_paid,
    round(TRY_CAST(s.avg_mdcr_pymt_amt AS DOUBLE) * TRY_CAST(s.tot_srvcs AS BIGINT), 2)
        AS total_medicare_paid
FROM stg_mup_service s
JOIN dim_provider d USING (npi)
WHERE d.is_primary_care
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    print("A provider's top 5 services by derived total paid:")
    print(
        con.execute(
            "SELECT npi, hcpcs_cd, hcpcs_desc[:40] AS desc, services, total_medicare_paid "
            "FROM mart_provider_services "
            "WHERE npi = (SELECT npi FROM mart_provider_services GROUP BY npi "
            "             ORDER BY sum(total_medicare_paid) DESC LIMIT 1) "
            "ORDER BY total_medicare_paid DESC LIMIT 5"
        )
        .fetchdf()
        .to_string(index=False)
    )
    con.close()


if __name__ == "__main__":
    main()
