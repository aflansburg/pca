"""Load ZIP-centroid reference -> ref_zcta_centroid (ZCTA5 -> lat/lon).

Fallback coords for addresses the Census geocoder can't match. The Gazetteer's last column has
trailing-space padding, so read positionally and TRIM. Run: uv run python -m pipeline.ingest.zcta
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect, scalar
from pipeline.sources import ROOT

GAZ_PATH = ROOT / "data/reference/2020_Gaz_zcta_national.txt"

INPUTS: tuple[str, ...] = ()
OUTPUT = "ref_zcta_centroid"
OUTPUT_COLUMNS = {"zcta5": "VARCHAR", "lat": "DOUBLE", "lon": "DOUBLE"}
REBUILD_IN_TEST = True  # reads the committed gazetteer file


def build(con) -> None:
    con.execute(
        r"""CREATE OR REPLACE TABLE ref_zcta_centroid AS
            SELECT column0 AS zcta5,
                   TRY_CAST(TRIM(column5) AS DOUBLE) AS lat,
                   TRY_CAST(TRIM(column6) AS DOUBLE) AS lon
            FROM read_csv(?, delim='\t', header=false, skip=1, all_varchar=true)""",
        [str(GAZ_PATH)],
    )


def main() -> None:
    con = connect()
    build(con)
    print(f"ref_zcta_centroid: {scalar(con, 'SELECT count(*) FROM ref_zcta_centroid')} ZCTAs")
    con.close()


if __name__ == "__main__":
    main()
