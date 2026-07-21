from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class DiagnosticResult:
    section: str
    check: str
    status: str
    detail: str


def _status(ok: bool) -> str:
    return "GEÇTİ" if ok else "KALDI"


def _safe_numeric_series(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan)
    return values


def build_model_diagnostics(
    data: pd.DataFrame,
    forecast_days: int,
    market_symbol: str = "",
    asset_name: str = "",
) -> pd.DataFrame:
    results: list[DiagnosticResult] = []

    def add(section: str, check: str, ok: bool, detail: str) -> None:
        results.append(
            DiagnosticResult(
                section=section,
                check=check,
                status=_status(ok),
                detail=detail,
            )
        )

    if data is None or not isinstance(data, pd.DataFrame) or data.empty:
        add("Veri", "Piyasa verisi", False, "DataFrame boş veya hiç veri gelmedi.")
        return pd.DataFrame([r.__dict__ for r in results])

    add("Varlık", "Seçilen varlık", True, f"{asset_name} / {market_symbol}")

    row_count = len(data)
    add("Veri", "Toplam satır", row_count >= 80, f"{row_count} satır var. Minimum hedef: 80+")

    has_close = "Close" in data.columns
    add("Veri", "Close sütunu", has_close, "Close sütunu var." if has_close else "Close sütunu yok.")

    if not has_close:
        return pd.DataFrame([r.__dict__ for r in results])

    close_raw = _safe_numeric_series(data["Close"])
    close_valid = close_raw.dropna()
    close_valid = close_valid[close_valid > 0]

    missing_close = int(close_raw.isna().sum())
    invalid_close = int((close_raw <= 0).sum())

    add(
        "Veri",
        "Close NaN kontrolü",
        missing_close == 0,
        f"NaN Close sayısı: {missing_close}",
    )
    add(
        "Veri",
        "Close pozitiflik kontrolü",
        invalid_close == 0,
        f"Sıfır/negatif Close sayısı: {invalid_close}",
    )
    add(
        "Veri",
        "Geçerli Close sayısı",
        len(close_valid) >= 80,
        f"{len(close_valid)} geçerli pozitif Close var.",
    )

    if len(close_valid) > 0:
        add(
            "Veri",
            "Son geçerli fiyat",
            True,
            f"Son geçerli Close: {float(close_valid.iloc[-1]):.6f}",
        )

    if len(close_valid) < 80:
        return pd.DataFrame([r.__dict__ for r in results])

    df = data.copy()
    df["Close"] = close_raw
    df = df.dropna(subset=["Close"])
    df = df[df["Close"] > 0]

    df["Lag_1"] = df["Close"].shift(1)
    df["Lag_2"] = df["Close"].shift(2)
    df["Lag_3"] = df["Close"].shift(3)
    df["MA_14"] = df["Close"].rolling(window=14).mean()
    df["Vol_14"] = df["Close"].rolling(window=14).std()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    forecast_days = int(forecast_days or 1)
    df["Target"] = df["Close"].shift(-forecast_days)

    features = ["Lag_1", "Lag_2", "Lag_3", "MA_14", "Vol_14", "RSI"]

    model_df = df.dropna(subset=features + ["Target"]).copy()
    model_rows = len(model_df)

    add(
        "Feature",
        "Model eğitim satırı",
        model_rows >= 80,
        f"{model_rows} satır eğitim için uygun. Vade: {forecast_days}",
    )

    if model_rows > 0:
        feature_nan = int(model_df[features].isna().sum().sum())
        target_nan = int(model_df["Target"].isna().sum())
        add("Feature", "Feature NaN", feature_nan == 0, f"Feature NaN toplamı: {feature_nan}")
        add("Feature", "Target NaN", target_nan == 0, f"Target NaN toplamı: {target_nan}")

        target_var = float(model_df["Target"].var()) if model_rows > 1 else 0.0
        add(
            "Feature",
            "Target değişkenliği",
            np.isfinite(target_var) and target_var > 0,
            f"Target varyansı: {target_var:.8f}",
        )

    regression_ready = model_rows >= 80
    add("Model", "Linear Regression hazır mı?", regression_ready, "Yeterli eğitim satırı gerekir.")
    add("Model", "Random Forest hazır mı?", regression_ready, "Yeterli eğitim satırı gerekir.")
    add("Model", "SVR hazır mı?", regression_ready, "Yeterli eğitim satırı gerekir.")
    add("Model", "XGBoost hazır mı?", regression_ready, "Yeterli eğitim satırı gerekir.")

    returns = df["Close"].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    mc_ready = len(returns) >= 60 and np.isfinite(float(returns.std())) and float(returns.std()) > 0
    add(
        "Model",
        "Monte Carlo hazır mı?",
        mc_ready,
        f"Getiri satırı: {len(returns)}, volatilite: {float(returns.std()) if len(returns) else 0:.8f}",
    )

    arima_ready = len(close_valid) >= 120 and float(close_valid.var()) > 0
    add(
        "Model",
        "ARIMA hazır mı?",
        arima_ready,
        f"Geçerli Close: {len(close_valid)}, varyans: {float(close_valid.var()):.8f}",
    )

    return pd.DataFrame([r.__dict__ for r in results])


def diagnostics_has_failure(diagnostics: pd.DataFrame) -> bool:
    if diagnostics is None or diagnostics.empty:
        return True
    return bool((diagnostics["status"] == "KALDI").any())
