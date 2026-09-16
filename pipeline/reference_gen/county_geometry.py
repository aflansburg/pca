"""Generate committed DE county geometry by dissolving the tract geometry (ST_Union_Agg).

Refresh: uv run python -m pipeline.reference_gen.county_geometry
"""

from __future__ import annotations

import json

import duckdb

from pipeline.sources import ROOT

TRACTS = ROOT / "data/reference/de_tract_geom_2020.json"
OUT = ROOT / "data/reference/de_county_geom_2020.json"


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    rows = con.execute(
        f"""SELECT substr(tract_fips, 1, 5) AS county_fips,
                   ST_AsGeoJSON(ST_Union_Agg(ST_GeomFromGeoJSON(geometry_json))) AS geometry_json
            FROM read_json('{TRACTS}', format='array',
                           columns={{'tract_fips': 'VARCHAR', 'geometry_json': 'VARCHAR'}})
            GROUP BY 1 ORDER BY 1"""
    ).fetchall()
    con.close()
    records = [{"county_fips": fips, "geometry_json": geometry} for fips, geometry in rows]
    OUT.write_text(json.dumps(records))
    print(f"de_county_geom: {len(records)} counties -> {OUT.name}")


if __name__ == "__main__":
    main()
