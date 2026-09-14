# HRSA — data dictionary notes (HPSA Primary Care + MUA/P)

Provenance: HRSA Data Warehouse bulk files ("DataDownload/DD_Files"). Downloaded 2026-09-14.
Field names below are exact (from the file headers); score ranges/thresholds are from HRSA (cited).
Full per-field definitions live in HRSA's own documentation (linked); this note covers the fields we use.

## Files
- HPSA Primary Care: `data/sources/hrsa/HPSA_Primary_Care.csv`
  from https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_PC.csv (46 MB, 79,750 rows).
- MUA/P: `data/sources/hrsa/MUA.csv`
  from https://data.hrsa.gov/DataDownload/DD_Files/MUA_DET.csv (8.4 MB, 20,132 rows).

DE filter: HPSA `Primary State Abbreviation` == "DE"; MUA `State Abbreviation` == "DE".
Status filter: use active designations only -- HPSA `HPSA Status` == "Designated"; MUA `MUA/P Status Description` == "Designated".

## HPSA Primary Care — key fields
- `HPSA ID` -- designation id. `HPSA Name` -- designation name.
- `Designation Type` -- one of: `Geographic HPSA` (whole area), `HPSA Population` (population group,
  e.g. low-income "LI -", migrant "ME -"), `Federally Qualified Health Center`, `Correctional Facility`.
  Semantics differ: geographic = an area; population = a subgroup within an area; facility = a single site.
- `HPSA Status` -- `Designated`, `Withdrawn`, `Proposed For Withdrawal`.
- `HPSA Score` -- **1 to 25**; higher = greater shortage. Used by NHSC to prioritize clinician assignment.
- `HPSA Population Type`, `HPSA Designation Population`, `HPSA Estimated Underserved Population`, `HPSA FTE`, `HPSA Formal Ratio`.
- Geography: `Common County Name`, `Common State County FIPS Code`, `County or County Equivalent FIPS Code`,
  `State and County FIPS Code`, `Longitude`, `Latitude`, `Rural Status`.

## MUA/P — key fields
- `MUA/P ID`, `MUA/P Service Area Name`.
- `Designation Type` -- `Medically Underserved Area` (area) or Medically Underserved Population.
- `MUA/P Status Description` -- active = `Designated`.
- `IMU Score` -- Index of Medical Underservice, **0-100**; an area/population with **IMU <= 62.0 qualifies** for designation.
- Geography: `State Abbreviation`, `County Equivalent Name`, `County or County Equivalent FIPS Code`, `Census Tract`,
  `County Subdivision Name` -- tract/subdivision grain (finer than county).

## Quirks (from the DE peek)
- Row fan-out: one designation spans multiple rows (per component / per census tract). Dedupe on `HPSA ID` / `MUA/P ID` + tract.
- DE active primary-care HPSAs are **population-type** (low-income / migrant), not whole-county geographic
  (the geographic DE rows were withdrawn/proposed). Mapping "underserved areas" here means population groups within areas.
- DE MUA rows are census-tract level, concentrated in New Castle County. Some `Designated` rows show IMU > 62
  (designated by exception); do not assume every designated row has IMU <= 62.

## Sources
- HPSA scoring (range + NHSC use): https://bhw.hrsa.gov/workforce-shortage-areas/shortage-designation/scoring
- MUA/IMU threshold (<= 62.0): https://bhw.hrsa.gov/shortage-designation/muap-process
- Find Shortage Areas (interactive): https://data.hrsa.gov/tools/shortage-area
- Note: the bhw.hrsa.gov scoring page returned HTTP 403 to automated fetch on 2026-09-14; ranges/threshold
  above are from HRSA's published summaries. Confirm the full HPSA/IMU component formulas against that page in a browser.
