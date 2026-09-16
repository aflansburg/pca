"""Generate committed DE tract geometry from TIGER via DuckDB-spatial (a generation-only dep).

Refresh: uv run python -m pipeline.reference_gen.tract_geometry
"""

from __future__ import annotations

import json
import os
import tempfile

import duckdb
import requests

from pipeline.config import STATE_FIPS
from pipeline.sources import ROOT

SRC = f"https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_{STATE_FIPS}_tract_500k.zip"
OUT = ROOT / "data/reference/de_tract_geom_2020.json"


def main() -> None:
    resp = requests.get(SRC, timeout=120)
    resp.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(resp.content)
        zpath = tmp.name
    try:
        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial;")
        # GEOID = 11-digit tract FIPS; ST_AsGeoJSON emits a GeoJSON string.
        rows = con.execute(
            f"SELECT GEOID, ST_AsGeoJSON(geom) FROM ST_Read('/vsizip/{zpath}') ORDER BY GEOID"
        ).fetchall()
        con.close()
    finally:
        os.remove(zpath)
    records = [{"tract_fips": geoid, "geometry_json": geometry} for geoid, geometry in rows]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records))
    print(f"de_tract_geom: {len(records)} tracts -> {OUT.name}")


if __name__ == "__main__":
    main()
