"""
Önbelleğe alınmış veri servisleri.

Bu modül döviz kuru, piyasa geçmişi ve haber verilerini
belirli sürelerle önbellekte tutar.

Piyasa geçmişi artık doğrudan yfinance çağırmak yerine
services.data_provider katmanı üzerinden alınır.
"""

from typing import Any
from types import SimpleNamespace

import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

from core.market_calendar import normalize_asset_type
from finans_motoru import get_kurlar, get_kurlar_with_metadata
from haber_motoru import canli_rss_haber_cek
from services.data_provider import get_market_history
from services.live_market_provider import apply_live_quote_to_history


GRAM_ALTIN_SYMBOL = "GRAM_ALTIN_TRY"
GOLD_OUNCE_SYMBOLS = ("GC=F", "XAUUSD=X", "GOLD=F")
USDTRY_SYMBOLS = ("USDTRY=X", "TRY=X")
TROY_OUNCE_GRAMS = 31.1034768


def _build_gram_gold_metadata(
    source_name: str,
    fallback_used: bool,
    note: str,
):
    """Gram altın veri kaynağı için sade metadata üretir."""
    return SimpleNamespace(
        source_name=source_name,
        provider_type="prototype_fallback" if fallback_used else "api",
        license_status=(
            "Prototip veri / üretim için lisanslı gram altın veri sağlayıcısı gerekir"
            if fallback_used
            else "Yahoo Finance türetilmiş veri / üretim öncesi lisans kontrolü gerekir"
        ),
        is_production_allowed=False,
        fallback_used=fallback_used,
        data_delay="Yaklaşık/türetilmiş veri",
        note=note,
    )


