"""Build dim_location: one row per distinct practice address, geocoded via the US Census.

Grain: location_key (hashed address). Geocode is incremental (new keys only). Census "geographies"
returns lat/lon + tract + county FIPS. Unmatched addresses fall back to a ZIP-centroid
(location_source records the tier). Network asset, not rebuilt in CI.
Run: uv run python -m pipeline.model.dim_location
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

import requests

from pipeline.ingest._duckdb import connect

INPUTS = ("dim_provider", "ref_zcta_centroid")
OUTPUT = "dim_location"
OUTPUT_COLUMNS = {
    "location_key": "VARCHAR",
    "lat": "DOUBLE",
    "lon": "DOUBLE",
    "geocode_match": "BOOLEAN",
    "location_source": "VARCHAR",  # census | zcta_centroid | unresolved
    "county_fips": "VARCHAR",
    "tract_fips": "VARCHAR",
}
REBUILD_IN_TEST = False  # external network call

_ENDPOINT = "https://geocoding.geo.census.gov/geocoder/geographies/addressbatch"
_BENCHMARK = "Public_AR_Current"
_VINTAGE = "Current_Current"
_BATCH = 5000

_DDL = """
CREATE TABLE IF NOT EXISTS dim_location (
    location_key VARCHAR PRIMARY KEY,
    address VARCHAR, city VARCHAR, state VARCHAR, postal_code VARCHAR,
    geocode_match BOOLEAN, match_type VARCHAR, matched_address VARCHAR,
    lat DOUBLE, lon DOUBLE,
    state_fips VARCHAR, county_fips VARCHAR, tract_fips VARCHAR,
    location_source VARCHAR,
    geocoder VARCHAR, benchmark VARCHAR, vintage VARCHAR, geocoded_at TIMESTAMP
)
"""


def _chunks(rows, n):
    for i in range(0, len(rows), n):
        yield rows[i : i + n]


def _geocode(batch: list[tuple]) -> list[list[str]]:
    """batch: (location_key, street, city, state, zip5). Returns Census response CSV rows."""
    buf = io.StringIO()
    csv.writer(buf).writerows(batch)
    resp = requests.post(
        _ENDPOINT,
        files={"addressFile": ("addresses.csv", buf.getvalue())},
        data={"benchmark": _BENCHMARK, "vintage": _VINTAGE},
        timeout=600,
    )
    resp.raise_for_status()
    return list(csv.reader(io.StringIO(resp.text)))


def _parse(row: list[str]) -> dict:
    """Census geographies batch row -> parsed fields. Handles matched and unmatched."""
    rid = row[0]
    matched = len(row) > 2 and row[2] == "Match"
    if matched:
        lon, lat = (float(x) for x in row[5].split(","))
        state_fips, county_fips, tract = row[8], row[9], row[10]
        return {
            "location_key": rid,
            "geocode_match": True,
            "match_type": row[3],
            "matched_address": row[4],
            "lat": lat,
            "lon": lon,
            "state_fips": state_fips,
            "county_fips": state_fips + county_fips,
            "tract_fips": state_fips + county_fips + tract,
            "location_source": "census",
        }
    return {
        "location_key": rid,
        "geocode_match": False,
        "match_type": row[2] if len(row) > 2 else None,
        "matched_address": None,
        "lat": None,
        "lon": None,
        "state_fips": None,
        "county_fips": None,
        "tract_fips": None,
        "location_source": None,
    }


def build(con) -> None:
    con.execute(_DDL)
    candidates = con.execute(
        """SELECT DISTINCT location_key, address, city, state, postal_code
           FROM dim_provider
           WHERE is_primary_care AND address IS NOT NULL
             AND location_key NOT IN (SELECT location_key FROM dim_location)"""
    ).fetchall()

    if candidates:
        components = {c[0]: c for c in candidates}
        now = datetime.now(tz=UTC)
        for chunk in _chunks(candidates, _BATCH):
            batch = [(c[0], c[1], c[2], c[3], (c[4] or "")[:5]) for c in chunk]
            for resp_row in _geocode(batch):
                if not resp_row:
                    continue
                p = _parse(resp_row)
                _, addr, city, state, postal = components[p["location_key"]]
                con.execute(
                    "INSERT OR REPLACE INTO dim_location VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [
                        p["location_key"],
                        addr,
                        city,
                        state,
                        postal,
                        p["geocode_match"],
                        p["match_type"],
                        p["matched_address"],
                        p["lat"],
                        p["lon"],
                        p["state_fips"],
                        p["county_fips"],
                        p["tract_fips"],
                        p["location_source"],
                        "census",
                        _BENCHMARK,
                        _VINTAGE,
                        now,
                    ],
                )

    # ZIP-centroid fallback for addresses the geocoder could not place.
    con.execute(
        """UPDATE dim_location AS dl
           SET lat = z.lat, lon = z.lon, location_source = 'zcta_centroid'
           FROM ref_zcta_centroid z
           WHERE dl.lat IS NULL AND left(coalesce(dl.postal_code, ''), 5) = z.zcta5"""
    )
    con.execute("UPDATE dim_location SET location_source = 'unresolved' WHERE lat IS NULL")


def main() -> None:
    con = connect()
    build(con)
    print("dim_location by source:")
    print(
        con.execute("SELECT location_source, count(*) n FROM dim_location GROUP BY 1 ORDER BY n DESC")
        .fetchdf()
        .to_string(index=False)
    )
    con.close()


if __name__ == "__main__":
    main()
