"""Load the NUCC taxonomy reference -> ref_taxonomy (code -> readable specialty).

Not state-scoped and not subject to CMS drift, so it bypasses the Source contract.
Run: uv run python -m pipeline.ingest.reference
"""

from __future__ import annotations

from pipeline.asset import SqlAsset
from pipeline.ingest._duckdb import scalar
from pipeline.sources import ROOT

NUCC_PATH = ROOT / "data/reference/nucc_taxonomy_261.csv"

ASSET = SqlAsset(
    name="ref_taxonomy",
    output="ref_taxonomy",
    inputs=(),
    output_columns={
        "code": "VARCHAR",
        "grouping": "VARCHAR",
        "classification": "VARCHAR",
        "specialization": "VARCHAR",
        "display_name": "VARCHAR",
    },
    rebuild_in_test=True,  # reads the committed NUCC reference file
    sql="""CREATE OR REPLACE TABLE ref_taxonomy AS
           SELECT "Code" AS code, "Grouping" AS grouping, "Classification" AS classification,
                  "Specialization" AS specialization, "Display Name" AS display_name
           FROM read_csv(?, all_varchar=true, header=true)""",
    params=(str(NUCC_PATH),),
)


def main() -> None:
    ASSET.run(lambda con, _: print(f"ref_taxonomy: {scalar(con, 'SELECT count(*) FROM ref_taxonomy')} codes"))


if __name__ == "__main__":
    main()
