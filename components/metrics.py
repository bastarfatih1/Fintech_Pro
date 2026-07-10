"""
Risk metrikleri bileşenleri.

Bu modül hesaplanan risk değerlerini Streamlit kartları halinde gösterir.
"""

from typing import Mapping

import streamlit as st


def render_risk_metrics(stats: Mapping[str, float]) -> None:
    """
    Temel risk metriklerini beş kart halinde gösterir.

    Args:
        stats: VaR, Sharpe, Sortino, MaxDD ve Beta değerlerini
            içeren sözlük benzeri veri.
    """
    required_keys = {"MaxDD", "VaR", "Sharpe", "Sortino", "Beta"}
    missing_keys = required_keys.difference(stats.keys())

    if missing_keys:
        st.error(
            "Risk metrikleri eksik: "
            + ", ".join(sorted(missing_keys))
        )
        return

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Max Drawdown",
        f"%{stats['MaxDD'] * 100:.2f}",
        help="Portföyün zirveden gördüğü en büyük düşüş oranıdır.",
    )

    col2.metric(
        "95% VaR",
        f"%{stats['VaR'] * 100:.2f}",
        help="Normal piyasa koşullarında beklenen günlük kayıp sınırını gösterir.",
    )

    col3.metric(
        "Sharpe Rasyosu",
        f"{stats['Sharpe']:.2f}",
        help="Toplam riske karşı üretilen getiriyi ölçer.",
    )

    col4.metric(
        "Sortino Rasyosu",
        f"{stats['Sortino']:.2f}",
        help="Yalnızca aşağı yönlü riske karşı üretilen getiriyi ölçer.",
    )

    col5.metric(
        "Beta Katsayısı",
        f"{stats['Beta']:.2f}",
        help="Varlığın piyasa hareketlerine karşı duyarlılığını gösterir.",
    )
