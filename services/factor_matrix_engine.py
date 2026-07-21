from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from config.factor_catalog import FactorSpec, get_factor_specs
from core.market_calendar import normalize_asset_type
from services.data_provider import get_market_history


def normalize_index(data: pd.DataFrame) -> pd.DataFrame:
    fixed = data.copy()
    fixed.index = pd.to_datetime(fixed.index, errors="coerce")

    try:
        fixed.index = fixed.index.tz_localize(None)
    except TypeError:
        pass

    fixed.index = fixed.index.normalize()
    fixed = fixed[~fixed.index.duplicated(keep="last")]
    return fixed.sort_index()


def safe_close(data: pd.DataFrame) -> pd.Series:
    if data is None or data.empty or "Close" not in data.columns:
        return pd.Series(dtype=float)

    close = pd.to_numeric(data["Close"], errors="coerce")
    close = close.replace([np.inf, -np.inf], np.nan)
    close = close.dropna()
    close = close[close > 0]
    return close.sort_index()


def log_return_from_close(close: pd.Series, name: str) -> pd.Series:
    if close is None or close.empty:
        return pd.Series(dtype=float, name=name)

    ret = np.log(close / close.shift(1))
    ret = ret.replace([np.inf, -np.inf], np.nan).dropna()
    ret.name = name
    return ret


def fetch_factor_history(symbol: str, period: str = "10y") -> pd.DataFrame:
    asset_type = normalize_asset_type(market_symbol=symbol)

    result = get_market_history(
        symbol=symbol,
        period=period,
        asset_type=asset_type,
    )

    if result.is_empty:
        return pd.DataFrame()

    return normalize_index(result.data)


def build_target_features(
    target_data: pd.DataFrame,
    forecast_days: int,
) -> pd.DataFrame:
    target = normalize_index(target_data)
    close = safe_close(target)

    if close.empty:
        raise ValueError("Hedef varlık için geçerli Close verisi yok.")

    frame = pd.DataFrame(index=close.index)
    frame["target_return_1d"] = log_return_from_close(close, "target_return_1d")
    frame["target_momentum_5d"] = np.log(close / close.shift(5))
    frame["target_momentum_20d"] = np.log(close / close.shift(20))
    frame["target_volatility_20d"] = frame["target_return_1d"].rolling(20).std()
    frame["target_future_return"] = np.log(close.shift(-int(forecast_days)) / close)

    if "Volume" in target.columns:
        volume = pd.to_numeric(target["Volume"], errors="coerce")
        volume = volume.replace([np.inf, -np.inf], np.nan)
        frame["target_volume_change_20d"] = np.log((volume + 1) / (volume.shift(20) + 1))
    else:
        frame["target_volume_change_20d"] = 0.0

    return frame


def build_factor_matrix(
    target_data: pd.DataFrame,
    forecast_days: int,
    market_symbol: str,
    asset_name: str,
    asset_type: str | None = None,
    period: str = "10y",
) -> dict[str, Any]:
    diagnostics: list[dict[str, Any]] = []
    factor_series: list[pd.Series] = []

    base = build_target_features(
        target_data=target_data,
        forecast_days=forecast_days,
    )

    specs = get_factor_specs(
        market_symbol=market_symbol,
        asset_type=asset_type,
    )

    for spec in specs:
        try:
            factor_data = fetch_factor_history(spec.symbol, period=period)

            if factor_data.empty:
                diagnostics.append({
                    "Faktör": spec.name,
                    "Sembol": spec.symbol,
                    "Grup": spec.group,
                    "Durum": "KALDI",
                    "Detay": "Veri sağlayıcıdan veri gelmedi.",
                })
                continue

            close = safe_close(factor_data)
            ret = log_return_from_close(close, spec.name)

            if ret.empty:
                diagnostics.append({
                    "Faktör": spec.name,
                    "Sembol": spec.symbol,
                    "Grup": spec.group,
                    "Durum": "KALDI",
                    "Detay": "Geçerli getiri serisi üretilemedi.",
                })
                continue

            factor_series.append(ret)
            diagnostics.append({
                "Faktör": spec.name,
                "Sembol": spec.symbol,
                "Grup": spec.group,
                "Durum": "GEÇTİ",
                "Detay": f"{len(ret)} getiri satırı alındı.",
            })
        except Exception as exc:
            diagnostics.append({
                "Faktör": spec.name,
                "Sembol": spec.symbol,
                "Grup": spec.group,
                "Durum": "KALDI",
                "Detay": str(exc),
            })

    if factor_series:
        factors = pd.concat(factor_series, axis=1)
        dataset = base.join(factors, how="inner")
    else:
        dataset = base.copy()

    dataset = dataset.replace([np.inf, -np.inf], np.nan).dropna()

    feature_columns = [
        col for col in dataset.columns
        if col != "target_future_return"
    ]

    return {
        "asset_name": asset_name,
        "market_symbol": market_symbol,
        "dataset": dataset,
        "feature_columns": feature_columns,
        "target_column": "target_future_return",
        "factor_diagnostics": pd.DataFrame(diagnostics),
        "factor_specs": specs,
    }
