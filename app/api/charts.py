"""Chart endpoints: Altair builds Vega-Lite specs from the marts; vega-embed renders them client-side."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
from fastapi import APIRouter, HTTPException

from app.api.db import fetch_df, fetch_dicts

router = APIRouter(prefix="/api/charts")


def _spending_spec(df: pd.DataFrame) -> dict:
    long = df.melt(
        id_vars=["provider_category"],
        value_vars=["medical_paid", "drug_paid"],
        var_name="kind",
        value_name="paid",
    )
    long["kind"] = long["kind"].map({"medical_paid": "Medical (professional)", "drug_paid": "Drug (pass-through)"})
    base: Any = alt.Chart(long)  # Altair's fluent API is dynamically typed
    chart = (
        base.mark_bar()
        .encode(
            x=alt.X("provider_category:N", title="Provider type", sort="-y"),
            y=alt.Y("paid:Q", title="Medicare paid ($)", stack="zero"),
            color=alt.Color("kind:N", title=None, scale=alt.Scale(range=["#1f77b4", "#ff7f0e"])),
            tooltip=[
                alt.Tooltip("provider_category:N", title="Type"),
                alt.Tooltip("kind:N", title="Spend"),
                alt.Tooltip("paid:Q", title="Paid", format="$,.0f"),
            ],
        )
        .properties(width="container", height=300, title="PC Medicare paid by provider type")
    )
    return chart.to_dict()


def _peers_spec(row: dict) -> dict:
    data = pd.DataFrame(
        [
            {"metric": "Services", "percentile": row["pct_services"]},
            {"metric": "Beneficiaries", "percentile": row["pct_beneficiaries"]},
            {"metric": "Medical paid", "percentile": row["pct_medical_paid"]},
        ]
    )
    title = f"{row['provider_name']} vs {row['taxonomy_label']} peers (n={row['peer_group_size']})"
    base: Any = alt.Chart(data)  # Altair's fluent API is dynamically typed
    chart = (
        base.mark_bar(color="#2ca02c")
        .encode(
            x=alt.X("percentile:Q", title="Percentile within specialty peers", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("metric:N", title=None, sort=None),
            tooltip=[alt.Tooltip("metric:N"), alt.Tooltip("percentile:Q", format=".0f")],
        )
        .properties(width="container", height=140, title=title)
    )
    return chart.to_dict()


@router.get("/spending")
def spending_spec() -> dict:
    df = fetch_df(
        "SELECT provider_category, medical_paid, drug_paid "
        "FROM mart_provider_spending ORDER BY total_medicare_paid DESC"
    )
    return _spending_spec(df)


@router.get("/peers")
def peers_spec(npi: str) -> dict:
    rows = fetch_dicts(
        "SELECT provider_name, taxonomy_label, peer_group_size, "
        "pct_services, pct_beneficiaries, pct_medical_paid "
        "FROM mart_provider_peer_comparison WHERE npi = ?",
        [npi],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="provider not in peer comparison")
    return _peers_spec(rows[0])
