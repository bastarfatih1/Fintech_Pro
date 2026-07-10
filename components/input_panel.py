"""
Üst giriş paneli.

Bu bileşen yatırım tutarı, para birimi, varlık ve
varlık türüne uygun projeksiyon vadesi seçimlerini yönetir.
"""

from dataclasses import dataclass
from typing import Mapping

import streamlit as st

from config.constants import CURRENCY_SYMBOLS
from config.markets import INSTRUMENTS
from core.market_calendar import get_market_calendar_config


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
    asset_type: str
    calendar_name: str
    period_unit: str


def render_input_panel(
    currencies: Mapping[str, float],
) -> InputSelection:
    """
    Ana giriş kontrollerini gösterir ve seçilen değerleri döndürür.

    Vade seçenekleri seçilen varlığın piyasa takvimine göre hazırlanır:
    kriptoda takvim günü, hisse ve dövizde işlem günü kullanılır.
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

    market_symbol = INSTRUMENTS[asset_name]
    calendar_config = get_market_calendar_config(
        market_symbol=market_symbol,
    )

    period_options = {
        f"{label} — {days} {calendar_config.period_unit}": (
            label,
            days,
        )
        for label, days in calendar_config.horizons
    }

    period_display_label = col_period.selectbox(
        "Projeksiyon Vadesi:",
        list(period_options.keys()),
        index=min(3, len(period_options) - 1),
        help=(
            f"Takvim: {calendar_config.calendar_name}. "
            f"{calendar_config.calendar_note}"
        ),
    )

    forecast_label, forecast_days = period_options[
        period_display_label
    ]

    col_period.caption(
        f"{calendar_config.display_name} · "
        f"{calendar_config.calendar_name}"
    )

    currency_rate = float(currencies.get(currency_code, 1.0))
    currency_symbol = CURRENCY_SYMBOLS[currency_code]

    return InputSelection(
        investment_amount=float(investment_amount),
        currency_code=currency_code,
        asset_name=asset_name,
        forecast_label=forecast_label,
        forecast_days=int(forecast_days),
        currency_symbol=currency_symbol,
        currency_rate=currency_rate,
        market_symbol=market_symbol,
        asset_type=calendar_config.asset_type,
        calendar_name=calendar_config.calendar_name,
        period_unit=calendar_config.period_unit,
    )
