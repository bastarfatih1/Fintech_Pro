"""
Tarihsel performans paneli.

Bu bileşen geçmiş performans tablosunu ve
reel getiri açıklamasını Streamlit arayüzünde gösterir.
"""

from typing import Any

import pandas as pd
import streamlit as st

from finans_motoru import hesapla_gecmis_performans
from components.ui_icons import icon_html

def _inject_performance_premium_style() -> None:
    """Performans paneli için premium görünüm stillerini ekler."""
    st.markdown(
        """
        <style>
        .fp-perf-hero {
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 20px;
            padding: 20px 22px;
            margin: 8px 0 18px 0;
            background:
                radial-gradient(circle at top left, rgba(234, 179, 8, 0.18), transparent 34%),
                radial-gradient(circle at bottom right, rgba(59, 130, 246, 0.15), transparent 30%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.90));
            box-shadow: 0 16px 40px rgba(2, 6, 23, 0.22);
        }
        .fp-perf-eyebrow {
            color: #fde68a;
            font-size: 0.76rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 7px;
        }
        .fp-perf-title {
            color: #f8fafc;
            font-size: 1.36rem;
            font-weight: 850;
            margin-bottom: 6px;
        }
        .fp-perf-subtitle {
            color: #cbd5e1;
            font-size: 0.94rem;
            line-height: 1.55;
            max-width: 900px;
        }
        .fp-perf-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }
        .fp-perf-pill {
            border: 1px solid rgba(226, 232, 240, 0.16);
            border-radius: 999px;
            padding: 6px 10px;
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.45);
            font-size: 0.78rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _parse_percentage(value: Any) -> float:
    """Yüzde formatındaki metni float değere çevirir."""
    text = str(value).replace("%", "").replace("+", "").replace(",", "")
    try:
        return float(text)
    except (TypeError, ValueError):
        return 0.0


def _render_performance_hero(
    performance_table: pd.DataFrame,
    investment_amount: float,
    currency_symbol: str,
) -> None:
    """Tarihsel performans paneli için premium giriş alanı gösterir."""
    _inject_performance_premium_style()

    best_period = "Veri yok"
    best_return = 0.0
    worst_period = "Veri yok"
    worst_return = 0.0

    if (
        isinstance(performance_table, pd.DataFrame)
        and not performance_table.empty
        and "Nominal Getiri" in performance_table.columns
        and "Dönem" in performance_table.columns
    ):
        temp = performance_table.copy()
        temp["_nominal_numeric"] = temp["Nominal Getiri"].apply(
            _parse_percentage
        )
        best_row = temp.loc[temp["_nominal_numeric"].idxmax()]
        worst_row = temp.loc[temp["_nominal_numeric"].idxmin()]

        best_period = str(best_row["Dönem"])
        best_return = float(best_row["_nominal_numeric"])
        worst_period = str(worst_row["Dönem"])
        worst_return = float(worst_row["_nominal_numeric"])

    st.markdown(
        f"""
        <div class="fp-perf-hero">
            <div class="fp-perf-eyebrow">Historical Performance Lens</div>
            <div class="fp-perf-title"><span class="fp-title-with-icon">{icon_html("performance_curve")}</span>Tarihsel Performans & Reel Getiri Penceresi</div>
            <div class="fp-perf-subtitle">
                Seçili varlığın geçmiş dönem performansı, sermaye karşılığı ve
                reel getiri görünümü tek tabloda karşılaştırılır.
            </div>
            <div class="fp-perf-pill-row">
                <div class="fp-perf-pill"><span class="fp-pill-with-icon">{icon_html("capital_stack", "fp-icon-small")}</span>Sermaye: {investment_amount:,.2f} {currency_symbol}</div>
                <div class="fp-perf-pill"><span class="fp-pill-with-icon">{icon_html("performance_curve", "fp-icon-small")}</span>En güçlü dönem: {best_period} · {best_return:+.2f}%</div>
                <div class="fp-perf-pill"><span class="fp-pill-with-icon">{icon_html("risk_shield", "fp-icon-small")}</span>En zayıf dönem: {worst_period} · {worst_return:+.2f}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )




def render_performance_panel(
    data: pd.DataFrame,
    current_price: float,
    investment_amount: float,
    currency_rate: float,
    currency_symbol: str,
) -> None:
    """
    Tarihsel performans sekmesinin tamamını oluşturur.

    Args:
        data: Fiyat geçmişini içeren veri çerçevesi.
        current_price: Güncel fiyat.
        investment_amount: Kullanıcının yatırım tutarı.
        currency_rate: Seçilen para birimi dönüşüm oranı.
        currency_symbol: Para birimi sembolü.
    """
    try:
        performance_table = hesapla_gecmis_performans(
            data,
            current_price,
            investment_amount,
            currency_rate,
            currency_symbol,
        )
    except Exception as exc:
        st.error(
            "Tarihsel performans hesaplanamadı. "
            f"Detay: {exc}"
        )
        return

    if performance_table is None:
        st.info("Tarihsel performans verisi bulunamadı.")
        return

    if isinstance(performance_table, pd.DataFrame):
        if performance_table.empty:
            st.info("Tarihsel performans verisi bulunamadı.")
            return

        _render_performance_hero(
            performance_table=performance_table,
            investment_amount=investment_amount,
            currency_symbol=currency_symbol,
        )

        st.dataframe(
            performance_table,
            hide_index=True,
        )
    else:
        st.warning(
            "Tarihsel performans sonucu beklenen tablo biçiminde değil."
        )
        return

    st.caption(
        "Not: Reel getiri hesabında ortalama küresel enflasyon "
        "varsayımı kullanılmaktadır."
    )
