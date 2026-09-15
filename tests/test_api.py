"""API smoke tests: the FastAPI endpoints serve the committed marts correctly.

Deterministic (against the committed atlas.duckdb), no network. Drill-down endpoints use IDs
pulled dynamically from list endpoints, so nothing is hardcoded.

Count assertions here are pinned to the committed DE dataset; tests/test_data_quality.py carries
the full row-count reconciliation and the reasoning behind those numbers.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_providers_geojson():
    data = client.get("/api/providers").json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 4000
    feature = data["features"][0]
    assert feature["geometry"]["type"] == "Point"
    assert len(feature["geometry"]["coordinates"]) == 2
    assert "provider_category" in feature["properties"]


def test_counties():
    data = client.get("/api/counties").json()
    assert len(data) == 3
    assert {"county_fips", "pc_provider_count", "pc_per_10k", "correctional_hpsa_count"} <= set(data[0])


def test_tracts_ranked():
    data = client.get("/api/tracts").json()
    assert len(data) == 259
    underserved = [t for t in data if t["is_underserved"]]
    assert underserved, "expected some underserved tracts"
    assert data[0]["is_underserved"]  # most-underserved first
    imus = [t["imu_score"] for t in underserved]
    assert imus == sorted(imus)  # ascending IMU = worst first


def test_tracts_geojson():
    data = client.get("/api/tracts/geojson").json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 259
    feature = data["features"][0]
    assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert {"tract_fips", "is_underserved", "imu_score"} <= set(feature["properties"])


def test_counties_geojson():
    data = client.get("/api/counties/geojson").json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 3
    feature = data["features"][0]
    assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert {"county_name", "pc_per_10k", "worst_imu"} <= set(feature["properties"])


def test_spending():
    data = client.get("/api/spending").json()
    assert len(data) == 4
    assert {"provider_category", "medical_paid", "drug_paid", "pct_of_paid"} <= set(data[0])


def test_volume_and_services():
    for metric in ("total_services", "total_beneficiaries", "medical_medicare_paid"):
        rows = client.get(f"/api/volume?metric={metric}&limit=5").json()
        assert rows and "npi" in rows[0]
    assert client.get("/api/volume?metric=bogus").status_code == 400
    npi = client.get("/api/volume?metric=total_services&limit=1").json()[0]["npi"]
    services = client.get(f"/api/providers/{npi}/services").json()
    assert services and {"hcpcs_cd", "services", "total_medicare_paid"} <= set(services[0])


def test_groups_and_members():
    groups = client.get("/api/groups").json()
    assert groups and groups[0]["pc_member_count"] >= 2
    gid = groups[0]["group_pac_id"]
    members = client.get(f"/api/groups/{gid}/members").json()
    assert members and "provider_name" in members[0]


def test_search_and_peers():
    npi = client.get("/api/volume?metric=total_services&limit=1").json()[0]["npi"]
    peer = client.get(f"/api/providers/{npi}/peers").json()
    assert "peer_group_size" in peer and "pct_services" in peer
    assert client.get("/api/providers/00000000/peers").status_code == 404
    hits = client.get("/api/providers/search?q=care&limit=3").json()
    assert isinstance(hits, list)


def test_chart_specs():
    spending = client.get("/api/charts/spending").json()
    assert spending["mark"] and "encoding" in spending
    npi = client.get("/api/volume?metric=total_services&limit=1").json()[0]["npi"]
    peers = client.get(f"/api/charts/peers?npi={npi}").json()
    assert "encoding" in peers
