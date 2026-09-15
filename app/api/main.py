"""FastAPI app: serves the marts as JSON / GeoJSON / Vega-Lite specs, plus the built SPA.

Endpoints select from the marts and shape output; no SQL logic here.
Run (API only): uv run uvicorn app.api.main:app --port 8000
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.api.charts import router as charts_router
from app.api.db import fetch_dicts as _query

app = FastAPI(title="Primary Care Atlas")

_VOLUME_METRICS = {"total_services", "total_beneficiaries", "medical_medicare_paid"}


def _feature_collection(rows: list[dict], geometry: Callable[[dict], dict]) -> dict:
    """Wrap query rows as a GeoJSON FeatureCollection. `geometry(rec)` returns the feature geometry
    and pops its geometry fields from rec, leaving the remaining columns as properties."""
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": geometry(rec), "properties": rec} for rec in rows],
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# --- locations + underserved

_PROVIDER_COLS = (
    "npi",
    "provider_name",
    "provider_category",
    "taxonomy_label",
    "is_organization",
    "city",
    "lat",
    "lon",
    "location_source",
    "in_mua_tract",
)


@app.get("/api/providers")
def providers() -> dict:
    """GeoJSON FeatureCollection of mappable primary-care providers."""
    rows = _query(f"SELECT {', '.join(_PROVIDER_COLS)} FROM mart_provider_locations")
    return _feature_collection(rows, lambda r: {"type": "Point", "coordinates": [r.pop("lon"), r.pop("lat")]})


@app.get("/api/counties")
def counties() -> list[dict]:
    return _query("SELECT * FROM mart_county_access ORDER BY pc_per_10k")


@app.get("/api/tracts")
def tracts() -> list[dict]:
    """DE census tracts, ranked most-underserved first (MUA, then worst IMU, then fewest providers)."""
    return _query(
        "SELECT * FROM mart_tract_access ORDER BY is_underserved DESC, imu_score ASC NULLS LAST, pc_provider_count ASC"
    )


@app.get("/api/tracts/geojson")
def tracts_geojson() -> dict:
    """GeoJSON FeatureCollection of DE tracts for the underserved choropleth."""
    rows = _query(
        "SELECT tract_fips, county_name, is_underserved, is_mua, imu_score, pc_provider_count, "
        "geometry_json FROM mart_tract_geo"
    )
    return _feature_collection(rows, lambda r: json.loads(r.pop("geometry_json")))


@app.get("/api/counties/geojson")
def counties_geojson() -> dict:
    """GeoJSON FeatureCollection of DE counties (dissolved), for the county overlay."""
    rows = _query(
        "SELECT county_fips, county_name, pc_per_10k, worst_imu, is_underserved, geometry_json FROM mart_county_geo"
    )
    return _feature_collection(rows, lambda r: json.loads(r.pop("geometry_json")))


# --- spending by provider type


@app.get("/api/spending")
def spending() -> list[dict]:
    return _query("SELECT * FROM mart_provider_spending ORDER BY total_medicare_paid DESC")


# --- highest-volume providers + what they bill


@app.get("/api/volume")
def volume(metric: str = "medical_medicare_paid", limit: int = 50) -> list[dict]:
    if metric not in _VOLUME_METRICS:
        raise HTTPException(status_code=400, detail=f"metric must be one of {sorted(_VOLUME_METRICS)}")
    limit = max(1, min(limit, 500))
    return _query(
        f"SELECT * FROM mart_provider_volume ORDER BY {metric} DESC NULLS LAST LIMIT ?",
        [limit],
    )


@app.get("/api/providers/{npi}/services")
def provider_services(npi: str, limit: int = 25) -> list[dict]:
    limit = max(1, min(limit, 100))
    return _query(
        "SELECT hcpcs_cd, hcpcs_desc, hcpcs_drug_ind, place_of_srvc, services, beneficiaries, "
        "avg_medicare_paid, total_medicare_paid FROM mart_provider_services "
        "WHERE npi = ? ORDER BY total_medicare_paid DESC NULLS LAST LIMIT ?",
        [npi, limit],
    )


# --- shared practice / billing entity


@app.get("/api/groups")
def groups() -> list[dict]:
    return _query("SELECT * FROM mart_practice_groups")


@app.get("/api/groups/{group_pac_id}/members")
def group_members(group_pac_id: str) -> list[dict]:
    return _query(
        "SELECT d.npi, d.provider_name, d.provider_category, d.taxonomy_label, d.city "
        "FROM bridge_provider_org b JOIN dim_provider d ON b.npi = d.npi "
        "WHERE b.group_pac_id = ? ORDER BY d.provider_category, d.provider_name",
        [group_pac_id],
    )


# --- peer comparison


@app.get("/api/providers/search")
def provider_search(q: str, limit: int = 20) -> list[dict]:
    # Search the billed population only, so every result has a /peers row (no 404 on select).
    limit = max(1, min(limit, 50))
    return _query(
        "SELECT npi, provider_name, provider_category, taxonomy_label, city "
        "FROM mart_provider_peer_comparison "
        "WHERE provider_name ILIKE ? ORDER BY provider_name LIMIT ?",
        ["%" + q + "%", limit],
    )


@app.get("/api/providers/{npi}/peers")
def provider_peers(npi: str) -> dict:
    rows = _query("SELECT * FROM mart_provider_peer_comparison WHERE npi = ?", [npi])
    if not rows:
        raise HTTPException(status_code=404, detail="provider not found in peer comparison")
    return rows[0]


app.include_router(charts_router)

# Serve the built SPA (mounted only if the frontend is built).
_DIST = Path(__file__).resolve().parents[2] / "app" / "web" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="web")
