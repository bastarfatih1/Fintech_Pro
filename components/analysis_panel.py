"""
Ana analiz paneli.

Bu bileşen risk metriklerini, RSI uyarısını,
fiyat grafiğini ve AI teknik analiz özetini gösterir.
"""

from typing import Any, Mapping

import pandas as pd
import streamlit as st

from charts.candlestick import create_price_volume_chart
from charts.rsi import analyze_rsi
from components.metrics import render_risk_metrics
from haber_motoru import ai_teknik_analiz_yorumu


def _render_rsi_status(close_prices: pd.Series) -> None:
    """RSI sonucunu uygun Streamlit mesaj kutusunda gösterir."""
    try:
        rsi_result = analyze_rsi(close_prices)
    except Exception as exc:
        st.warning(
            "RSI analizi tamamlanamadı. "
            f"Detay: {exc}"
        )
        return

    if rsi_result.status == "overbought":
        st.warning(f"⚠️ {rsi_result.message}")
    elif rsi_result.status == "oversold":
        st.success(f"✅ {rsi_result.message}")
    else:
        st.info(f"ℹ️ {rsi_result.message}")


def _render_ai_summary(
    asset_name: str,
    current_price: float,
    bull_target: float,
    bear_target: float,
) -> None:
    """AI teknik analiz özetini güvenli şekilde gösterir."""
    try:
        ai_summary = ai_teknik_analiz_yorumu(
            asset_name,
            current_price,
            bull_target,
            bear_target,
        )
    except Exception as exc:
        st.warning(
            "AI teknik analiz özeti oluşturulamadı. "
            f"Detay: {exc}"
        )
        return

    st.info(f"**🤖 AI Sentezi:** {ai_summary}")


def render_analysis_panel(
    data: pd.DataFrame,
    asset_name: str,
    current_price: float,
    currency_rate: float,
    forecast_data: Mapping[str, Any],
) -> None:
    """
    Ana analiz sekmesinin tamamını oluşturur.

    Args:
        data: Varlığın tarihsel fiyat verisi.
        asset_name: Kullanıcıya gösterilen varlık adı.
        current_price: Varlığın güncel fiyatı.
        currency_rate: Seçilen para birimi dönüşüm oranı.
        forecast_data: Risk metrikleri ve tahmin hedeflerini içeren sözlük.
    """
    required_keys = {"stats", "ayi", "boga"}
    missing_keys = required_keys.difference(forecast_data.keys())

    if missing_keys:
        st.error(
            "Ana analiz paneli için eksik veri alanları: "
            + ", ".join(sorted(missing_keys))
        )
        return

    st.markdown(f"### 📡 {asset_name} - Merkezi Terminal")

    render_risk_metrics(forecast_data["stats"])

    st.markdown("---")

    if "Close" not in data.columns:
        st.error("RSI ve fiyat grafiği için Close sütunu bulunamadı.")
        return

    _render_rsi_status(data["Close"])

    try:
        price_figure = create_price_volume_chart(
            data=data,
            currency_rate=currency_rate,
            current_price=current_price,
            bear_target=forecast_data["ayi"],
            bull_target=forecast_data["boga"],
        )
    except Exception as exc:
        st.error(
            "Fiyat grafiği oluşturulamadı. "
            f"Detay: {exc}"
        )
    else:
        st.plotly_chart(
            price_figure,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "responsive": True,
            },
        )

    _render_ai_summary(
        asset_name=asset_name,
        current_price=current_price,
        bull_target=float(forecast_data["boga"]),
        bear_target=float(forecast_data["ayi"]),
    )
