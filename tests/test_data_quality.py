"""Data-quality tests: the pipeline's data is correct, not just correctly shaped.

Where test_schema_contract.py checks columns/types, this checks VALUES — grain/uniqueness,
referential integrity, row-count reconciliation, value ranges, and cross-column invariants. It also
carries regression guards for "underserved is not degenerate",
organizations are excluded from clinician density, and the MUP-join drop is bounded and visible.

Deterministic and CI-safe: it copies the committed atlas.duckdb and rebuilds the rebuild_in_test
assets from committed staging (same fixture idea as the schema-contract test), so mart edits are
exercised rather than read stale. It doubles as executable documentation of the data contract.
"""

from __future__ import annotations

import shutil

import duckdb
import pytest

from pipeline.assets import ASSETS
from pipeline.sources import DB_PATH


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    assert DB_PATH.exists(), "data/db/atlas.duckdb must be committed for the data-quality tests"
    tmp = tmp_path_factory.mktemp("db") / "atlas.duckdb"
    shutil.copy(DB_PATH, tmp)
    connection = duckdb.connect(str(tmp))
    for asset in ASSETS:
        if asset.rebuild_in_test:
            asset.build(connection)
    yield connection
    connection.close()


def _scalar(con, sql: str):
    row = con.execute(sql).fetchone()
    assert row is not None
    return row[0]


# --- 1. Grain / uniqueness --------------------------------------------------------------------


def test_dim_provider_unique_on_npi(con):
    """dim_provider grain is one row per NPI."""
    rows, distinct = con.execute("SELECT count(*), count(DISTINCT npi) FROM dim_provider").fetchone()
    assert rows == distinct, f"dim_provider has duplicate NPIs ({rows} rows, {distinct} distinct)"


def test_bridge_distinct_on_npi_group(con):
    """bridge_provider_org has no duplicate (npi, group_pac_id) edges."""
    rows, distinct = con.execute(
        "SELECT count(*), count(DISTINCT (npi, group_pac_id)) FROM bridge_provider_org"
    ).fetchone()
    assert rows == distinct, "bridge_provider_org has duplicate (npi, group_pac_id) edges"


def test_spending_one_row_per_category(con):
    """mart_provider_spending is one row per provider_category."""
    rows, distinct = con.execute(
        "SELECT count(*), count(DISTINCT provider_category) FROM mart_provider_spending"
    ).fetchone()
    assert rows == distinct


def test_volume_and_peer_one_row_per_npi(con):
    """mart_provider_volume and mart_provider_peer_comparison are one row per NPI."""
    for table in ("mart_provider_volume", "mart_provider_peer_comparison"):
        rows, distinct = con.execute(f"SELECT count(*), count(DISTINCT npi) FROM {table}").fetchone()
        assert rows == distinct, f"{table} has duplicate NPIs"


# --- 2. Referential integrity -----------------------------------------------------------------


@pytest.mark.parametrize(
    "table",
    [
        "mart_provider_volume",
        "mart_provider_services",
        "mart_provider_peer_comparison",
        "mart_provider_locations",
        "bridge_provider_org",
    ],
)
def test_every_mart_npi_exists_in_dim_provider(con, table):
    """No mart references an NPI absent from dim_provider."""
    orphans = _scalar(
        con,
        f"SELECT count(*) FROM (SELECT DISTINCT npi FROM {table}) t WHERE t.npi NOT IN (SELECT npi FROM dim_provider)",
    )
    assert orphans == 0, f"{table} has {orphans} NPIs not in dim_provider"


def test_bridge_members_are_primary_care(con):
    """Every provider in a practice-group bridge edge is primary care."""
    non_pc = _scalar(
        con,
        "SELECT count(*) FROM bridge_provider_org b JOIN dim_provider d USING (npi) WHERE NOT d.is_primary_care",
    )
    assert non_pc == 0


def test_tract_marts_reference_known_geography(con):
    """Every mart_tract_access tract has geometry; every county has a population row."""
    bad_tracts = _scalar(
        con,
        "SELECT count(*) FROM mart_tract_access WHERE tract_fips NOT IN (SELECT tract_fips FROM ref_tract_geom)",
    )
    bad_counties = _scalar(
        con,
        "SELECT count(*) FROM mart_tract_access "
        "WHERE county_fips NOT IN (SELECT county_fips FROM ref_county_population)",
    )
    assert bad_tracts == 0 and bad_counties == 0


# --- 3. Reconciliation (exact counts) ---------------------------------------------------------


def test_dim_provider_reconciles_to_nppes(con):
    """dim_provider carries exactly the staged NPPES NPIs."""
    assert _scalar(con, "SELECT count(*) FROM dim_provider") == _scalar(con, "SELECT count(*) FROM stg_nppes")


def test_primary_care_count_and_split(con):
    """Primary-care population and its category split match the documented figures"""
    assert _scalar(con, "SELECT count(*) FROM dim_provider WHERE is_primary_care") == 4524
    split = dict(
        con.execute("SELECT provider_category, count(*) FROM dim_provider WHERE is_primary_care GROUP BY 1").fetchall()
    )
    assert split == {"Physician": 2023, "NP": 1646, "PA": 810, "CNS": 45}


