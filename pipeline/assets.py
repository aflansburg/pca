"""Asset registry: the pipeline DAG as data.

Each Asset declares output, inputs, build(), schema contract, and CI-rebuildability -- the metadata
to lift to Dagster (@asset(deps=inputs)) or Airflow. A thin CLI runs them in order today.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pipeline.ingest import (
    county_geom,
    county_population,
    dac,
    hpsa,
    mua,
    mup_provider,
    mup_service,
    nppes,
    reassignment,
    reference,
    tract_geom,
    zcta,
)
from pipeline.marts import (
    mart_county_access,
    mart_county_geo,
    mart_practice_groups,
    mart_provider_locations,
    mart_provider_peer_comparison,
    mart_provider_services,
    mart_provider_spending,
    mart_provider_volume,
    mart_tract_access,
    mart_tract_geo,
)
from pipeline.model import bridge_provider_org, dim_location, dim_org, dim_provider


@dataclass(frozen=True)
class Asset:
    name: str
    output: str
    inputs: tuple[str, ...]
    build: Callable[[object], object]
    output_columns: dict[str, str]
    rebuild_in_test: bool


def _asset(mod, name: str) -> Asset:
    return Asset(name, mod.OUTPUT, mod.INPUTS, mod.build, mod.OUTPUT_COLUMNS, mod.REBUILD_IN_TEST)


# Declared in dependency order (upstream first).
ASSETS: tuple[Asset, ...] = (
    _asset(nppes, "nppes"),
    _asset(dac, "dac"),
    _asset(hpsa, "hpsa"),
    _asset(mua, "mua"),
    _asset(mup_provider, "mup_provider"),
    _asset(mup_service, "mup_service"),
    _asset(reassignment, "reassignment"),
    _asset(reference, "ref_taxonomy"),
    _asset(zcta, "ref_zcta_centroid"),
    _asset(county_population, "ref_county_population"),
    _asset(tract_geom, "ref_tract_geom"),
    _asset(county_geom, "ref_county_geom"),
    _asset(dim_provider, "dim_provider"),
    _asset(dim_location, "dim_location"),
    _asset(dim_org, "dim_org"),
    _asset(bridge_provider_org, "bridge_provider_org"),
    _asset(mart_provider_locations, "mart_provider_locations"),
    _asset(mart_county_access, "mart_county_access"),
    _asset(mart_tract_access, "mart_tract_access"),
    _asset(mart_tract_geo, "mart_tract_geo"),
    _asset(mart_county_geo, "mart_county_geo"),
    _asset(mart_provider_spending, "mart_provider_spending"),
    _asset(mart_provider_volume, "mart_provider_volume"),
    _asset(mart_provider_services, "mart_provider_services"),
    _asset(mart_provider_peer_comparison, "mart_provider_peer_comparison"),
    _asset(mart_practice_groups, "mart_practice_groups"),
)

BY_NAME = {a.name: a for a in ASSETS}
