# VBC — data dictionary notes (suppression codes)

Provenance: CMS publishes these dictionaries only as rendered web pages (SPA); there is no
downloadable dictionary file, and the data-api exposes column headers but not definitions.
The definitions below are transcribed from the CMS dictionary resource pages (cited), not a raw file.
Verified 2026-09-14.

## Number of ACO Assigned Beneficiaries by County (2024 PUF)

File: `Number_Of_ACO_Assigned_Beneficiaries_by_County_PUF_2024_01_01.csv`
Dataset UUID: `ae8c9418-acc9-4442-b217-33291448f6b8`
CSV: https://data.cms.gov/sites/default/files/2025-11/c9b8923e-5bb4-4d28-8387-48d9bde5e74c/Number_Of_ACO_Assigned_Beneficiaries_by_County_PUF_2024_01_01.csv
Dictionary page: https://data.cms.gov/resources/number-of-accountable-care-organization-assigned-beneficiaries-by-county-data-dictionary-2023

Count columns: `AB_Psn_Yrs_ESRD`, `AB_Psn_Yrs_DIS`, `AB_Psn_Yrs_AGDU`, `AB_Psn_Yrs_AGND`, `Tot_AB_Psn_Yrs`, `Tot_AB`.

Suppression codes in count columns:
- `*` = suppressed. The county has 1-10 assigned beneficiaries of that enrollment type,
  OR the county was selected for complementary suppression (blocks back-calculation).
- `.` = missing/none. The county has zero assigned beneficiaries of that enrollment type.

Threshold: values for counts of 1-10 are suppressed (< 11).

Handling: parse `*` and `.` as null before numeric aggregation. Any county sum from unmasked
rows is a LOWER BOUND, not a true total. Label it "sum of unmasked ACOs".

## County-level Aggregate Expenditure and Risk Score

Full title: "County Level Fee-For-Service Data for Shared Savings Program Benchmark PUF".
Dictionary page: https://data.cms.gov/resources/county-level-aggregate-expenditure-and-risk-score-data-on-assignable-beneficiaries-data-dictionary-0

Columns: `YEAR`, `STATE_NAME`, `COUNTY_NAME`, `STATE_ID` (2-digit SSA), `COUNTY_ID` (3-digit SSA; leading zeros may drop).
Then per enrollment type (ESRD, DIS, AGDU, AGND):
- `PER_CAPITA_EXP_*` = annualized, truncated, weighted mean total expenditure per assignable person-year.
- `AVG_RISK_SCORE_*` = mean CMS-HCC risk score, renormalized so national FFS mean = 1.0.
- `AVG_DEMOG_SCORE_*` = demographic risk score, renormalized to 1.0.
- `PERSON_YEARS_*` = assignable beneficiaries adjusted for months enrolled in that type.

Suppression: **different from the ACO-by-county file above.** A county x enrollment-type value is
suppressed when that county has **1-10** assignable beneficiaries of that type. Suppressed cells are
**blank/omitted** here -- there is NO `*` or `.` legend in this file. Threshold: published only at >= 11.

## Sources
- https://data.cms.gov/resources/number-of-accountable-care-organization-assigned-beneficiaries-by-county-data-dictionary-2023
- https://www.cms.gov/medicare/payment/fee-for-service-providers/shared-savings-program-ssp-acos/data