def test_geography_row_counts(con):
    """DE has 259 tracts and 3 counties across the location centric marts."""
    assert _scalar(con, "SELECT count(*) FROM mart_tract_access") == 259
    assert _scalar(con, "SELECT count(*) FROM mart_county_access") == 3
    assert _scalar(con, "SELECT count(*) FROM mart_county_geo") == 3


# --- 4. Value ranges --------------------------------------------------------------------------


def test_imu_score_in_range(con):
    """IMU scores are within HRSA's 0-100 index range."""
    bad = _scalar(
        con,
        "SELECT count(*) FROM mart_tract_access WHERE imu_score IS NOT NULL AND (imu_score < 0 OR imu_score > 100)",
    )
    assert bad == 0


def test_percentiles_in_range(con):
    """Peer percentile ranks are 0-100."""
    bad = _scalar(
        con,
        "SELECT count(*) FROM mart_provider_peer_comparison WHERE "
        "(pct_services IS NOT NULL AND (pct_services < 0 OR pct_services > 100)) OR "
        "(pct_beneficiaries IS NOT NULL AND (pct_beneficiaries < 0 OR pct_beneficiaries > 100)) OR "
        "(pct_medical_paid IS NOT NULL AND (pct_medical_paid < 0 OR pct_medical_paid > 100))",
    )
    assert bad == 0


def test_spending_non_negative(con):
    """Spending totals are non-negative."""
    bad = _scalar(
        con,
        "SELECT count(*) FROM mart_provider_spending WHERE total_services < 0 OR coalesce(total_medicare_paid, 0) < 0",
    )
    assert bad == 0


def test_county_population_and_rate_sane(con):
    """County population is positive and per-capita rate is non-negative."""
    bad = _scalar(
        con,
        "SELECT count(*) FROM mart_county_access WHERE population <= 0 OR pc_per_10k < 0",
    )
    assert bad == 0


# --- 5. Cross-column invariants ---------------------------------------------------------------


def test_county_category_counts_bounded(con):
    """physician_count + app_provider_count never exceeds pc_provider_count."""
    bad = _scalar(
        con,
        "SELECT count(*) FROM mart_county_access WHERE physician_count + app_provider_count > pc_provider_count",
    )
    assert bad == 0


def test_provider_category_domain(con):
    """provider_category is drawn from the fixed vocabulary."""
    bad = _scalar(
        con,
        "SELECT count(*) FROM dim_provider WHERE provider_category NOT IN ('Physician', 'NP', 'PA', 'CNS', 'Other')",
    )
    assert bad == 0


def test_medical_plus_drug_within_total(con):
    """medical_paid + drug_paid <= total_medicare_paid (suppressed sub-amounts are a lower bound)."""
    bad = _scalar(
        con,
        "SELECT count(*) FROM mart_provider_spending "
        "WHERE coalesce(medical_paid, 0) + coalesce(drug_paid, 0) > total_medicare_paid + 0.5",
    )
    assert bad == 0


def test_underserved_not_degenerate(con):
    """#3: is_underserved discriminates -- it is neither all-false nor all-true across tracts."""
    total = _scalar(con, "SELECT count(*) FROM mart_tract_access")
    underserved = _scalar(con, "SELECT count(*) FROM mart_tract_access WHERE is_underserved")
    assert 0 < underserved < total, (
        f"is_underserved is degenerate ({underserved}/{total}); whole-county fan-out likely over-flagging again"
    )


def test_new_castle_not_blanket_underserved(con):
    """#3: New Castle (no Single-County MUA) has both underserved and served tracts."""
    underserved, served = con.execute(
        "SELECT count(*) FILTER (WHERE is_underserved), count(*) FILTER (WHERE NOT is_underserved) "
        "FROM mart_tract_access WHERE county_fips = '10003'"
    ).fetchone()
    assert underserved > 0 and served > 0, "New Castle should be partially, not wholly, underserved"


def test_no_organizations_in_clinician_density(con):
    """#4: county provider counts are individual clinicians only (org NPIs excluded)."""
    mart_total = _scalar(con, "SELECT sum(pc_provider_count) FROM mart_county_access")
    clinicians = _scalar(
        con,
        "SELECT count(*) FROM dim_provider p JOIN dim_location l USING (location_key) "
        "WHERE p.is_primary_care AND NOT p.is_organization AND l.county_fips IS NOT NULL",
    )
    assert mart_total == clinicians, (
        f"county density {mart_total} != non-org clinicians {clinicians}; organizations are leaking into the counts"
    )


def test_mup_join_drop_is_bounded_and_visible(con):
    """#6: some MUP-DE NPIs are dropped by the dim_provider join (out-of-state NPPES address).

    This makes the drop explicit rather than silent; a large jump signals a join/scoping problem.
    """
    dropped = _scalar(
        con,
        "SELECT count(*) FROM (SELECT DISTINCT npi FROM stg_mup_provider) m "
        "WHERE m.npi NOT IN (SELECT npi FROM dim_provider)",
    )
    assert 0 < dropped < 200, f"unexpected MUP-join drop count: {dropped}"
