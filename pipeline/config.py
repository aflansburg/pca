"""Load pipeline configuration (state filter + primary-care scope) from config/config.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

_ROOT = next(
    p for p in [Path(__file__).resolve(), *Path(__file__).resolve().parents] if (p / "pyproject.toml").exists()
)
CONFIG_PATH = _ROOT / "config" / "config.toml"


def load_config() -> dict:
    """Read and return the parsed config dict."""
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


CONFIG = load_config()
STATE: str = CONFIG["state"]
PRIMARY_CARE: dict = CONFIG["primary_care"]

# State FIPS derived from `state` (single source of truth; generators avoid a hardcoded "10").
_STATE_FIPS = {
    "AL": "01",
    "AK": "02",
    "AZ": "04",
    "AR": "05",
    "CA": "06",
    "CO": "08",
    "CT": "09",
    "DE": "10",
    "DC": "11",
    "FL": "12",
    "GA": "13",
    "HI": "15",
    "ID": "16",
    "IL": "17",
    "IN": "18",
    "IA": "19",
    "KS": "20",
    "KY": "21",
    "LA": "22",
    "ME": "23",
    "MD": "24",
    "MA": "25",
    "MI": "26",
    "MN": "27",
    "MS": "28",
    "MO": "29",
    "MT": "30",
    "NE": "31",
    "NV": "32",
    "NH": "33",
    "NJ": "34",
    "NM": "35",
    "NY": "36",
    "NC": "37",
    "ND": "38",
    "OH": "39",
    "OK": "40",
    "OR": "41",
    "PA": "42",
    "RI": "44",
    "SC": "45",
    "SD": "46",
    "TN": "47",
    "TX": "48",
    "UT": "49",
    "VT": "50",
    "VA": "51",
    "WA": "53",
    "WV": "54",
    "WI": "55",
    "WY": "56",
}
try:
    STATE_FIPS: str = _STATE_FIPS[STATE]
except KeyError:
    raise ValueError(f"no FIPS mapping for state {STATE!r}; add it to _STATE_FIPS in config.py") from None
