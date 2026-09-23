"""Asset registry: the pipeline DAG as data (ordered upstream-first).

Each step declares its own Asset instance as `<module>.ASSET`; this file only collects them
in dependency order. The Asset types live in `pipeline/asset.py`. A thin CLI (`pipeline/cli.py`)
runs them in order today; the metadata (inputs/output/columns) is enough to lift the graph to
Dagster @asset(deps=inputs) or Airflow without a rewrite.
"""

from __future__ import annotations

from pipeline.asset import Asset
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

# Declared in dependency order (upstream first).
ASSETS: tuple[Asset, ...] = (
    nppes.ASSET,
    dac.ASSET,
    hpsa.ASSET,
    mua.ASSET,
    mup_provider.ASSET,
    mup_service.ASSET,
    reassignment.ASSET,
    reference.ASSET,
    zcta.ASSET,
    county_population.ASSET,
    tract_geom.ASSET,
    county_geom.ASSET,
    dim_provider.ASSET,
    dim_location.ASSET,
    dim_org.ASSET,
    bridge_provider_org.ASSET,
    mart_provider_locations.ASSET,
    mart_county_access.ASSET,
    mart_tract_access.ASSET,
    mart_tract_geo.ASSET,
    mart_county_geo.ASSET,
    mart_provider_spending.ASSET,
    mart_provider_volume.ASSET,
    mart_provider_services.ASSET,
    mart_provider_peer_comparison.ASSET,
    mart_practice_groups.ASSET,
)

BY_NAME = {a.name: a for a in ASSETS}