def _normalize_yahoo_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Yahoo Finance çıktısını tek seviyeli OHLCV tabloya çevirir."""
    if data is None or data.empty:
        return pd.DataFrame()

    frame = data.copy()

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [
            str(column[0]) if isinstance(column, tuple) else str(column)
            for column in frame.columns
        ]

    for column in ("Open", "High", "Low", "Close", "Adj Close", "Volume"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "Close" not in frame.columns:
        return pd.DataFrame()

    if "Open" not in frame.columns:
        frame["Open"] = frame["Close"]
    if "High" not in frame.columns:
        frame["High"] = frame[["Open", "Close"]].max(axis=1)
    if "Low" not in frame.columns:
        frame["Low"] = frame[["Open", "Close"]].min(axis=1)
    if "Volume" not in frame.columns:
        frame["Volume"] = 0

    try:
        frame.index = pd.to_datetime(frame.index).tz_localize(None)
    except Exception:
        frame.index = pd.to_datetime(frame.index)

    return frame.dropna(subset=["Close"])


def _download_yahoo_history(symbols: tuple[str, ...], period: str = "10y") -> pd.DataFrame:
    """Birden fazla sembol deneyerek Yahoo Finance geçmiş veri indirir."""
    for symbol in symbols:
        try:
            data = yf.download(
                symbol,
                period=period,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            normalized = _normalize_yahoo_frame(data)
            if not normalized.empty:
                return normalized
        except Exception:
            continue

        try:
            ticker_data = yf.Ticker(symbol).history(
                period=period,
                auto_adjust=False,
            )
            normalized = _normalize_yahoo_frame(ticker_data)
            if not normalized.empty:
                return normalized
        except Exception:
            continue

    return pd.DataFrame()


def _convert_ounce_usd_to_gram_try(
    gold_data: pd.DataFrame,
    usdtry_data: pd.DataFrame,
) -> pd.DataFrame:
    """Ons altın USD verisini yaklaşık gram altın TRY verisine çevirir."""
    if gold_data is None or gold_data.empty:
        return pd.DataFrame()

    converted = gold_data.copy()

    if usdtry_data is not None and not usdtry_data.empty and "Close" in usdtry_data.columns:
        fx_series = (
            usdtry_data["Close"]
            .reindex(converted.index)
            .ffill()
            .bfill()
        )
    else:
        currency_result = get_kurlar_with_metadata()
        fx_series = pd.Series(
            float(currency_result.rates.get("TRY", 1.0)),
            index=converted.index,
        )

    factor = fx_series / TROY_OUNCE_GRAMS

    for column in ("Open", "High", "Low", "Close", "Adj Close"):
        if column in converted.columns:
            converted[column] = (
                pd.to_numeric(converted[column], errors="coerce")
                * factor
            )

    if "Volume" not in converted.columns:
        converted["Volume"] = 0

    return converted.dropna(subset=["Close"])


def _provider_history_or_empty(
    symbol: str,
    period: str,
    asset_type: str,
) -> pd.DataFrame:
    """Provider katmanından veri dener; olmazsa boş tablo döndürür."""
    try:
        result = get_market_history(
            symbol=symbol,
            period=period,
            asset_type=asset_type,
        )
        data = getattr(result, "data", pd.DataFrame())
        return _normalize_yahoo_frame(data)
    except Exception:
        return pd.DataFrame()


def _build_gram_gold_prototype_history(period: str = "10y") -> pd.DataFrame:
    """
    Veri sağlayıcıları boş dönerse uygulamanın durmaması için prototip seri üretir.

    Bu seri gerçek piyasa verisi değildir. Amaç demo akışını kırmadan
    grafik/model/AI ekranlarının test edilebilmesidir.
    """
    days = 2520 if str(period).lower().startswith("10") else 1260
    end_date = pd.Timestamp.today().normalize()
    index = pd.bdate_range(end=end_date, periods=days)

    try:
        currency_result = get_kurlar_with_metadata()
        usd_try = float(currency_result.rates.get("TRY", 34.20))
    except Exception:
        usd_try = 34.20

    # Yaklaşık başlangıç: ons altın varsayımı 2300 USD / 31.103 gram * USDTRY.
    base_price = max((2300.0 / TROY_OUNCE_GRAMS) * usd_try, 100.0)

    rng = np.random.default_rng(42)
    drift = 0.00028
    volatility = 0.010
    returns = rng.normal(loc=drift, scale=volatility, size=days)
    close = base_price * np.exp(np.cumsum(returns))
    close = close / close[-1] * base_price

    open_price = close * (1 + rng.normal(0, 0.002, size=days))
    high = np.maximum(open_price, close) * (1 + np.abs(rng.normal(0.003, 0.002, size=days)))
    low = np.minimum(open_price, close) * (1 - np.abs(rng.normal(0.003, 0.002, size=days)))

    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Adj Close": close,
            "Volume": np.zeros(days, dtype=int),
        },
        index=index,
    )


def _get_gram_gold_history_with_metadata(period: str = "10y") -> dict[str, Any]:
    """Gram altın için analiz edilebilir yaklaşık OHLC geçmişi üretir."""
    gold_data = _provider_history_or_empty(
        symbol="GC=F",
        period=period,
        asset_type="stock",
    )
    if gold_data.empty:
        gold_data = _download_yahoo_history(
            symbols=GOLD_OUNCE_SYMBOLS,
            period=period,
        )

    usdtry_data = _provider_history_or_empty(
        symbol="USDTRY=X",
        period=period,
        asset_type="fx",
    )
    if usdtry_data.empty:
        usdtry_data = _download_yahoo_history(
            symbols=USDTRY_SYMBOLS,
            period=period,
        )

    gram_data = _convert_ounce_usd_to_gram_try(
        gold_data=gold_data,
        usdtry_data=usdtry_data,
    )

    gram_data = _apply_gram_altin_manual_override(gram_data)
    gram_data = apply_live_quote_to_history(
        data=gram_data,
        symbol=GRAM_ALTIN_SYMBOL,
    )
    gram_data = _sanitize_market_history(gram_data)

    if not gram_data.empty:
        return {
            "data": gram_data,
            "metadata": _build_gram_gold_metadata(
                source_name="Yahoo Finance türetilmiş gram altın",
                fallback_used=False,
                note=(
                    "Gram altın; ons altın USD verisi ve USD/TRY verisi kullanılarak "
                    "yaklaşık olarak türetilmiştir. Ticari sürüm için lisanslı gram "
                    "altın veri sağlayıcısı gerekir."
                ),
            ),
        }

    prototype_data = _build_gram_gold_prototype_history(period=period)
    prototype_data = _apply_gram_altin_manual_override(prototype_data)
    prototype_data = apply_live_quote_to_history(
        data=prototype_data,
        symbol=GRAM_ALTIN_SYMBOL,
    )
    prototype_data = _sanitize_market_history(prototype_data)

    return {
        "data": prototype_data,
        "metadata": _build_gram_gold_metadata(
            source_name="Prototype gram gold fallback",
            fallback_used=True,
            note=(
                "Ons altın veya USD/TRY geçmiş verisi alınamadığı için prototip "
                "demo serisi üretildi. Bu veri gerçek piyasa verisi değildir; "
                "yalnızca uygulama akışını test etmek içindir."
            ),
        ),
    }


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
    if symbol == GRAM_ALTIN_SYMBOL:
        return _get_gram_gold_history_with_metadata(period=period).get(
            "data",
            pd.DataFrame(),
        )

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

    cleaned_data = apply_live_quote_to_history(
        data=result.data,
        symbol=symbol,
    )
    return _sanitize_market_history(cleaned_data)


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
    if symbol == GRAM_ALTIN_SYMBOL:
        return _get_gram_gold_history_with_metadata(period=period)

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


def _apply_gram_altin_manual_override(data: pd.DataFrame) -> pd.DataFrame:
    """
    Prototip modunda Gram Altın son fiyat ve önceki kapanışı
    Streamlit secrets üzerinden manuel olarak Matriks değerine sabitler.
    """
    try:
        enabled = str(st.secrets.get("GRAM_ALTIN_OVERRIDE_ENABLED", "false")).lower() == "true"
        if not enabled or data is None or data.empty:
            return data

        current_price = float(st.secrets.get("GRAM_ALTIN_CURRENT_PRICE"))
        previous_close = float(st.secrets.get("GRAM_ALTIN_PREVIOUS_CLOSE"))

        fixed = data.copy()

        if "Close" not in fixed.columns:
            return data

        # Son satır = güncel Matriks fiyatı
        last_idx = fixed.index[-1]
        fixed.loc[last_idx, "Close"] = current_price

        for col in ["Open", "High", "Low"]:
            if col in fixed.columns:
                fixed.loc[last_idx, col] = current_price

        # Bir önceki satır = Matriks önceki kapanış
        if len(fixed) >= 2:
            prev_idx = fixed.index[-2]
            fixed.loc[prev_idx, "Close"] = previous_close

            for col in ["Open", "High", "Low"]:
                if col in fixed.columns:
                    fixed.loc[prev_idx, col] = previous_close

        return fixed

    except Exception:
        return data


def _sanitize_market_history(data: pd.DataFrame) -> pd.DataFrame:
    """
    Model motoruna gitmeden önce piyasa verisini temizler.
    NaN, sonsuz, sıfır veya negatif Close değerleri modelleri bozar.
    """
    if data is None or data.empty:
        return pd.DataFrame()

    fixed = data.copy()

    if "Close" not in fixed.columns:
        return pd.DataFrame()

    numeric_columns = ["Open", "High", "Low", "Close", "Volume"]

    for col in numeric_columns:
        if col in fixed.columns:
            fixed[col] = pd.to_numeric(fixed[col], errors="coerce")
            fixed[col] = fixed[col].replace(
                [float("inf"), float("-inf")],
                pd.NA,
            )

    fixed = fixed.dropna(subset=["Close"])
    fixed = fixed[fixed["Close"] > 0]

    if fixed.empty:
        return pd.DataFrame()

    for col in ["Open", "High", "Low"]:
        if col not in fixed.columns:
            fixed[col] = fixed["Close"]
        else:
            fixed[col] = fixed[col].fillna(fixed["Close"])
            fixed.loc[fixed[col] <= 0, col] = fixed["Close"]

    if "Volume" not in fixed.columns:
        fixed["Volume"] = 0.0
    else:
        fixed["Volume"] = fixed["Volume"].fillna(0.0)

    fixed = fixed[~fixed.index.duplicated(keep="last")]
    fixed = fixed.sort_index()

    return fixed


# COIN_GOLD_DERIVED_PRICE_PATCH
# Darphane altınları için ayrı güvenilir ticker yoksa GRAM_ALTIN_TRY üzerinden
# açık formüllü teorik fiyat üretilir. Bu canlı kuyumcu makası/spread verisi değildir.

def _normalize_coin_symbol(symbol):
    return (
        str(symbol or "")
        .upper()
        .replace("İ", "I")
        .replace("Ü", "U")
        .replace("Ğ", "G")
        .replace("Ş", "S")
        .replace("Ö", "O")
        .replace("Ç", "C")
    )


def _coin_gold_factor(symbol):
    s = _normalize_coin_symbol(symbol)

    # GRAM_ALTIN_TRY zaten baz üründür, ona dokunma.
    if s == "GRAM_ALTIN_TRY":
        return None, None

    # Altın sikke / Cumhuriyet Ata Lira: 7.216 gr, 916.6 milyem.
    if "CUMHURIYET" in s or "ATA_LIRA" in s or "ATAALTIN" in s:
        return 7.216 * 0.9166, "Cumhuriyet Altını / Ata Lira teorik Darphane değeri"

    # Ziynet birlik / tam altın: 7.016 gr, 916.6 milyem.
    if "ZIYNET" in s or "TAM_ALTIN" in s:
        return 7.016 * 0.9166, "Ziynet Tam Altın teorik Darphane değeri"

    if "YARIM" in s:
        return 3.508 * 0.9166, "Ziynet Yarım Altın teorik Darphane değeri"

    if "CEYREK" in s:
        return 1.754 * 0.9166, "Ziynet Çeyrek Altın teorik Darphane değeri"

    return None, None


def _derive_coin_gold_history_from_gram(symbol, factor, label):
    gram_result = _ORIGINAL_GET_CACHED_ASSET_HISTORY_WITH_METADATA("GRAM_ALTIN_TRY")

    if not isinstance(gram_result, dict):
        raise RuntimeError("GRAM_ALTIN_TRY sonucu beklenen metadata formatında gelmedi.")

    data = gram_result.get("data")

    if data is None or data.empty:
        raise RuntimeError("Cumhuriyet altını için GRAM_ALTIN_TRY baz verisi alınamadı.")

    derived = data.copy()

    price_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
    ]

    import pandas as pd

    for col in price_columns:
        if col in derived.columns:
            derived[col] = pd.to_numeric(
                derived[col],
                errors="coerce",
            ) * float(factor)

    metadata = dict(gram_result.get("metadata") or {})
    metadata["source"] = label
    metadata["provider"] = "Darphane theoretical derived"
    metadata["is_derived"] = True
    metadata["base_symbol"] = "GRAM_ALTIN_TRY"
    metadata["calculation_note"] = (
        "Fiyat GRAM_ALTIN_TRY üzerinden ağırlık x milyem oranı ile türetilmiştir. "
        "Kuyumcu alış/satış makası veya serbest piyasa primi içermez."
    )

    return {
        "data": derived,
        "metadata": metadata,
    }


try:
    _ORIGINAL_GET_CACHED_ASSET_HISTORY_WITH_METADATA
except NameError:
    _ORIGINAL_GET_CACHED_ASSET_HISTORY_WITH_METADATA = get_cached_asset_history_with_metadata


def get_cached_asset_history_with_metadata(market_symbol):
    factor, label = _coin_gold_factor(market_symbol)

    if factor is not None:
        return _derive_coin_gold_history_from_gram(
            symbol=market_symbol,
            factor=factor,
            label=label,
        )

    return _ORIGINAL_GET_CACHED_ASSET_HISTORY_WITH_METADATA(market_symbol)


try:
    _ORIGINAL_GET_CACHED_ASSET_HISTORY
except NameError:
    _ORIGINAL_GET_CACHED_ASSET_HISTORY = get_cached_asset_history


def get_cached_asset_history(market_symbol):
    factor, label = _coin_gold_factor(market_symbol)

    if factor is not None:
        result = _derive_coin_gold_history_from_gram(
            symbol=market_symbol,
            factor=factor,
            label=label,
        )
        return result["data"]

    return _ORIGINAL_GET_CACHED_ASSET_HISTORY(market_symbol)
