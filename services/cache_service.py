"""
Önbelleğe alınmış veri servisleri.

Bu modül döviz kuru, piyasa geçmişi ve haber verilerini
belirli sürelerle önbellekte tutar.
"""

from typing import Any

import pandas as pd
import streamlit as st
import yfinance as yf

from finans_motoru import get_kurlar
from haber_motoru import canli_rss_haber_cek


@st.cache_data(ttl=900)
def get_cached_currencies() -> dict[str, float]:
    """
    Döviz kurlarını 15 dakika önbellekte tutar.

    Returns:
        Para birimi kodlarını ve kurlarını içeren sözlük.
    """
    return get_kurlar()


@st.cache_data(ttl=600)
def get_cached_news(keyword: str) -> list[dict[str, Any]]:
    """
    Haber sonuçlarını 10 dakika önbellekte tutar.

    Args:
        keyword: Haber aramasında kullanılacak varlık adı.

    Returns:
        Haber kayıtlarından oluşan liste.
    """
    return canli_rss_haber_cek(keyword)


@st.cache_data(ttl=3600)
def get_cached_asset_history(
    symbol: str,
    period: str = "10y",
) -> pd.DataFrame:
    """
    Varlığın geçmiş piyasa verisini bir saat önbellekte tutar.

    Args:
        symbol: Yahoo Finance varlık sembolü.
        period: İndirilecek geçmiş veri süresi.

    Returns:
        OHLCV piyasa verisini içeren DataFrame.
    """
    data = yf.Ticker(symbol).history(period=period)

    if data is None:
        return pd.DataFrame()

    return data