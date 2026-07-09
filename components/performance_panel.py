"""
Tarihsel performans paneli.

Bu bileşen geçmiş performans tablosunu ve
reel getiri açıklamasını Streamlit arayüzünde gösterir.
"""

from typing import Any

import pandas as pd
import streamlit as st

from finans_motoru import hesapla_gecmis_performans


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
    st.markdown(
        "### 📊 Tarihsel Verim & Enflasyon Karşılaştırması"
    )

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

        st.table(performance_table)
    else:
        st.warning(
            "Tarihsel performans sonucu beklenen tablo biçiminde değil."
        )
        return

    st.caption(
        "Not: Reel getiri hesabında ortalama küresel enflasyon "
        "varsayımı kullanılmaktadır."
    )
