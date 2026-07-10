"""
Önbelleğe alınmış veri servisleri.

Bu modül döviz kuru, piyasa geçmişi ve haber verilerini
belirli sürelerle önbellekte tutar.

Piyasa geçmişi artık doğrudan yfinance çağırmak yerine
services.data_provider katmanı üzerinden alınır.
"""

from typing import Any

import pandas as pd
import streamlit as st

from core.market_calendar import normalize_asset_type
from finans_motoru import get_kurlar, get_kurlar_with_metadata
from haber_motoru import canli_rss_haber_cek
from services.data_provider import get_market_history


@st.cache_data(ttl=900)
def get_cached_currencies() -> dict[str, float]:
    """
    Döviz kurlarını 15 dakika önbellekte tutar.

    Returns:
        Para birimi kodlarını ve kurlarını içeren sözlük.
    """
    return get_kurlar()


@st.cache_data(ttl=900)
def get_cached_currencies_with_metadata() -> dict[str, Any]:
    """
    Döviz kurlarını kaynak bilgisiyle birlikte 15 dakika önbellekte tutar.

    Returns:
        rates ve metadata alanlarını içeren sözlük.
    """
    result = get_kurlar_with_metadata()

    return {
        "rates": result.rates,
        "metadata": result.metadata,
    }


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
        symbol: Piyasa veri sağlayıcı sembolü.
        period: İndirilecek geçmiş veri süresi.

    Returns:
        OHLCV piyasa verisini içeren DataFrame.
    """
    asset_type = normalize_asset_type(
        market_symbol=symbol,
    )

    result = get_market_history(
        symbol=symbol,
        period=period,
        asset_type=asset_type,
    )

    if result.is_empty:
        return pd.DataFrame()

    return result.data


@st.cache_data(ttl=3600)
def get_cached_asset_history_with_metadata(
    symbol: str,
    period: str = "10y",
) -> dict[str, Any]:
    """
    Varlığın piyasa verisini kaynak bilgisiyle birlikte döndürür.

    Bu fonksiyon henüz ana uygulama akışında zorunlu değildir.
    Sonraki sprintte arayüzde veri kaynağı etiketi göstermek için
    kullanılacaktır.
    """
    asset_type = normalize_asset_type(
        market_symbol=symbol,
    )

    result = get_market_history(
        symbol=symbol,
        period=period,
        asset_type=asset_type,
    )

    return {
        "data": result.data,
        "metadata": result.metadata,
    }
