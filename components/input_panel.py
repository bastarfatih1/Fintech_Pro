"""
Üst giriş paneli.

Bu bileşen yatırım tutarı, para birimi,
varlık ve projeksiyon vadesi seçimlerini yönetir.
"""

from dataclasses import dataclass
from typing import Mapping

import streamlit as st

from config.constants import CURRENCY_SYMBOLS
from config.markets import FORECAST_PERIODS, INSTRUMENTS


CURRENCY_OPTIONS = (
    "TRY",
    "USD",
    "EUR",
    "CNY",
    "RUB",
    "JPY",
    "SAR",
    "KWD",
)


@dataclass(frozen=True)
class InputSelection:
    """Kullanıcının üst panelde yaptığı seçimler."""

    investment_amount: float
    currency_code: str
    asset_name: str
    forecast_label: str
    forecast_days: int
    currency_symbol: str
    currency_rate: float
    market_symbol: str


def render_input_panel(
    currencies: Mapping[str, float],
) -> InputSelection:
    """
    Ana giriş kontrollerini gösterir ve seçilen değerleri döndürür.

    Args:
        currencies: Para birimi kodlarını dönüşüm oranlarına
            eşleyen sözlük.

    Returns:
        Kullanıcının seçimlerini içeren InputSelection nesnesi.
    """
    col_amount, col_currency, col_asset, col_period = st.columns(
        [2, 1, 1, 1]
    )

    investment_amount = col_amount.number_input(
        "Stratejik Yatırım Tutarı:",
        min_value=0.0,
        value=0.0,
        step=10000.0,
    )

    currency_code = col_currency.selectbox(
        "Baz Para Birimi:",
        list(CURRENCY_OPTIONS),
    )

    asset_name = col_asset.selectbox(
        "Analiz Edilecek Varlık:",
        list(INSTRUMENTS.keys()),
    )

    forecast_label = col_period.selectbox(
        "Projeksiyon Vadesi:",
        list(FORECAST_PERIODS.keys()),
        index=3,
    )

    currency_rate = float(currencies.get(currency_code, 1.0))
    currency_symbol = CURRENCY_SYMBOLS[currency_code]
    market_symbol = INSTRUMENTS[asset_name]
    forecast_days = int(FORECAST_PERIODS[forecast_label])

    return InputSelection(
        investment_amount=float(investment_amount),
        currency_code=currency_code,
        asset_name=asset_name,
        forecast_label=forecast_label,
        forecast_days=forecast_days,
        currency_symbol=currency_symbol,
        currency_rate=currency_rate,
        market_symbol=market_symbol,
    )
