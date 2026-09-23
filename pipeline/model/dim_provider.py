"""Build dim_provider: one row per NPI, the provider dimension the app builds on.

Adds taxonomy label, provider_category, is_primary_care (config scope), and a
Medicare-enrolled flag (DAC). Org/practice linkage lives in bridge_provider_org.py.
Run: uv run python -m pipeline.model.dim_provider
"""

from __future__ import annotations

from duckdb import DuckDBPyConnection

from pipeline.asset import SqlAsset
from pipeline.config import PRIMARY_CARE

_SQL = """
CREATE OR REPLACE TABLE dim_provider AS
WITH dac_enrolled AS (SELECT DISTINCT npi FROM stg_dac)
SELECT
    n.npi,
    n.entity_type_code,
    (n.entity_type_code = '2') AS is_organization,
    CASE WHEN n.entity_type_code = '2' THEN n.org_name
         ELSE nullif(trim(coalesce(n.first_name, '') || ' ' || coalesce(n.last_name, '')), '') END
        AS provider_name,
    n.address, n.city, n.state, n.postal_code,
    n.primary_taxonomy,
    t.classification AS taxonomy_classification,
    t.specialization AS taxonomy_specialization,
    coalesce(nullif(t.display_name, ''), t.classification) AS taxonomy_label,
    CASE
        WHEN t.classification = 'Nurse Practitioner' THEN 'NP'
        WHEN t.classification = 'Physician Assistant' THEN 'PA'
        WHEN t.classification = 'Clinical Nurse Specialist' THEN 'CNS'
        WHEN t.grouping = 'Allopathic & Osteopathic Physicians' THEN 'Physician'
        ELSE 'Other'
    END AS provider_category,
    (n.primary_taxonomy IN ?) AS is_primary_care,
    (d.npi IS NOT NULL) AS is_medicare_enrolled,
    -- Stable key for the distinct practice address; FK into dim_location.
    md5(upper(trim(coalesce(n.address, ''))) || '|' || upper(trim(coalesce(n.city, ''))) || '|'
        || upper(trim(coalesce(n.state, ''))) || '|' || left(coalesce(n.postal_code, ''), 5)) AS location_key,
    n.npi_deactivation_date
FROM stg_nppes n
LEFT JOIN ref_taxonomy t ON n.primary_taxonomy = t.code
LEFT JOIN dac_enrolled d ON n.npi = d.npi
"""


ASSET = SqlAsset(
    name="dim_provider",
    output="dim_provider",
    inputs=("stg_nppes", "stg_dac", "ref_taxonomy"),
    output_columns={
        "npi": "VARCHAR",
        "is_organization": "BOOLEAN",
        "provider_name": "VARCHAR",
        "city": "VARCHAR",
        "state": "VARCHAR",
        "postal_code": "VARCHAR",
        "primary_taxonomy": "VARCHAR",
        "taxonomy_label": "VARCHAR",
        "provider_category": "VARCHAR",
        "is_primary_care": "BOOLEAN",
        "is_medicare_enrolled": "BOOLEAN",
        "location_key": "VARCHAR",
    },
    rebuild_in_test=True,  # rebuilds from committed staging tables
    sql=_SQL,
    params=(PRIMARY_CARE["nppes_taxonomy_codes"],),
)


def _summary(con: DuckDBPyConnection, _) -> None:
    print("dim_provider built.")
    print(
        con.execute(
            "SELECT provider_category, count(*) AS n, sum(is_primary_care::int) AS primary_care "
            "FROM dim_provider GROUP BY 1 ORDER BY n DESC"
        )
        .fetchdf()
        .to_string(index=False)
    )


def main() -> None:
    ASSET.run(_summary)


if __name__ == "__main__":
    main()
