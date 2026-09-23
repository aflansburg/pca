"""Load ZIP-centroid reference -> ref_zcta_centroid (ZCTA5 -> lat/lon).

Fallback coords for addresses the Census geocoder can't match. The Gazetteer's last column has
trailing-space padding, so read positionally and TRIM. Run: uv run python -m pipeline.ingest.zcta
"""

from __future__ import annotations

from pipeline.asset import SqlAsset
from pipeline.ingest._duckdb import scalar
from pipeline.sources import ROOT

GAZ_PATH = ROOT / "data/reference/2020_Gaz_zcta_national.txt"

ASSET = SqlAsset(
    name="ref_zcta_centroid",
    output="ref_zcta_centroid",
    inputs=(),
    output_columns={"zcta5": "VARCHAR", "lat": "DOUBLE", "lon": "DOUBLE"},
    rebuild_in_test=True,  # reads the committed gazetteer file
    sql=r"""CREATE OR REPLACE TABLE ref_zcta_centroid AS
            SELECT column0 AS zcta5,
                   TRY_CAST(TRIM(column5) AS DOUBLE) AS lat,
                   TRY_CAST(TRIM(column6) AS DOUBLE) AS lon
            FROM read_csv(?, delim='\t', header=false, skip=1, all_varchar=true)""",
    params=(str(GAZ_PATH),),
)


def main() -> None:
    ASSET.run(lambda con, _: print(f"ref_zcta_centroid: {scalar(con, 'SELECT count(*) FROM ref_zcta_centroid')} ZCTAs"))


if __name__ == "__main__":
    main()
