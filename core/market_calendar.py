"""
Varlık türüne göre tahmin takvimi ve vade standardı.

Bu modül hisse senedi, döviz ve kripto varlıkları için
grafik tarihlerini ve standart vade eşiklerini tek yerde tutar.

Not:
    Hisse ve döviz takvimleri bu aşamada hafta sonlarını hariç tutar.
    Resmî borsa ve ülke tatilleri sonraki sprintte eklenecektir.
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple

import pandas as pd


ASSET_TYPE_STOCK = "stock"
ASSET_TYPE_CRYPTO = "crypto"
ASSET_TYPE_FX = "fx"
ASSET_TYPE_OTHER = "other"


@dataclass(frozen=True)
class MarketCalendarConfig:
    """Bir varlık türünün takvim ve vade ayarları."""

    asset_type: str
    display_name: str
    period_unit: str
    date_frequency: str
    horizons: Tuple[Tuple[str, int], ...]
    xaxis_title: str
    calendar_name: str
    calendar_note: str


_BUSINESS_DAY_HORIZONS: Tuple[Tuple[str, int], ...] = (
    ("1 İşlem Günü", 1),
    ("1 Hafta", 5),
    ("1 Ay", 21),
    ("3 Ay", 63),
    ("6 Ay", 126),
    ("1 Yıl", 252),
    ("2 Yıl", 504),
    ("5 Yıl", 1260),
)

_CALENDAR_DAY_HORIZONS: Tuple[Tuple[str, int], ...] = (
    ("1 Takvim Günü", 1),
    ("1 Hafta", 7),
    ("1 Ay", 30),
    ("3 Ay", 90),
    ("6 Ay", 180),
    ("1 Yıl", 365),
    ("2 Yıl", 730),
    ("5 Yıl", 1825),
)


_CONFIGS = {
    ASSET_TYPE_STOCK: MarketCalendarConfig(
        asset_type=ASSET_TYPE_STOCK,
        display_name="Hisse Senedi / Endeks",
        period_unit="işlem günü",
        date_frequency="B",
        horizons=_BUSINESS_DAY_HORIZONS,
        xaxis_title="Yaklaşık İşlem Tarihi",
        calendar_name="Hafta sonu hariç iş günü",
        calendar_note=(
            "Hafta sonları hariç tutulur. Resmî borsa tatilleri "
            "henüz takvime uygulanmamaktadır."
        ),
    ),
    ASSET_TYPE_FX: MarketCalendarConfig(
        asset_type=ASSET_TYPE_FX,
        display_name="Döviz",
        period_unit="işlem günü",
        date_frequency="B",
        horizons=_BUSINESS_DAY_HORIZONS,
        xaxis_title="Yaklaşık İşlem Tarihi",
        calendar_name="Hafta sonu hariç döviz iş günü",
        calendar_note=(
            "Hafta sonları hariç tutulur. Ülke ve banka tatilleri "
            "henüz takvime uygulanmamaktadır."
        ),
    ),
    ASSET_TYPE_CRYPTO: MarketCalendarConfig(
        asset_type=ASSET_TYPE_CRYPTO,
        display_name="Kripto Varlık",
        period_unit="takvim günü",
        date_frequency="D",
        horizons=_CALENDAR_DAY_HORIZONS,
        xaxis_title="Tahmin Tarihi (7/24)",
        calendar_name="7/24 takvim",
        calendar_note=(
            "Kripto piyasası için hafta sonları dâhil her takvim "
            "günü kullanılır."
        ),
    ),
    ASSET_TYPE_OTHER: MarketCalendarConfig(
        asset_type=ASSET_TYPE_OTHER,
        display_name="Diğer Piyasa Varlığı",
        period_unit="işlem günü",
        date_frequency="B",
        horizons=_BUSINESS_DAY_HORIZONS,
        xaxis_title="Yaklaşık İşlem Tarihi",
        calendar_name="Hafta sonu hariç iş günü",
        calendar_note=(
            "Varlık türü kesin belirlenemediği için hafta sonu hariç "
            "iş günü varsayımı kullanılır."
        ),
    ),
}


_ASSET_TYPE_ALIASES = {
    "stock": ASSET_TYPE_STOCK,
    "equity": ASSET_TYPE_STOCK,
    "hisse": ASSET_TYPE_STOCK,
    "hisse senedi": ASSET_TYPE_STOCK,
    "endeks": ASSET_TYPE_STOCK,
    "index": ASSET_TYPE_STOCK,
    "crypto": ASSET_TYPE_CRYPTO,
    "cryptocurrency": ASSET_TYPE_CRYPTO,
    "kripto": ASSET_TYPE_CRYPTO,
    "kripto varlık": ASSET_TYPE_CRYPTO,
    "fx": ASSET_TYPE_FX,
    "forex": ASSET_TYPE_FX,
    "currency": ASSET_TYPE_FX,
    "döviz": ASSET_TYPE_FX,
    "doviz": ASSET_TYPE_FX,
    "other": ASSET_TYPE_OTHER,
    "diğer": ASSET_TYPE_OTHER,
    "diger": ASSET_TYPE_OTHER,
}


def normalize_asset_type(
    asset_type: Optional[Any] = None,
    market_symbol: Optional[Any] = None,
) -> str:
    """
    Varlık türünü açık alandan veya piyasa sembolünden belirler.

    Öncelik:
        1. Açıkça gönderilen asset_type
        2. Yahoo Finance biçimindeki market_symbol
        3. Güvenli varsayılan olarak hisse senedi
    """
    if asset_type is not None:
        normalized = str(asset_type).strip().lower()
        if normalized in _ASSET_TYPE_ALIASES:
            return _ASSET_TYPE_ALIASES[normalized]

    symbol = str(market_symbol or "").strip().upper()

    if symbol:
        if symbol.endswith("=X"):
            return ASSET_TYPE_FX

        crypto_quote_suffixes = (
            "-USD",
            "-USDT",
            "-EUR",
            "-TRY",
            "-GBP",
            "-JPY",
            "-BTC",
            "-ETH",
        )
        if symbol.endswith(crypto_quote_suffixes):
            return ASSET_TYPE_CRYPTO

        if symbol.endswith("=F"):
            return ASSET_TYPE_OTHER

    return ASSET_TYPE_STOCK


def get_market_calendar_config(
    asset_type: Optional[Any] = None,
    market_symbol: Optional[Any] = None,
) -> MarketCalendarConfig:
    """Varlık türüne uygun değiştirilemez takvim ayarını döndürür."""
    resolved_type = normalize_asset_type(
        asset_type=asset_type,
        market_symbol=market_symbol,
    )
    return _CONFIGS[resolved_type]


def build_forecast_dates(
    last_date: Any,
    periods: int,
    asset_type: Optional[Any] = None,
    market_symbol: Optional[Any] = None,
) -> pd.DatetimeIndex:
    """Varlık türüne göre gelecek tarih dizisi oluşturur."""
    periods = int(periods)

    if periods <= 0:
        raise ValueError("Tahmin tarihi için periyot sıfırdan büyük olmalıdır.")

    config = get_market_calendar_config(
        asset_type=asset_type,
        market_symbol=market_symbol,
    )
    start_date = pd.Timestamp(last_date)

    if config.date_frequency == "D":
        return pd.date_range(
            start=start_date + pd.Timedelta(days=1),
            periods=periods,
            freq="D",
        )

    return pd.bdate_range(
        start=start_date + pd.offsets.BDay(1),
        periods=periods,
    )


def get_standard_horizons(
    asset_type: Optional[Any] = None,
    market_symbol: Optional[Any] = None,
) -> Tuple[Tuple[str, int], ...]:
    """Varlık türü için standart vade etiketlerini döndürür."""
    return get_market_calendar_config(
        asset_type=asset_type,
        market_symbol=market_symbol,
    ).horizons
