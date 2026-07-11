"""
Üst giriş paneli.

Bu bileşen yatırım tutarı, para birimi, varlık ve
varlık türüne uygun projeksiyon vadesi seçimlerini yönetir.
"""

from dataclasses import dataclass
from typing import Mapping

import streamlit as st

from config.constants import CURRENCY_SYMBOLS
from config.markets import INSTRUMENTS as BASE_INSTRUMENTS
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

INSTRUMENTS = {"Gram Altın (TRY)": "GRAM_ALTIN_TRY"}
for _asset_name, _market_symbol in BASE_INSTRUMENTS.items():
    INSTRUMENTS.setdefault(_asset_name, _market_symbol)


def _format_turkish_amount(value: float) -> str:
    """1000000.5 değerini 1.000.000,50 biçiminde gösterir."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0

    formatted = f"{number:,.2f}"
    return (
        formatted
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )


def _parse_turkish_amount(raw_value: str) -> float:
    """1.000.000,50 veya 1000000.50 metnini güvenli float'a çevirir."""
    text = str(raw_value or "").strip()

    if not text:
        return 0.0

    cleaned = (
        text
        .replace("₺", "")
        .replace("$", "")
        .replace("€", "")
        .replace(" ", "")
    )

    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(".", "")

    try:
        return max(float(cleaned), 0.0)
    except ValueError:
        return 0.0


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

    amount_text = col_amount.text_input(
        "Stratejik Yatırım Tutarı:",
        value=st.session_state.get("investment_amount_display", ""),
        key="investment_amount_display",
        placeholder="Örn: 1.000,00",
        help="Örnek yazım: 1.000,00 veya 250.000,50",
    )
    investment_amount = _parse_turkish_amount(amount_text)

    currency_code = col_currency.selectbox(
        "Baz Para Birimi:",
        list(CURRENCY_OPTIONS),
    )

    asset_name = col_asset.selectbox(
        "Analiz Edilecek Varlık:",
        list(INSTRUMENTS.keys()),
    )

    market_symbol = INSTRUMENTS[asset_name]

    if market_symbol == "GRAM_ALTIN_TRY":
        calendar_config = get_market_calendar_config(
            asset_type="fx",
            market_symbol=market_symbol,
        )
        effective_asset_type = "fx"
    else:
        calendar_config = get_market_calendar_config(
            market_symbol=market_symbol,
        )
        effective_asset_type = calendar_config.asset_type

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

    if market_symbol == "GRAM_ALTIN_TRY":
        col_period.caption(
            "Gram Altın · TRY bazlı yaklaşık veri · hafta içi işlem günü"
        )
    else:
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
        asset_type=effective_asset_type,
        calendar_name=calendar_config.calendar_name,
        period_unit=calendar_config.period_unit,
    )
