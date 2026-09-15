"""Load the NUCC taxonomy reference -> ref_taxonomy (code -> readable specialty).

Not state-scoped and not subject to CMS drift, so it bypasses the Source contract.
Run: uv run python -m pipeline.ingest.reference
"""

from __future__ import annotations

from pipeline.ingest._duckdb import connect, scalar
from pipeline.sources import ROOT

NUCC_PATH = ROOT / "data/reference/nucc_taxonomy_261.csv"

INPUTS: tuple[str, ...] = ()
OUTPUT = "ref_taxonomy"
OUTPUT_COLUMNS = {
    "code": "VARCHAR",
    "grouping": "VARCHAR",
    "classification": "VARCHAR",
    "specialization": "VARCHAR",
    "display_name": "VARCHAR",
}
REBUILD_IN_TEST = True  # reads the committed NUCC reference file


def build(con) -> None:
    con.execute(
        """CREATE OR REPLACE TABLE ref_taxonomy AS
           SELECT "Code" AS code, "Grouping" AS grouping, "Classification" AS classification,
                  "Specialization" AS specialization, "Display Name" AS display_name
           FROM read_csv(?, all_varchar=true, header=true)""",
        [str(NUCC_PATH)],
    )


def main() -> None:
    con = connect()
    build(con)
    n = scalar(con, "SELECT count(*) FROM ref_taxonomy")
    print(f"ref_taxonomy: {n} codes")
    con.close()


if __name__ == "__main__":
    main()
