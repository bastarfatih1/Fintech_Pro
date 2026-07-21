from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm

from services.factor_matrix_engine import (
    build_factor_matrix,
    normalize_index,
    safe_close,
)


@dataclass(frozen=True)
class HorizonSpec:
    label: str
    days: int
    group: str
    max_windows: int
    min_train_rows: int


HORIZON_SPECS = [
    HorizonSpec("1 Hafta", 5, "Kısa Vade", 120, 252),
    HorizonSpec("1 Ay", 20, "Kısa Vade", 120, 252),
    HorizonSpec("3 Ay", 60, "Kısa Vade", 80, 378),
    HorizonSpec("6 Ay", 126, "Kısa Vade", 60, 504),
    HorizonSpec("1 Yıl", 252, "Orta Vade", 40, 756),
    HorizonSpec("3 Yıl", 756, "Uzun Vade", 20, 1008),
    HorizonSpec("5 Yıl", 1260, "Uzun Vade", 10, 1260),
]


def _drop_highly_correlated_features(
    x: pd.DataFrame,
    threshold: float = 0.98,
) -> tuple[pd.DataFrame, list[str]]:
    if x.empty or x.shape[1] <= 1:
        return x, []

    corr = x.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    drop_cols = [
        col for col in upper.columns
        if any(upper[col] > threshold)
    ]

    if drop_cols:
        return x.drop(columns=drop_cols), drop_cols

    return x, []


def _rmse(predicted: np.ndarray, actual: np.ndarray) -> float:
    predicted = np.asarray(predicted, dtype=float)
    actual = np.asarray(actual, dtype=float)
    return float(np.sqrt(np.mean((predicted - actual) ** 2)))




def _mape(predicted: np.ndarray, actual: np.ndarray) -> float:
    predicted = np.asarray(predicted, dtype=float)
    actual = np.asarray(actual, dtype=float)

    mask = np.isfinite(predicted) & np.isfinite(actual) & (actual != 0)

    if mask.sum() == 0:
        return float("nan")

    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100.0)


def _direction_accuracy(
    predicted: np.ndarray,
    actual: np.ndarray,
    start: np.ndarray,
) -> float:
    predicted = np.asarray(predicted, dtype=float)
    actual = np.asarray(actual, dtype=float)
    start = np.asarray(start, dtype=float)

    pred_dir = np.sign(predicted - start)
    actual_dir = np.sign(actual - start)

    return float(np.mean(pred_dir == actual_dir) * 100.0)


def _safe_float(value: Any, default: float = np.nan) -> float:
    try:
        value = float(value)
        if np.isfinite(value):
            return value
    except Exception:
        pass
    return default


