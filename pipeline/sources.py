"""Per-source acquisition specs (the ingest seam).

Each Source declares how a dataset is fetched + its schema contract. The state filter lives in config.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = next(p for p in [Path(__file__).resolve(), *Path(__file__).resolve().parents] if (p / "pyproject.toml").exists())
DB_PATH = ROOT / "data" / "db" / "atlas.duckdb"


@dataclass(frozen=True)
class Source:
    key: str  # short name; drives the stg_<key> table
    kind: str  # "zip" | "csv" | "api"
    path: Path  # file to read (zip or csv)
    member: str | None  # member inside the zip, else None
    encoding: str  # "utf-8" | "latin-1" (CMS files vary; HISTORY 006)
    state_col: str  # column the state filter applies to
    required_columns: tuple[str, ...]  # schema contract: these MUST be present (fail loud otherwise)
    release: str  # pinned release id, for provenance
    lenient: bool = False  # HRSA ragged CSVs: force delimiter, tolerate ragged rows
    # --- acquisition: how the snapshot at `path` is fetched (staging reads `path` unchanged) ---
    acquire: str = "static"  # "api_data_cms" | "api_provider_data" | "bulk" | "static"
    api_keyword: str | None = None  # exact catalog title; resolves the current dataset UUID (never hardcoded)
    download_url: str | None = None  # pinned URL for a "bulk" fetch


NPPES = Source(
    key="nppes",
    kind="zip",
    path=ROOT / "data/sources/provider_registry/npi_files/NPPES_Data_Dissemination_September_2026_V2.zip",
    member="npidata_pfile_20050523-20260913.csv",
    encoding="utf-8",  # NPPES main file is valid UTF-8 (verified full DE scan)
    state_col="Provider Business Practice Location Address State Name",
    required_columns=(
        "NPI",
        "Entity Type Code",
        "Provider Business Practice Location Address State Name",
        "Healthcare Provider Taxonomy Code_1",
        "Healthcare Provider Primary Taxonomy Switch_1",
    ),
    release="NPPES_Data_Dissemination_September_2026_V2",
    # Stays bulk: the file is 11.7 GB monthly and the NPI Registry API is single-lookup, not bulk.
    acquire="bulk",
    download_url="https://download.cms.gov/nppes/NPPES_Data_Dissemination_September_2026_V2.zip",
)

DAC = Source(
    key="dac",
    kind="csv",
    # DE snapshot fetched from the provider-data DKAN datastore (machine column names).
    path=ROOT / "data/sources/provider_registry/dac/dac_DE.csv",
    member=None,
    encoding="utf-8",
    state_col="state",  # DKAN machine name (bulk file used "State")
    required_columns=("npi", "state", "pri_spec", "org_pac_id", "ind_pac_id", "adrs_id"),
    release="DAC_NationalDownloadableFile_2026-09",
    acquire="api_provider_data",
    api_keyword="National Downloadable File",
)

HPSA = Source(
    key="hpsa",
    kind="csv",
    path=ROOT / "data/sources/hrsa/HPSA_Primary_Care.csv",
    member=None,
    encoding="utf-8",  # verified UTF-8 (file(1)); notebook's latin-1 read only looked right on ASCII rows
    state_col="Primary State Abbreviation",
    required_columns=(
        "HPSA ID",
        "Primary State Abbreviation",
        "HPSA Status",
        "Designation Type",
        "HPSA Score",
        "State and County Federal Information Processing Standard Code",
    ),
    release="HRSA_HPSA_PrimaryCare_2026-09",
    lenient=True,  # auto-sniff fails on very long lines; rows are ragged
    # National file from the HRSA Data Warehouse; the lenient staging filters DE.
    acquire="bulk",
    download_url="https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_PC.csv",
)

MUA = Source(
    key="mua",
    kind="csv",
    path=ROOT / "data/sources/hrsa/MUA.csv",
    member=None,
    encoding="utf-8",
    state_col="State Abbreviation",
    required_columns=(
        "MUA/P ID",
        "State Abbreviation",
        "MUA/P Status Description",
        "IMU Score",
        "Census Tract",
        "State and County Federal Information Processing Standard Code",
    ),
    release="HRSA_MUA_2026-09",
    lenient=True,
    acquire="bulk",
    download_url="https://data.hrsa.gov/DataDownload/DD_Files/MUA_DET.csv",
)

MUP_PROVIDER = Source(
    key="mup_provider",
    kind="csv",
    # DE snapshot fetched from the data.cms.gov data-api (display column names preserved).
    path=ROOT / "data/sources/utilization_and_payment/mup/mup_provider_DE_2024.csv",
    member=None,
    encoding="utf-8",
    state_col="Rndrng_Prvdr_State_Abrvtn",
    required_columns=(
        "Rndrng_NPI",
        "Rndrng_Prvdr_State_Abrvtn",
        "Rndrng_Prvdr_Type",
        "Tot_Srvcs",
        "Tot_Mdcr_Pymt_Amt",
    ),
    release="MUP_PHY_R26_P05_by_Provider_2024",
    acquire="api_data_cms",
    api_keyword="Medicare Physician & Other Practitioners - by Provider",
)

MUP_SERVICE = Source(
    key="mup_service",
    kind="csv",
    path=ROOT / "data/sources/utilization_and_payment/mup/mup_service_DE_2024.csv",
    member=None,
    encoding="utf-8",
    state_col="Rndrng_Prvdr_State_Abrvtn",
    required_columns=(
        "Rndrng_NPI",
        "Rndrng_Prvdr_State_Abrvtn",
        "HCPCS_Cd",
        "Tot_Srvcs",
        "Avg_Mdcr_Pymt_Amt",
    ),
    release="MUP_PHY_R26_P05_by_Provider_and_Service_2024",
    acquire="api_data_cms",
    api_keyword="Medicare Physician & Other Practitioners - by Provider and Service",
)

REASSIGNMENT = Source(
    key="reassignment",
    kind="csv",
    # DE snapshot from the data-api (UTF-8 JSON, so the bulk latin-1 quirk is gone). The state
    # filter (Individual State Code) makes reassignment API-filterable; it was bulk before.
    path=ROOT / "data/sources/provider_registry/reassignment/reassignment_DE_2026-09.csv",
    member=None,
    encoding="utf-8",
    state_col="Individual State Code",
    required_columns=(
        "Individual NPI",
        "Individual State Code",
        "Group PAC ID",
        "Group Legal Business Name",
    ),
    release="Revalidation_Reassignment_List_Sep_2026",
    acquire="api_data_cms",
    api_keyword="Revalidation Reassignment List",
)


# Acquisition registry (order not significant; staging order is in assets.py).
ALL_SOURCES: tuple[Source, ...] = (
    NPPES,
    DAC,
    HPSA,
    MUA,
    MUP_PROVIDER,
    MUP_SERVICE,
    REASSIGNMENT,
)
