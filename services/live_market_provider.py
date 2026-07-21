"""Live multi-provider market data layer for Fintech Pro.

Provider priority:
1) Twelve Data
2) Finnhub
3) CoinGecko for crypto
4) Alpha Vantage
5) Existing app fallback

This module never stores API keys. It reads them from Streamlit secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pandas as pd
import requests
import streamlit as st

GRAMS_PER_TROY_OUNCE = 31.1034768
REQUEST_TIMEOUT = 8


@dataclass
class LiveQuote:
    symbol: str
    price: float
    previous_close: Optional[float] = None
    change_percent: Optional[float] = None
    source: str = ""
    timestamp: str = ""

    @property
    def is_valid(self) -> bool:
        return self.price is not None and self.price > 0


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        return default
    if value is None:
        return default
    return str(value).strip()


def _live_enabled() -> bool:
    provider = _secret("MARKET_DATA_PROVIDER", "").lower()
    return provider in {"live", "twelvedata", "finnhub", "coingecko", "alpha_vantage"}


def _as_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        text = str(value).replace("%", "").replace(",", ".").strip()
        if text == "":
            return None
        return float(text)
    except Exception:
        return None


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _crypto_id(symbol: str) -> Optional[str]:
    s = symbol.upper().replace("/", "-").replace("_", "-")
    mapping = {
        "BTC-USD": "bitcoin",
        "BTCUSD": "bitcoin",
        "BTC": "bitcoin",
        "ETH-USD": "ethereum",
        "ETHUSD": "ethereum",
        "ETH": "ethereum",
        "BNB-USD": "binancecoin",
        "SOL-USD": "solana",
        "XRP-USD": "ripple",
        "DOGE-USD": "dogecoin",
        "ADA-USD": "cardano",
    }
    return mapping.get(s)


def _td_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    mapping = {
        "USDTRY=X": "USD/TRY",
        "EURTRY=X": "EUR/TRY",
        "EURUSD=X": "EUR/USD",
        "GBPUSD=X": "GBP/USD",
        "GC=F": "XAU/USD",
        "SI=F": "XAG/USD",
        "BTC-USD": "BTC/USD",
        "ETH-USD": "ETH/USD",
    }
    return mapping.get(s, symbol)


def _finnhub_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    mapping = {
        "USDTRY=X": "OANDA:USD_TRY",
        "EURTRY=X": "OANDA:EUR_TRY",
        "EURUSD=X": "OANDA:EUR_USD",
        "GBPUSD=X": "OANDA:GBP_USD",
        "GC=F": "OANDA:XAU_USD",
        "SI=F": "OANDA:XAG_USD",
        "BTC-USD": "BINANCE:BTCUSDT",
        "ETH-USD": "BINANCE:ETHUSDT",
    }
    return mapping.get(s, symbol)


def _twelve_quote(symbol: str) -> Optional[LiveQuote]:
    key = _secret("TWELVE_DATA_API_KEY")
    if not key:
        return None

    td_symbol = _td_symbol(symbol)
    try:
        response = requests.get(
            "https://api.twelvedata.com/quote",
            params={"symbol": td_symbol, "apikey": key},
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
    except Exception:
        return None

    if not isinstance(data, dict) or data.get("status") == "error" or data.get("code"):
        return None

    price = _as_float(data.get("close") or data.get("price"))
    previous = _as_float(data.get("previous_close") or data.get("previous_close_price"))
    pct = _as_float(data.get("percent_change"))

    if not price:
        return None

    return LiveQuote(td_symbol, price, previous, pct, "Twelve Data live quote", data.get("datetime") or _now_label())


def _finnhub_quote(symbol: str) -> Optional[LiveQuote]:
    key = _secret("FINNHUB_API_KEY")
    if not key:
        return None

    fh_symbol = _finnhub_symbol(symbol)
    try:
        response = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={"symbol": fh_symbol, "token": key},
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    price = _as_float(data.get("c"))
    previous = _as_float(data.get("pc"))
    pct = _as_float(data.get("dp"))

    if not price:
        return None

    return LiveQuote(fh_symbol, price, previous, pct, "Finnhub live quote", _now_label())


def _coingecko_quote(symbol: str) -> Optional[LiveQuote]:
    coin_id = _crypto_id(symbol)
    if not coin_id:
        return None

    key = _secret("COINGECKO_API_KEY")
    headers = {}
    if key:
        headers["x-cg-demo-api-key"] = key

    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
    except Exception:
        return None

    item = data.get(coin_id) if isinstance(data, dict) else None
    if not isinstance(item, dict):
        return None

    price = _as_float(item.get("usd"))
    pct = _as_float(item.get("usd_24h_change"))
    previous = None
    if price and pct is not None and pct != -100:
        previous = price / (1 + pct / 100)

    if not price:
        return None

    return LiveQuote(coin_id, price, previous, pct, "CoinGecko crypto quote", _now_label())


def _alpha_quote(symbol: str) -> Optional[LiveQuote]:
    key = _secret("ALPHA_VANTAGE_API_KEY")
    if not key:
        return None

    alpha_symbol = symbol.upper().replace("-USD", "").strip()
    if symbol.upper().endswith("=X"):
        return None

    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": alpha_symbol, "apikey": key},
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
    except Exception:
        return None

    quote = data.get("Global Quote") if isinstance(data, dict) else None
    if not isinstance(quote, dict) or not quote:
        return None

    price = _as_float(quote.get("05. price"))
    previous = _as_float(quote.get("08. previous close"))
    pct = _as_float(quote.get("10. change percent"))

    if not price:
        return None

    return LiveQuote(alpha_symbol, price, previous, pct, "Alpha Vantage global quote", quote.get("07. latest trading day") or _now_label())


def _gram_altin_try_quote() -> Optional[LiveQuote]:
    """Compute TRY gram gold from live XAU/USD and USD/TRY quotes."""
    xau = _twelve_quote("GC=F") or _finnhub_quote("GC=F")
    usdtry = _twelve_quote("USDTRY=X") or _finnhub_quote("USDTRY=X")

    if not xau or not usdtry or not xau.price or not usdtry.price:
        return None

    price = xau.price * usdtry.price / GRAMS_PER_TROY_OUNCE
    previous = None
    if xau.previous_close and usdtry.previous_close:
        previous = xau.previous_close * usdtry.previous_close / GRAMS_PER_TROY_OUNCE

    pct = None
    if previous and previous > 0:
        pct = ((price - previous) / previous) * 100

    return LiveQuote(
        "GRAM_ALTIN_TRY",
        price,
        previous,
        pct,
        f"Live derived gram gold ({xau.source} + {usdtry.source})",
        _now_label(),
    )


def get_live_quote(symbol: str) -> Optional[LiveQuote]:
    """Return best available live quote for a market symbol."""
    if not _live_enabled():
        return None

    if symbol == "GRAM_ALTIN_TRY":
        return _gram_altin_try_quote()

    crypto = _coingecko_quote(symbol)
    if crypto:
        return crypto

    for provider in (_twelve_quote, _finnhub_quote, _alpha_quote):
        quote = provider(symbol)
        if quote and quote.is_valid:
            return quote

    return None


def apply_live_quote_to_history(data: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Canlı quote geldiyse OHLC geçmiş verisinin son satırını güncel fiyatla,
    bir önceki satırını da önceki kapanışla günceller.
    """
    quote = get_live_quote(symbol)

    if quote is None or data is None or data.empty:
        return data

    fixed = data.copy()

    if "Close" not in fixed.columns:
        return data

    last_idx = fixed.index[-1]
    fixed.loc[last_idx, "Close"] = float(quote.price)

    for col in ["Open", "High", "Low"]:
        if col in fixed.columns:
            fixed.loc[last_idx, col] = float(quote.price)

    if len(fixed) >= 2 and quote.previous_close is not None:
        prev_idx = fixed.index[-2]
        fixed.loc[prev_idx, "Close"] = float(quote.previous_close)

        for col in ["Open", "High", "Low"]:
            if col in fixed.columns:
                fixed.loc[prev_idx, col] = float(quote.previous_close)

    return fixed