def _evaluate_one_horizon(
    target_data: pd.DataFrame,
    market_symbol: str,
    asset_name: str,
    asset_type: str | None,
    spec: HorizonSpec,
) -> dict[str, Any]:
    matrix = build_factor_matrix(
        target_data=target_data,
        forecast_days=spec.days,
        market_symbol=market_symbol,
        asset_name=asset_name,
        asset_type=asset_type,
        period="10y",
    )

    dataset = matrix["dataset"].copy()
    feature_columns = list(matrix["feature_columns"])
    target_column = matrix["target_column"]

    if len(feature_columns) < 2:
        raise ValueError("Yeterli faktör yok.")

    close = safe_close(normalize_index(target_data))
    close = close.reindex(dataset.index).dropna()

    dataset = dataset.loc[
        dataset.index.intersection(close.index)
    ].copy()

    if len(dataset) < spec.min_train_rows + 20:
        raise ValueError(
            f"Yetersiz gözlem. Mevcut: {len(dataset)}, gerekli: {spec.min_train_rows + 20}+"
        )

    log_returns = np.log(close / close.shift(1)).replace(
        [np.inf, -np.inf],
        np.nan,
    )

    start_index = max(
        spec.min_train_rows,
        len(dataset) - spec.max_windows,
    )

    ols_predicted = []
    actual_prices = []
    start_prices = []

    no_change_predicted = []
    drift_predicted = []
    ma_predicted = []

    dropped_feature_counter = set()

    for i in range(start_index, len(dataset)):
        train = dataset.iloc[:i].copy()
        test_row = dataset.iloc[[i]].copy()
        test_date = test_row.index[0]

        if test_date not in close.index:
            continue

        y_train = train[target_column].astype(float)
        x_train = train[feature_columns].astype(float)

        x_train, dropped_cols = _drop_highly_correlated_features(x_train)

        for col in dropped_cols:
            dropped_feature_counter.add(col)

        if x_train.shape[1] < 2:
            continue

        x_const = sm.add_constant(x_train, has_constant="add")
        model = sm.OLS(y_train, x_const).fit()

        x_test = test_row[x_train.columns].astype(float)
        x_test_const = sm.add_constant(x_test, has_constant="add")

        pred_return = _safe_float(model.predict(x_test_const).iloc[0])
        actual_return = _safe_float(test_row[target_column].iloc[0])

        start_price = _safe_float(close.loc[test_date])

        if not (
            np.isfinite(pred_return)
            and np.isfinite(actual_return)
            and np.isfinite(start_price)
            and start_price > 0
        ):
            continue

        actual_price = start_price * float(np.exp(actual_return))
        ols_price = start_price * float(np.exp(pred_return))

        past_returns = log_returns.loc[:test_date].dropna().iloc[-252:]

        if len(past_returns) >= 20:
            drift_mu = float(past_returns.mean())
            drift_price = start_price * float(np.exp(drift_mu * spec.days))
        else:
            drift_price = start_price

        past_close = close.loc[:test_date].dropna()

        if len(past_close) >= 20:
            ma_price = float(past_close.rolling(20).mean().iloc[-1])
        else:
            ma_price = start_price

        if not (
            np.isfinite(actual_price)
            and np.isfinite(ols_price)
            and np.isfinite(drift_price)
            and np.isfinite(ma_price)
            and actual_price > 0
            and ols_price > 0
            and drift_price > 0
            and ma_price > 0
        ):
            continue

        start_prices.append(start_price)
        actual_prices.append(actual_price)
        ols_predicted.append(ols_price)

        no_change_predicted.append(start_price)
        drift_predicted.append(drift_price)
        ma_predicted.append(ma_price)

    if len(ols_predicted) < 10:
        raise ValueError(
            f"Geçerli test üretilemedi. Geçerli test sayısı: {len(ols_predicted)}"
        )

    start_arr = np.asarray(start_prices, dtype=float)
    actual_arr = np.asarray(actual_prices, dtype=float)

    ols_arr = np.asarray(ols_predicted, dtype=float)
    no_change_arr = np.asarray(no_change_predicted, dtype=float)
    drift_arr = np.asarray(drift_predicted, dtype=float)
    ma_arr = np.asarray(ma_predicted, dtype=float)

    ols_rmse = _rmse(ols_arr, actual_arr)

    benchmark_rmses = {
        "No_Change_Benchmark": _rmse(no_change_arr, actual_arr),
        "Historical_Drift_Benchmark": _rmse(drift_arr, actual_arr),
        "Moving_Average_Benchmark": _rmse(ma_arr, actual_arr),
    }

    best_benchmark_name = min(
        benchmark_rmses,
        key=lambda key: benchmark_rmses[key],
    )
    best_benchmark_rmse = benchmark_rmses[best_benchmark_name]

    passed_benchmarks = [
        name for name, rmse in benchmark_rmses.items()
        if ols_rmse < rmse
    ]

    passed_benchmark_rmses = {
        name: rmse for name, rmse in benchmark_rmses.items()
        if ols_rmse < rmse
    }

    if passed_benchmark_rmses:
        strongest_passed_benchmark = min(
            passed_benchmark_rmses,
            key=lambda key: passed_benchmark_rmses[key],
        )
        strongest_passed_rmse = passed_benchmark_rmses[strongest_passed_benchmark]
        strongest_passed_improvement = (
            (strongest_passed_rmse - ols_rmse) / strongest_passed_rmse * 100.0
            if strongest_passed_rmse > 0
            else np.nan
        )
    else:
        strongest_passed_benchmark = "-"
        strongest_passed_improvement = np.nan

    absolute_best_gap = (
        (ols_rmse - best_benchmark_rmse) / best_benchmark_rmse * 100.0
        if best_benchmark_rmse > 0
        else np.nan
    )

    ols_mape = _mape(ols_arr, actual_arr)
    no_change_mape = _mape(no_change_arr, actual_arr)
    drift_mape = _mape(drift_arr, actual_arr)
    ma_mape = _mape(ma_arr, actual_arr)

    passed_count = len(passed_benchmarks)
    total_benchmarks = len(benchmark_rmses)

    if passed_count == total_benchmarks:
        horizon_success = "Güçlü"
    elif passed_count >= 1:
        horizon_success = "Kısmi"
    else:
        horizon_success = "Hayır"

    best_improvement = (
        (best_benchmark_rmse - ols_rmse) / best_benchmark_rmse * 100.0
        if best_benchmark_rmse > 0
        else np.nan
    )

    direction_accuracy = _direction_accuracy(
        predicted=ols_arr,
        actual=actual_arr,
        start=start_arr,
    )

    return {
        "Vade": spec.label,
        "Vade Grubu": spec.group,
        "Gün": spec.days,
        "Model": "Multi_Factor_OLS",
        "Model RMSE": round(ols_rmse, 2),
        "Model MAPE %": round(ols_mape, 2),
        "Mutlak En İyi Benchmark": best_benchmark_name,
        "Mutlak En İyi Benchmark RMSE": round(best_benchmark_rmse, 2),
        "Mutlak En İyi Benchmarktan Fark %": round(absolute_best_gap, 2),
        "Geçebildiği En Güçlü Benchmark": strongest_passed_benchmark,
        "Geçilen En Güçlü Benchmarka Göre İyileşme %": round(strongest_passed_improvement, 2) if np.isfinite(strongest_passed_improvement) else np.nan,
        "En İyi Benchmark": best_benchmark_name,
        "En İyi Benchmark RMSE": round(best_benchmark_rmse, 2),
        "En İyi Benchmarka Göre İyileşme %": round(best_improvement, 2),
        "Geçtiği Benchmark": passed_count,
        "Toplam Benchmark": total_benchmarks,
        "Vade Başarısı": horizon_success,
        "Yön Doğruluğu %": round(direction_accuracy, 1),
        "Test Gözlemi": int(len(ols_predicted)),
        "No Change RMSE": round(benchmark_rmses["No_Change_Benchmark"], 2),
        "Historical Drift RMSE": round(benchmark_rmses["Historical_Drift_Benchmark"], 2),
        "Moving Average RMSE": round(benchmark_rmses["Moving_Average_Benchmark"], 2),
        "No Change MAPE %": round(no_change_mape, 2),
        "Historical Drift MAPE %": round(drift_mape, 2),
        "Moving Average MAPE %": round(ma_mape, 2),
        "Çıkarılan Korelasyonlu Faktör": ", ".join(sorted(dropped_feature_counter)) or "-",
    }


def build_horizon_validation_report(
    target_data: pd.DataFrame,
    market_symbol: str,
    asset_name: str,
    asset_type: str | None = None,
) -> dict[str, pd.DataFrame]:
    rows = []
    diagnostics = []

    for spec in HORIZON_SPECS:
        try:
            row = _evaluate_one_horizon(
                target_data=target_data,
                market_symbol=market_symbol,
                asset_name=asset_name,
                asset_type=asset_type,
                spec=spec,
            )
            rows.append(row)
            diagnostics.append({
                "Vade": spec.label,
                "Durum": "GEÇTİ",
                "Detay": "Vade bazlı çoklu benchmark testi üretildi.",
            })
        except Exception as exc:
            detail = str(exc)
            detail_lower = detail.lower()

            if "yetersiz" in detail_lower or "gözlem" in detail_lower or "veri" in detail_lower:
                status = "VERİ YETERSİZ"
            else:
                status = "HESAPLANAMADI"

            diagnostics.append({
                "Vade": spec.label,
                "Durum": status,
                "Detay": detail,
            })

    return {
        "summary": pd.DataFrame(rows),
        "diagnostics": pd.DataFrame(diagnostics),
    }
