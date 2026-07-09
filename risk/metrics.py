"""
Profesyonel risk metrikleri.

Bu modül fiyat serisinden günlük ve yıllıklaştırılmış
risk ölçümlerini hesaplar.
"""

from typing import Dict

import numpy as np
import pandas as pd


TRADING_DAYS = 252


def _prepare_returns(close_prices: pd.Series) -> pd.Series:
    """Kapanış fiyatlarından temiz günlük getiri serisi üretir."""
    if close_prices is None:
        raise ValueError("Kapanış fiyatları bulunamadı.")

    prices = pd.to_numeric(close_prices, errors="coerce").dropna()

    if len(prices) < 30:
        raise ValueError(
            "Risk hesaplamak için en az 30 geçerli fiyat gerekir."
        )

    returns = prices.pct_change().replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    if returns.empty:
        raise ValueError("Geçerli getiri serisi oluşturulamadı.")

    return returns


def calculate_max_drawdown(close_prices: pd.Series) -> float:
    """
    En büyük zirve-dip kaybını pozitif oran olarak döndürür.

    Örnek:
        %25 maksimum düşüş için 0.25 döndürür.
    """
    prices = pd.to_numeric(close_prices, errors="coerce").dropna()

    running_peak = prices.cummax()
    drawdowns = prices / running_peak - 1.0

    return abs(float(drawdowns.min()))


def calculate_var(
    returns: pd.Series,
    confidence: float = 0.95,
) -> float:
    """
    Tarihsel VaR değerini pozitif kayıp oranı olarak döndürür.
    """
    if not 0 < confidence < 1:
        raise ValueError("Güven seviyesi 0 ile 1 arasında olmalıdır.")

    percentile = (1.0 - confidence) * 100
    quantile_return = float(np.percentile(returns, percentile))

    return max(0.0, -quantile_return)


def calculate_cvar(
    returns: pd.Series,
    confidence: float = 0.95,
) -> float:
    """
    VaR sınırını aşan günlerdeki ortalama kaybı hesaplar.
    """
    var_loss = calculate_var(returns, confidence)
    tail_returns = returns[returns <= -var_loss]

    if tail_returns.empty:
        return var_loss

    return max(0.0, -float(tail_returns.mean()))


def calculate_sharpe(
    returns: pd.Series,
    annual_risk_free_rate: float = 0.0,
) -> float:
    """Yıllıklandırılmış Sharpe oranını hesaplar."""
    daily_risk_free = (
        (1.0 + annual_risk_free_rate) ** (1.0 / TRADING_DAYS)
        - 1.0
    )

    excess_returns = returns - daily_risk_free
    volatility = float(excess_returns.std(ddof=1))

    if volatility <= 1e-12:
        return 0.0

    return float(
        excess_returns.mean()
        / volatility
        * np.sqrt(TRADING_DAYS)
    )


def calculate_sortino(
    returns: pd.Series,
    annual_risk_free_rate: float = 0.0,
) -> float:
    """Yalnızca aşağı yönlü riski kullanan Sortino oranını hesaplar."""
    daily_risk_free = (
        (1.0 + annual_risk_free_rate) ** (1.0 / TRADING_DAYS)
        - 1.0
    )

    excess_returns = returns - daily_risk_free
    downside_returns = np.minimum(excess_returns, 0.0)
    downside_deviation = float(
        np.sqrt(np.mean(np.square(downside_returns)))
    )

    if downside_deviation <= 1e-12:
        return 0.0

    return float(
        excess_returns.mean()
        / downside_deviation
        * np.sqrt(TRADING_DAYS)
    )


def calculate_annualized_volatility(
    returns: pd.Series,
) -> float:
    """Yıllıklandırılmış volatiliteyi hesaplar."""
    return float(
        returns.std(ddof=1) * np.sqrt(TRADING_DAYS)
    )


def calculate_risk_metrics(
    close_prices: pd.Series,
    annual_risk_free_rate: float = 0.0,
) -> Dict[str, float]:
    """Uygulamanın kullandığı temel risk metriklerini üretir."""
    returns = _prepare_returns(close_prices)

    return {
        "VaR": calculate_var(returns, confidence=0.95),
        "CVaR": calculate_cvar(returns, confidence=0.95),
        "Sharpe": calculate_sharpe(
            returns,
            annual_risk_free_rate,
        ),
        "Sortino": calculate_sortino(
            returns,
            annual_risk_free_rate,
        ),
        "MaxDD": calculate_max_drawdown(close_prices),
        "Volatility": calculate_annualized_volatility(returns),
    }