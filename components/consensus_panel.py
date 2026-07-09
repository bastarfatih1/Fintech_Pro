"""
Konsensüs tahmin paneli.

Bu bileşen konsensüs grafiğini ve
gelecek değerlemeleri tablosunu gösterir.
"""

from typing import Any, Mapping

import pandas as pd
import streamlit as st

from charts.consensus import create_consensus_chart


def render_consensus_panel(
    forecast_data: Mapping[str, Any],
    last_date: Any,
) -> None:
    """
    Konsensüs sekmesinin tamamını oluşturur.

    Args:
        forecast_data: Tahmin rotaları, güven bantları ve
            gelecek tablosunu içeren sözlük.
        last_date: Tarihsel verideki son gözlem tarihi.
    """
    st.markdown("### 🎯 Kurumsal Konsensüs & AI Projeksiyonu")

    required_keys = {
        "konsensus_rota",
        "mc_upper",
        "mc_lower",
        "rotalar",
        "gelecek_df",
    }
    missing_keys = required_keys.difference(forecast_data.keys())

    if missing_keys:
        st.error(
            "Konsensüs paneli için eksik veri alanları: "
            + ", ".join(sorted(missing_keys))
        )
        return

    try:
        consensus_figure = create_consensus_chart(
            forecast_data=forecast_data,
            last_date=last_date,
        )
    except Exception as exc:
        st.error(
            "Konsensüs grafiği oluşturulamadı. "
            f"Detay: {exc}"
        )
    else:
        st.plotly_chart(
            consensus_figure,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "responsive": True,
            },
        )

    st.markdown("#### Detaylı Gelecek Değerlemeleri")

    future_table = forecast_data["gelecek_df"]

    if future_table is None:
        st.info("Gelecek değerlemeleri bulunamadı.")
        return

    if isinstance(future_table, pd.DataFrame):
        if future_table.empty:
            st.info("Gelecek değerlemeleri bulunamadı.")
            return

        st.table(future_table)
        return

    st.warning(
        "Gelecek değerlemeleri beklenen tablo biçiminde değil."
    )
