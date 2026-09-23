# AGENTS.md

Guidance for AI coding tools working alongside a human operator on primary-care-atlas.

Read `README.md` for the project overview and setup, and `HISTORY.md` for the
decision log. This file adds the working conventions those two do not state.

## The human owns the README

Do not edit `README.md`. A human operator maintains it by hand to keep the project's
architecture clear in a human mind.

If a task implies a README change, do the code work, then tell the operator which
README sections now need their update. Propose the wording; let them apply it.

## Log decisions in HISTORY.md

`HISTORY.md` records every design decision, accepted and rejected, with the human-vs-AI
dissonance and how it resolved. Append a numbered entry when you make or propose a decision that
shapes the build. Never delete or rewrite an old entry; supersede it and cross-link.

- Keep entries terse: one line per point.
- Record rejected proposals too, with the reason. It stops the next tool re-proposing them.
- Use only absolute dates (YYYY-MM-DD).
- Add a row to the Index table at the top; keep its TL;DR identical to the entry's.

Entry format:

````
## NNN — Title
`[TYPE]` · YYYY-MM-DD · status

**TL;DR** — one line.

**Decision**
- point
- point
````

- `NNN` — next sequence number, zero-padded to 3 digits, in the `## NNN — Title` heading.
- `[TYPE]` — `[DECISION]` for a choice, `[NOTE]` for an observation. A `[DECISION]` carries a
  `status` (`accepted` / `proposed` / `rejected`) on the metadata line; a `[NOTE]` omits it.
- `**TL;DR**` — a one-line gist, the first line of the body.
- Body: bold labeled sections. Use the labels the existing entries use — **Context**, **Decision**,
  **Dissonance (human vs AI)**, **Impact**, **Notes**, **Rejected**, **Open**, **Verification**, **Why**.
  Include only the ones the entry needs.
- Supersession: mark the metadata line `*revises NNN*` (and the old entry `*revised by NNN*`), and
  cross-link entries inline as `[NNN](#anchor)`.

## Commands

`mise` runs every task. Run `mise tasks ls` for the current list; do not copy task
definitions here. The common ones:

- `mise run check` — type-check (`ty`) plus tests (`pytest`). Run this before you
  call work done.
- `mise run pipeline` — rebuild the DuckDB assets end to end.
- `mise run dev` — API plus Vite dev servers with reload.

## Architecture conventions

- **Config drives scope and state.** Read the state filter and the primary-care
  specialty scope from `config/config.toml`. Never hardcode `"DE"` or a specialty
  list in pipeline logic.
- **Pipeline layers.** Sources flow through the pipeline `stg_* -> dim_*/fct_* -> mart_*`. Put
  question-specific logic only in the marts.
- **Assets are a DAG as data.** Each step module declares one `ASSET` instance -- a subclass of
  `Asset` (`SqlAsset` / `StageAsset` / `FuncAsset`, defined in `pipeline/asset.py`). `pipeline/assets.py`
  collects them in dependency order and `pipeline/cli.py` executes the graph. Keep this shape (name,
  output, inputs, output_columns + a `build(con)` method) so the pipeline can be lifted to Dagster or
  Airflow or another orchestrator without a rewrite. See HISTORY 027.
- **Marts get domain-semantic names** (`mart_provider_locations`).
  Name the concept or question being answered in the docstring only.
- **Build for extension.** Add a source using the existing per source convention: one
  ingest to one DuckDB table.

## Handle CMS data quirks visibly

Each source carries its own encoding, suppression, and shape traps. `HISTORY.md`
notes the known ones (latin-1 files, uppercase state names, suppression flags,
per-NPI fan-out, the HRSA lenient reader). When you meet a new quirk:

- Handle it per-source, not with a global switch. See the `Source.lenient` pattern
  (HISTORY 014).
- Make the handling visible in code and note it in `HISTORY.md`.
- Never let a quirk cause a row to silently drop. Always fail loud or account for every row.

## Verify at each step

- `mise run check` must pass: `ty` clean, `pytest` green, `ruff` checks clean and formatting clean. Surface any issues to the human operator unless they are trivial (formatting, unused imports, functions, etc).
- `tests/test_data_quality.py` guards grain, referential integrity, row-count
  reconciliation, and value ranges. Keep these green; add a guard when you add a mart.
- Reconcile row counts against the figures in `HISTORY.md` when you rebuild. A count
  that moves is either a bug or a new decision to log.
- Preserve traceability: a reader should trace any number in the app back through the
  marts to the source. Keep that chain intact.

## Work with the human, not around them

- Do not presume architecture. When a runtime or design choice is open, propose it and
  wait. HISTORY 010 records an architecture presumed and rejected.
- Surface dissonance. When your recommendation differs from the operator's, state the
  trade-off plainly and log the resolution.
- Anchor claims in verified sources (live CMS dictionaries or APIs, the committed
  reference files), not in memory.

## Layout and data

- `pipeline/` — ETL: `acquire/`, `ingest/`, `model/`, `marts/`, `reference_gen/`.
- `app/api/` — FastAPI backend; `app/web/` — Vue 3 + Vite frontend.
- `data/sources/` is gitignored (rebuild via `mise run acquire`); `data/db/` is
  tracked. Reference files (NUCC taxonomy, ZCTA gazetteer, geometries) are committed.
- `notebooks/` holds EDA. Jupyter is dev-only.

## Updating this file
When new code is added that might impact the overall architecture, propose updates to this file. All updates should be terse, concise, and easy to understand. Adopting a simplified language approach such as ASD-STE100 is preferred.
