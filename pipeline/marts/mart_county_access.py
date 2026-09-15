"""mart_county_access: access rollup at county grain (tract detail is mart_tract_access).

Per county: PC provider counts (clinicians only), providers per 10k, and HRSA signals split by what
they measure -- area/resident (HPSA-Population + MUA) vs facility (Correctional, FQHC). No binary
underserved tag: every DE county has an MUA, so the signal is the graded per-capita + counts.
Provider counts are census-matched addresses only. Run: uv run python -m pipeline.marts.mart_county_access
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect

INPUTS = ("ref_county_population", "dim_provider", "dim_location", "stg_hpsa", "stg_mua")
OUTPUT = "mart_county_access"
OUTPUT_COLUMNS = {
    "county_fips": "VARCHAR",
    "county_name": "VARCHAR",
    "population": "BIGINT",
    "pc_provider_count": "BIGINT",
    "physician_count": "BIGINT",
    "app_provider_count": "BIGINT",
    "pc_per_10k": "DOUBLE",
    "hpsa_population_count": "BIGINT",
    "correctional_hpsa_count": "BIGINT",
    "fqhc_hpsa_count": "BIGINT",
    "hpsa_population_max_score": "DOUBLE",
    "mua_tract_count": "BIGINT",
    "mua_designation_count": "BIGINT",
}
REBUILD_IN_TEST = True  # pure SQL over committed reference + staging tables

# Area/resident HPSAs = geographic + population; facility HPSAs (Correctional/FQHC) counted separately.
_IS_AREA_HPSA = "(designation_type ILIKE '%Geographic%' OR designation_type = 'HPSA Population')"

_SQL = f"""
CREATE OR REPLACE TABLE mart_county_access AS
WITH prov AS (
    -- Individual clinicians only: org NPIs would inflate per-capita (they still map as points).
    SELECT l.county_fips,
           count(*) AS pc_provider_count,
           count(*) FILTER (WHERE p.provider_category = 'Physician') AS physician_count,
           count(*) FILTER (WHERE p.provider_category IN ('NP', 'PA', 'CNS')) AS app_provider_count
    FROM dim_provider p JOIN dim_location l USING (location_key)
    WHERE p.is_primary_care AND NOT p.is_organization AND l.county_fips IS NOT NULL
    GROUP BY 1
),
hpsa AS (
    SELECT county_fips,
           count(DISTINCT hpsa_id) FILTER (WHERE {_IS_AREA_HPSA}) AS hpsa_population_count,
           count(DISTINCT hpsa_id) FILTER (WHERE designation_type = 'Correctional Facility')
               AS correctional_hpsa_count,
           count(DISTINCT hpsa_id) FILTER (WHERE designation_type ILIKE '%Federally Qualified%')
               AS fqhc_hpsa_count,
           max(TRY_CAST(hpsa_score AS DOUBLE)) FILTER (WHERE {_IS_AREA_HPSA}) AS hpsa_population_max_score
    FROM stg_hpsa
    WHERE hpsa_status = 'Designated' AND county_fips IS NOT NULL
    GROUP BY 1
),
mua AS (
    SELECT county_fips,
           count(DISTINCT tract_fips) FILTER (WHERE regexp_full_match(tract_fips, '[0-9]{{11}}'))
               AS mua_tract_count,
           count(DISTINCT mua_id) AS mua_designation_count
    FROM stg_mua
    WHERE status = 'Designated' AND county_fips IS NOT NULL
    GROUP BY 1
)
SELECT
    cp.county_fips, cp.county_name, cp.population,
    coalesce(prov.pc_provider_count, 0) AS pc_provider_count,
    coalesce(prov.physician_count, 0) AS physician_count,
    coalesce(prov.app_provider_count, 0) AS app_provider_count,
    round(coalesce(prov.pc_provider_count, 0) * 10000.0 / cp.population, 1) AS pc_per_10k,
    coalesce(h.hpsa_population_count, 0) AS hpsa_population_count,
    coalesce(h.correctional_hpsa_count, 0) AS correctional_hpsa_count,
    coalesce(h.fqhc_hpsa_count, 0) AS fqhc_hpsa_count,
    h.hpsa_population_max_score,
    coalesce(m.mua_tract_count, 0) AS mua_tract_count,
    coalesce(m.mua_designation_count, 0) AS mua_designation_count
FROM ref_county_population cp
LEFT JOIN prov USING (county_fips)
LEFT JOIN hpsa h USING (county_fips)
LEFT JOIN mua m USING (county_fips)
ORDER BY pc_per_10k ASC
"""


def build(con) -> None:
    con.execute(_SQL)


def main() -> None:
    con = connect()
    build(con)
    print(con.execute("SELECT * FROM mart_county_access").fetchdf().to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
