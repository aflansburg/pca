"""Generate committed DE county population from the keyless popest bulk (the Census data API needs a key).

Refresh: uv run python -m pipeline.reference_gen.county_population
"""

from __future__ import annotations

import csv
import io

import requests

from pipeline.config import STATE_FIPS
from pipeline.sources import ROOT

SRC = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/totals/co-est2023-alldata.csv"
OUT = ROOT / "data/reference/de_county_population_2023.csv"
POP_COL = "POPESTIMATE2023"


def main() -> None:
    resp = requests.get(SRC, timeout=120)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.content.decode("latin-1")))  # popest uses latin-1
    rows = [
        {
            "county_fips": r["STATE"] + r["COUNTY"],  # 5-digit state+county FIPS (e.g. 10001)
            "county_name": r["CTYNAME"],
            "population": r[POP_COL],
        }
        for r in reader
        if r["STATE"] == STATE_FIPS and r["COUNTY"] != "000"  # 000 = state total
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=["county_fips", "county_name", "population"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"de_county_population: {len(rows)} counties -> {OUT.name}")


if __name__ == "__main__":
    main()
