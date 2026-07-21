import streamlit as st
from components.premium_ui import render_premium_table

from services.analysis_diagnostics import (
    build_model_diagnostics,
    diagnostics_has_failure,
)


def render_developer_diagnostics_panel(
    data,
    forecast_days: int,
    market_symbol: str,
    asset_name: str,
) -> None:
    diagnostics = build_model_diagnostics(
        data=data,
        forecast_days=forecast_days,
        market_symbol=market_symbol,
        asset_name=asset_name,
    )

    failed = diagnostics_has_failure(diagnostics)

    if failed:
        st.error("Geliştirici Tanı Paneli: Bu varlıkta veri/model problemi var. Sistem sonucu gizlemiyor.")
    else:
        st.success("Geliştirici Tanı Paneli: Veri ve model ön koşulları geçti.")

    with st.expander("🧪 Geliştirici Tanı Paneli — Veri ve Model Kontrolü", expanded=failed):
        render_premium_table(diagnostics, width="stretch")
