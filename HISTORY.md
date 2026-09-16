# Decision log

A log of decisions (accepted and rejected) and notes, from both the human operator and AI tooling.
Each entry answers what was decided, why, or — inversely — what was proposed and why it was rejected.
The log is append-only: supersessions are cross-linked, never deleted.

Questions this project answers:

- **Q1** — Where are primary-care providers located, and which areas are underserved?
- **Q2** — Who are the highest-volume primary-care providers, and what do they bill for?
- **Q3** — How is primary-care spending distributed across provider types (physicians vs NPs/PAs)?
- **Q4** — Which providers work together — sharing a practice or billing entity?
- **Q5** — How does a given provider's billing profile compare to peers?

## Index

| # | Entry | Type | Status | TL;DR |
|---|---|---|---|---|
| [001](#001--defining-primary-care) | Defining "Primary Care" | DECISION | accepted | Scope = ACA §5501 specialties + provider types, held in config, mapped per source. |
| [002](#002--source-selection) | Source selection | DECISION | accepted | Five CMS sources + HRSA (Q1); MSSP optional (county overlay only). |
| [003](#003--q1-stack) | Q1 stack | DECISION | proposed | NPPES + DAC, Census geocode, DuckDB, FastAPI, Vue, Leaflet, HRSA overlay. |
| [004](#004--repo-structure) | Repo structure | DECISION | accepted | Single uv project, Python 3.14; pipeline/ + app/; ty type-checking. |
| [005](#005--pecos-access-pinned-csv-vs-api) | PECOS access: pinned CSV vs API | DECISION | accepted | API DE-filter where a state column exists, else bulk CSV. *(revised by 024)* |
| [006](#006--eda-notes-de-peek-9-notebooks) | EDA notes (DE peek) | NOTE | — | Per-source quirks + DE row counts from the notebooks. |
| [007](#007--nppes-deactivated-npi-report) | NPPES deactivated NPI report | DECISION | accepted | Don't source it for filtering; keep as an optional scrub. |
| [008](#008--taxonomy-names-nucc-set) | Taxonomy names: NUCC set | DECISION | accepted | NPPES codes → names via the tracked NUCC v26.1 set. |
| [009](#009--scope-filter) | Scope filter | DECISION | accepted | Per-source primary-care allow-lists; NPPES matched on primary taxonomy only. |
| [010](#010--pipeline-runtime) | Pipeline runtime | DECISION | accepted | DuckDB-native scripts; dlt rejected; config holds scope + state only. |
| [011](#011--acquisition--schema-drift) | Acquisition + schema drift | DECISION | accepted | Snapshot everything; schema-contract test (gating) + drift-watch (non-gating). |
| [012](#012--model-layer--asset-registry) | Model layer + asset registry | DECISION | accepted | Assets = DAG as data; stg → dim/fct → mart; dim_provider grain = NPI. |
| [013](#013--unmatched-address-fallback) | Unmatched-address fallback | DECISION | accepted | Geocode misses fall back to ZIP-centroid so they still plot. |
| [014](#014--hrsa-ingest-quirks) | HRSA ingest quirks | NOTE | — | HPSA is UTF-8; per-source lenient reader for ragged HRSA rows. |
| [015](#015--mart-naming) | Mart naming | DECISION | accepted | Domain-semantic mart names, not `mart_q1_*`. |
| [016](#016--q1-app-mvp) | Q1 app (MVP) | DECISION | accepted | FastAPI + Vue + Leaflet; one command serves SPA + /api. |
| [017](#017--mup-ingest) | MUP ingest | NOTE | — | Stage MUP; scope by joining to dim_provider (canonical NPPES scope). |
| [018](#018--q5-peer-definition) | Q5 peer definition | DECISION | accepted | Peers = same taxonomy; percentile rank; low_confidence when n < 10. |
| [019](#019--q4-practice-groups) | Q4 practice groups | NOTE | — | reassignment → dim_org + bridge → mart_practice_groups. |
| [020](#020--app-views-q2-q5) | App views Q2–Q5 | DECISION | accepted | Tabbed SPA over the marts; Altair → Vega-Lite charts. |
| [021](#021--map-render-fix) | Map render fix | NOTE | — | Blank map = AccessView lacked `flex:1`; measure the box first. |
| [022](#022--drug-pass-through-flagging) | Drug pass-through flagging | NOTE | — | Volume view flags drug HCPCS + medical/drug split. |
| [023](#023--mobile-responsive) | Mobile responsive | DECISION | accepted | CSS-first, single 768px breakpoint, no JS viewport branching. |
| [024](#024--api-acquisition--drift-watch) | API acquisition + drift-watch | DECISION | accepted | Four sources ported to API DE-filter; NPPES + HRSA bulk. *(revises 005)* |
| [025](#025--q1-underserved-done-properly) | Q1 underserved, done properly | DECISION | accepted | Underserved = HRSA MUA + IMU severity; per-capita; facility HPSAs split out. *(revised by 026)* |
| [026](#026--p1-review-fixes-underserved-precision--density--tests) | P1 review fixes | DECISION | accepted | MUA by component type; orgs out of density; drop in_hpsa_county; data-quality tests. *(revises 025)* |

---

## 001 — Defining "Primary Care"
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — Primary care = ACA §5501 specialties + provider types, held in config and mapped per source.

**Context**
The problem statement inherently requires that we define "primary care." We must set a single scope,
which is the set of specialties and provider types we count as primary care. Then we must map that
scope to each source, because each source (NPPES, MUP, or DAC) labels specialties differently.

**Decision**
- Include these specialties: general practice, internal medicine, family medicine, pediatrics, geriatric medicine.
- Include these provider types: physician, nurse practitioner (primary care), physician assistant, clinical nurse specialist.
- This anchors the scope to the ACA Section 5501 primary care definition and holds it in a config list.

**Dissonance (human vs AI)** — None.

**Impact** — "Primary care" exists as a mapping. Concept-to-source mapping:
- NPPES → NUCC taxonomy codes
- MUP → CMS specialty description
- DAC → DAC specialty field

## 002 — Source selection
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — Keep five CMS sources, add HRSA for Q1, retain MSSP as optional (county overlay only).

**Context**
The brief provides a list of six data sources. We inspected each against its live CMS dictionary or
API, then mapped it to the five questions.

**Decision** — Keep five CMS sources. Add HRSA (Q1). Retain MSSP under investigation.
- NPPES — Q1. Identity, practice location, taxonomy.
- DAC — Q4; helps Q1/Q3/Q5. Adds Org_PAC_ID, credential, specialty.
- MUP by-Provider — Q2/Q3/Q5. Per-NPI totals (Tot_Srvcs, Tot_Mdcr_Pymt_Amt).
- MUP by-Service — Q2/Q5. Per-NPI HCPCS mix (HCPCS_Cd).
- Reassignment — Q4. `revalidation_group_reassignment_pa_xref` for individual-to-group cross-reference. Medicare FFS Public Provider Enrollment for NPI to org PAC ID.
- MSSP — Optional. County overlay only (see dissonance); NPI enrichment rejected (TIN-keyed).
- HRSA HPSA/MUA — Q1. Official shortage-area overlay = underserved denominator.

**Dissonance (human vs AI)** — resolved; one dispute was really two.
- NPI-level enrichment: AI right. REJECT. Participant key is TIN; TIN is in none of our public files (NPPES/MUP/PECOS). The PDF's "participating PAC IDs" is imprecise; the real key is TIN → needs a ResDAC DUA.
- County-level overlay: human right. ACCEPT. No provider join needed. The overlay is primary-care-anchored by construction (ACO assignment driven by primary-care claims). Use: Q1 ACO penetration over the HRSA shortage layer; Q3 county per-capita expenditure + risk-score backdrop.
- Cautions: 3 DE counties (New Castle, Kent, Sussex), small-cell suppression; it is ACO-assigned FFS residing in DE, not DE-based ACOs; assigned population, not care delivered; align MSSP PY24 vs MUP year.
- Scope: MSSP stays optional → county overlay only, time-boxed, gated behind the core five.

**Open** — none. Underserved = HRSA HPSA/MUA overlay (decided 2026-09-14).

**Verification**
- Every field name came from a live CMS dictionary or API.
- Currency 2026-09-14: MUP year 2024; NPPES monthly full; DAC ~3.39M rows; PPEF quarterly.
- MSSP county files verified 2026-09-14 from live CSV headers.
- Files 2 and 3 carry state + county and include Delaware, our initial state to support. File 1 has no geography.
- Data sources verified and checked for relevance in a Jupyter notebook.

**Impact**
- Build source set is five confirmed, plus MSSP under investigation.
- Thin slice (Q1) needs NPPES, plus DAC for per-location precision.
- Q1 slice ready to plan.

## 003 — Q1 stack
`[DECISION]` · 2026-09-14 · proposed

**TL;DR** — Q1 stack: NPPES + DAC, Census geocode, DuckDB, FastAPI, Vue, Leaflet, HRSA overlay.

**Decision**
- sources — NPPES + DAC
- geocode — Census Geocoder (street-level)
- store — DuckDB
- backend — FastAPI
- frontend — Vue
- map — Leaflet (markercluster points, GeoJSON overlay)
- underserved — HRSA HPSA/MUA overlay

**Dissonance (human vs AI)**
- AI proposed: NPPES-only; recommended geocode/store/frontend as open choices.
- Human pushback: NPPES + DAC; chose FastAPI + Vue + Leaflet.

## 004 — Repo structure
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — Single uv project (Python 3.14); pipeline/ + app/ + notebooks/; ty type-checking.

**Decision**
- Single root uv project with Python 3.14.
- Runtime deps: duckdb, pandas, pyarrow, requests. Dev group: jupyterlab, ipykernel, ty.
- Layers: pipeline/ (ETL), app/ (FastAPI+Vue), notebooks/ (.ipynb), data/sources (raw, ignored), data/db (processed, tracked).
- Jupyter is dev-only.
- Type check: ty (Astral), dev dep. `uv run ty check pipeline`. Added 2026-09-15; fixed 7 initial errors (fetchone() Optional, Optional narrowing).

## 005 — PECOS access: pinned CSV vs API
`[DECISION]` · 2026-09-14 · accepted · *revised by [024](#024--api-acquisition--drift-watch)*

**TL;DR** — API DE-filter where a trusted state column exists, else pinned bulk CSV.

**Dissonance (human vs AI)**
- AI: pin one dated bulk CSV per source. Reproducible.
- Human: filter server-side by state via API where available; avoid pulling national files.

**Decision** — Per-dataset, by whether a trusted state column exists.
- Has state (MUP, FFS Enrollment): API server-side filter by DE. Lighter.
- No native state (Reassignment xref; NPI-scoped): bulk CSV, pin dated release, join to DE NPI set.
- Resolve UUID/CSV path from dataset metadata; never hardcode. Pin resolved value + date.

## 006 — EDA notes (DE peek, 9 notebooks)
`[NOTE]` · 2026-09-14

**TL;DR** — Per-source quirks (encodings, suppression, fan-out) and DE row counts from the EDA notebooks.

**Notes**
- PPEF Enrollment is latin-1, not UTF-8 (byte 0xA0). Read encoding="latin-1".
- VBC county files use UPPERCASE state names ("DELAWARE"). Wrong case → silent 0 rows.
- VBC ACO-by-county suppression (CMS dict confirmed): `*` = 1-10 or complementary; `.` = zero. Parse as null; sums are lower bounds.
- DAC fan-out 1.65 rows/NPI, reassignment 1.55. Dedupe on purpose.
- PROVIDER_TYPE_DESC prefixed "PRACTITIONER - "; map on the suffix.

**DE row counts** — NPPES 27,975; DAC 11,894 / 7,192 NPIs; Enrollment 12,778; Reassignment 13,771 / 1,262 groups; MUP Provider 4,931 ($555M); MUP Service 40,082; ACO-by-county 260 ACOs; County agg 3; PY financial 476.

## 007 — NPPES deactivated NPI report
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — Don't source the deactivated-NPI report for filtering; keep it as an optional scrub.

**Decision** — Do not source it for filtering. Keep the downloaded file on hand as an optional scrub.
- Main NPPES file already excludes deactivated NPIs. DE: only 49/27,975 carry a deactivation date, and being present = reactivated/active.
- Report is just NPI + NPPES Deactivation Date (xlsx).
- Optional later: anti-join it against MUP/DAC/PECOS to drop NPIs deactivated after their vintage. Not in the thin slice.

## 008 — Taxonomy names: NUCC set
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — NPPES codes map to readable names via the tracked NUCC v26.1 taxonomy set.

**Decision**
- NPPES codes map names via the NUCC taxonomy set. `data/reference/nucc_taxonomy_261.csv` (v26.1, 883 codes, tracked).
- Use: readable labels + build the primary-care code allow-list (see [001](#001--defining-primary-care)). NPPES only; DAC/MUP/PPEF carry specialty text.

## 009 — Scope filter
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — Per-source primary-care allow-lists in config; NPPES matched on primary taxonomy only.

**Decision** — Per-source primary-care allow-lists. Held in config/config.toml (scope + state only; see [010](#010--pipeline-runtime)).
- NPPES: NUCC codes, matched on PRIMARY taxonomy only (switch=Y).
- DAC/MUP/PPEF: exact specialty strings. PPEF anchors "PRACTITIONER - " (excludes ORDER-AND-REFERRING/DME).
- Include NP/PA base (unspecified) + org NPIs (Entity Type 2). Carry Entity Type Code to split person vs practice.
- NP/PA/CNS: NPPES picks primary-care specializations; DAC/MUP/PPEF are monolithic (included wholesale).

**Why primary-taxonomy-only** — Any-slot adds 527 DE providers whose real primary role is specialist (psych NP 67, hospitalist 36, cardiology 22, EM 22, ortho 19, PA-surgical 15…). They carry base IM/FM from training. Primary-only excludes them.

**DE PC counts** — NPPES 4,524 (3,860 indiv / 664 org); PPEF 4,201; DAC 2,870; MUP 1,989 ($138.8M).

## 010 — Pipeline runtime
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — DuckDB-native scripts; dlt rejected; config holds the scope allow-list + state only.

**Dissonance (human vs AI)**
- AI: added config.toml + pipeline/config.py loader, presuming a config-driven pipeline.
- Human: rejected that. Runtime was undecided; don't presume architecture.

**Decision**
- Runtime = DuckDB-native scripts (read_csv + WHERE pushdown). Per-source seam: one ingest → one DuckDB table.
- Rejected dlt: row-by-row normalize is overhead on the giant CSVs (NPPES 11.7GB, MUP-svc 3.3GB); DuckDB reads them natively.
- Retain config.toml for the scope allow-list + state ONLY. Not a general pipeline-config layer.

## 011 — Acquisition + schema drift
`[DECISION]` · 2026-09-14 · accepted

**TL;DR** — Snapshot everything; a schema-contract test gates PRs, a daily drift-watch Action warns on upstream drift.

**Decision**
- Snapshot everything; don't run live APIs at query time. API doesn't fix drift (same columns, new UUID per release).
- Acquire per-source behind the seam: API DE-filter for state sources (MUP, PPEF), bulk for NPPES + reference (NUCC, HRSA).
- Each source pins release + expected_columns + provenance (uuid, fetch date, row count, schema hash).
- Two checks, never merged:
  1. schema-contract test — deterministic, gates PRs, runs on our data.
  2. drift-watch — daily GitHub Action, non-gating. Polls data-api /data-viewer headers vs expected_columns; red x + opens issue on drift.
- Both read one source of truth: expected_columns per source. Drift logic in a repo script (runs local + CI); the Action is a thin wrapper.

## 012 — Model layer + asset registry
`[DECISION]` · 2026-09-15 · accepted

**TL;DR** — Assets are a DAG as data; layers stg → dim/fct → mart; dim_provider grain = NPI.

**Decision**
- Assets = DAG as data: Asset(name, output, inputs, build) in pipeline/assets.py; run via pipeline/cli.py. Can be lifted to Dagster @asset(deps=inputs) or Airflow tasks with no rewrite.
- Layers: stg_* → dim_*/fct_* → mart_*. Question-specific logic only in marts.
- dim_provider: grain = NPI. is_primary_care from config scope; provider_category (Physician/NP/PA/CNS) for Q3; taxonomy_label via NUCC (ref_taxonomy); is_medicare_enrolled from DAC. Org/practice linkage deferred to a Q4 bridge.
- DE primary-care: 4,524 (Physician 2,023 / NP 1,646 / PA 810 / CNS 45).

## 013 — Unmatched-address fallback
`[DECISION]` · 2026-09-15 · accepted

**TL;DR** — Census geocode misses fall back to a ZIP-centroid so they still plot, clearly marked coarser.

**Decision** — Census geocode misses fall back to ZIP (ZCTA) centroid so they still plot.
- dim_location.location_source: census | zcta_centroid | unresolved. Centroid rows get lat/lon only (no tract_fips).
- Centroid source: Census 2020 ZCTA gazetteer, tracked in data/reference. Geocode match rate at build: 88% (1,382/1,559).

**Rejected**
- Leave-flagged (drop unmatched from the map). Reason: ~525 PC providers (12%) would vanish from Q1; the centroid keeps them visible, clearly marked coarser.

## 014 — HRSA ingest quirks
`[NOTE]` · 2026-09-15

**TL;DR** — HPSA is UTF-8; a per-source lenient reader parses HRSA's ragged rows without silent drops.

**Notes**
- HPSA file is UTF-8, not latin-1 (the notebook's latin-1 only looked right on ASCII rows). Fixed in the source spec.
- DuckDB delimiter sniff failed on HRSA long lines → parsed as 1 column. Lenient reader: delim=',', strict_mode=false, null_padding=true, parallel=false (no ignore_errors → no silent drops).
- Lenient is PER-SOURCE (Source.lenient): HRSA only. NPPES/DAC keep the plain parallel reader — null_padding breaks NPPES's quoted newlines under DuckDB's parallel scanner.
- Overlay join proven: 201 DE PC providers fall in a Designated MUA tract (geocoded tract_fips ↔ stg_mua).

## 015 — Mart naming
`[DECISION]` · 2026-09-15 · accepted

**TL;DR** — Domain-semantic mart names (`mart_provider_locations`), not `mart_q1_*`.

**Dissonance (human vs AI)**
- AI named marts mart_q1_*. Human rejected: opaque, quarter-collision, won't age.
- Renamed domain-semantic: mart_provider_locations, mart_county_access. Question # in docstring only.

## 016 — Q1 app (MVP)
`[DECISION]` · 2026-09-15 · accepted

**TL;DR** — FastAPI (marts → GeoJSON/JSON) + Vue + Leaflet; one command serves SPA + /api.

**Decision**
- FastAPI (marts → GeoJSON/JSON, read-only DuckDB) + Vue 3.5 TS + Vite 8 + Leaflet markercluster.
- One command serves SPA + /api. MVP = provider map + county panel; deferred: polygon choropleth (TIGER).

## 017 — MUP ingest
`[NOTE]` · 2026-09-15

**TL;DR** — Stage MUP; scope it by joining to dim_provider (canonical NPPES scope), not MUP provider_type.

**Notes**
- stg_mup_provider (4,931), stg_mup_service (40,082) DE. Unlocks Q2/Q3/Q5. Encoding utf-8, plain reader.
- Scope MUP by joining to dim_provider.is_primary_care (canonical NPPES scope), not MUP provider_type.
- Amounts kept as text (parse downstream). Suppression flags + drug/medical split preserved.

## 018 — Q5 peer definition
`[DECISION]` · 2026-09-15 · accepted

**TL;DR** — Peers = same taxonomy/specialty; percentile rank per metric; low_confidence when n < 10.

**Dissonance (human vs AI)**
- AI: peers = provider_category (Physician/NP/PA/CNS) + state. More stable n.
- Human: peers = same taxonomy/specialty → fairer comparison, given DE-only scope.

**Decision**
- Peer group = primary_taxonomy (specialty). Percentile rank per metric (services / benes / medical paid).
- Guard small n: carry peer_group_size per row; low_confidence flag when peer_group_size < 10.

## 019 — Q4 practice groups
`[NOTE]` · 2026-09-15

**TL;DR** — reassignment → dim_org + bridge_provider_org → mart_practice_groups (≥2 PC members).

**Notes**
- Reassignment xref is latin-1 (bad byte ~line 198698), like PPEF. Set encoding=latin-1.
- Chain: stg_reassignment (13,771) → dim_org (1,262) + bridge_provider_org (2,801 PC links) → mart_practice_groups (224 groups with ≥2 PC members). Bridge = who-works-with-whom edge list.
- Top DE groups: Christiana Care 625, Beebe 175, Bayhealth 167, Nemours 93.
- All 5 questions now modeled (data + marts). Remaining: app views for Q2-Q5.

## 020 — App views Q2–Q5
`[DECISION]` · 2026-09-15 · accepted

**TL;DR** — Tabbed SPA over the marts; Altair builds Vega-Lite specs server-side, vega-embed renders them.

**Decision**
- Tabbed SPA over the marts: Access (map) / Volume / Spending / Practice Groups / Peer Compare.
- Charts (Q3, Q5): Altair builds Vega-Lite specs server-side; vega-embed renders client-side (lazy chunk).
- Endpoints: /api/spending, /volume, /providers/{npi}/services, /groups, /groups/{id}/members, /providers/search, /providers/{npi}/peers, /charts/spending, /charts/peers. 28 tests, ty clean.
- All 5 questions now answerable in the app. Backlog unchanged: MSSP, drift-watch, Q1 choropleth, README.

## 021 — Map render fix
`[NOTE]` · 2026-09-15

**TL;DR** — Blank Q1 map = AccessView lacked `flex:1` (collapsed to 320px, width 0). Measure the box first.

**Notes**
- Q1 map blank after the tab refactor: AccessView (flex item of .body) lacked flex:1 → collapsed to the 320px panel width, map width 0 (height was fine). Fix: flex:1 on .access.
- invalidateSize + unmount map.remove() kept as tabbed-map hygiene (were not the bug).
- Diagnosed by measuring the computed box in headless chromium, not theorizing. Lesson: measure first.

## 022 — Drug pass-through flagging
`[NOTE]` · 2026-09-15

**TL;DR** — Volume view flags drug HCPCS lines + a per-provider medical/drug split, to expose the units-as-services skew.

**Notes**
- Volume view: per-provider medical/drug split bar + % drug; drug HCPCS lines tagged (hcpcs_drug_ind='Y').
- Makes the units-as-services skew legible: top-by-services NP = 98% drug ($4.32M drug / $98K medical).
- Frontend-only; fields already on the marts. No backend change.

## 023 — Mobile responsive
`[DECISION]` · 2026-09-15 · accepted

**TL;DR** — CSS-first responsive: a single 768px breakpoint, no JS viewport branching.

**Decision**
- CSS-first, single 768px breakpoint, no JS viewport branching / no VueUse (agent-reviewed, endorsed).
- Split views + tables stack on mobile; tables stay `<table>` inside .scroll-x wrappers (a11y, not display:block); map full-width 55vh above the county panel.
- Mobile row tap scrolls detail into view; tab click scrolls the active tab into view (horizontal bar).
- KeepAlive on the tab views (map no longer refetches 4,508 providers) + onActivated invalidateSize.
- Verified at 390px + desktop in headless chromium (0 refetch on tab return, tables keep table semantics).

## 024 — API acquisition + drift-watch
`[DECISION]` · 2026-09-15 · accepted · *revises [005](#005--pecos-access-pinned-csv-vs-api)*

**TL;DR** — Four sources ported to API DE-filter; NPPES + HRSA bulk; drift-watch wired.

**Decision**
- Acquisition seam: fetch DE snapshot, then stage Source.path unchanged (see [011](#011--acquisition--schema-drift): snapshot, no live API at query time).
- Ported to API DE-filter: MUP provider, MUP service, DAC, reassignment. Bulk-fetched (pinned URL): NPPES (11.7GB; NPI API single-lookup), HRSA HPSA + MUA (national CSV, staged WHERE state). Reference (NUCC, ZCTA) committed.
- Two dialects: data.cms.gov data-api (JSON:API, filter[col]=DE, display column names) for MUP x2 + reassignment; provider-data DKAN datastore (conditions, machine names, limit≤1000) for DAC.
- UUID resolved from metastore/catalog by title, newest vintage; never hardcoded (see [011](#011--acquisition--schema-drift)). Provenance sidecar (uuid, vintage, row count, schema hash) per snapshot.
- Reassignment: API returns UTF-8 JSON → drops the latin-1 quirk (see [006](#006--eda-notes-de-peek-9-notebooks)).
- drift-watch (pipeline/driftwatch.py): polls live schema vs required_columns; daily Action, non-gating, opens one issue on a missing column. Contract source of truth stays required_columns.
- DE snapshot rows match the bulk files (see [006](#006--eda-notes-de-peek-9-notebooks)/[009](#009--scope-filter)): provider 4,931; service 40,082; DAC 11,894; reassignment 13,771.

**Dissonance** — *revises [005](#005--pecos-access-pinned-csv-vs-api)*. 005 chose bulk CSV for reassignment on a "no native state" read. The file/API carry Individual State Code, so reassignment is API-filterable. Reversed to API.

## 025 — Q1 underserved, done properly
`[DECISION]` · 2026-09-15 · accepted · *revised by [026](#026--p1-review-fixes-underserved-precision--density--tests)*

**TL;DR** — Underserved = HRSA MUA + IMU severity + county per-capita; facility HPSAs split out; TIGER choropleth.

**Context** — Old is_underserved_any = any HPSA/MUA designation → all 3 counties flagged, driven by 6 correctional-facility HPSAs. Meaningless.

**Decision**
- Underserved = HRSA's determination (MUA-designated); IMU score = degree (lower worse). No invented threshold.
- Tract grain: mart_tract_access. Underserved = tract-level MUA OR a whole-county MUA covering the tract. All 259 DE tracts covered; shaded by IMU severity: New Castle 57.2 (16 tract-level), Sussex 61.3, Kent 75.7 (whole-county). Matches the DE HRSA map (dehealthforce.org).
- Facility HPSAs (correctional, FQHC) excluded from the area tag, shown separately (distinct population, distinct question).
- County rollup reworked: no binary tag; per-capita PC/10k. Sussex 25.6 < Kent 35.3 < New Castle 45.9 — the signal the tag hid.
- Population: keyless Census popest bulk → committed de_county_population_2023.csv (Census data API now key-gated; committing keeps the rebuild keyless).
- Choropleth: TIGER cb_2020 (259 DE tracts) via DuckDB spatial → committed de_tract_geom_2020.json. Spatial is generation-only; rebuild reads the committed GeoJSON.
- County overlay: tracts dissolved to 3 counties (ST_Union_Agg) → de_county_geom_2020.json; bold severity outline + faint tint, layered over tracts, under the PCP clusters (non-interactive so tract tooltips pass through).
- MUA quirk: tract_fips = county_fips || census_tract; whole-area MUAs = '<county>Not Applicable'. Tract MUAs shade their tract; whole-area MUAs shade every tract in the county (worst applicable IMU). *(refined by [026](#026--p1-review-fixes-underserved-precision--density--tests))*
- Caveat: provider practice address ≠ patient residence; per-capita is a corroborating lens at county grain. mart_provider_locations in_hpsa_county now area HPSAs only. *(in_hpsa_county later dropped in [026](#026--p1-review-fixes-underserved-precision--density--tests))*

## 026 — P1 review fixes: underserved precision + density + tests
`[DECISION]` · 2026-09-16 · accepted · *revises [025](#025--q1-underserved-done-properly)*

**TL;DR** — MUA placed by HRSA component type; orgs out of density; in_hpsa_county dropped; data-quality tests added.

**Context** — A three-lens code review flagged: is_underserved degenerate (all 259 tracts flagged), org NPIs inflating clinician density, in_hpsa_county a non-signal, two unreconciled Q3 spend totals, and no data-quality tests.

**Decision**
- MUA placement by HRSA component type (*revises [025](#025--q1-underserved-done-properly)*): 'Single County' → whole county (Sussex, Kent); 'Census Tract' → its tract (New Castle 16); 'County Subdivision' (Middletown-Odessa, 07689) NOT tract-placed — a documented limitation (needs an MCD→tract crosswalk). is_underserved now 131/259, meaningful again.
- Exclude org NPIs (Entity Type 2) from clinician density in the county + tract marts (600 orgs, 475 mislabeled Physician were inflating per-capita). Orgs still map as points (see [009](#009--scope-filter)).
- Dropped in_hpsa_county (*revises [025](#025--q1-underserved-done-properly)*): every DE county has an area HPSA, so the flag was always true for geocoded providers — a non-signal.
- Q3 spend scope reconciled: NPPES-canonical $124.6M/1,765 (see [017](#017--mup-ingest)) vs MUP-type-scope $138.8M/1,989 (see [009](#009--scope-filter)); the dim_provider inner join also drops ~121 MUP-DE NPIs (NPPES address out-of-state). Documented; tracked by a test.
- Added tests/test_data_quality.py: grain/uniqueness, referential integrity, row-count reconciliation, value ranges, category + suppression invariants, and regression guards (is_underserved not uniform; zero orgs in density).
