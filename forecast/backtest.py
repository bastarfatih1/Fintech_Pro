"""
Zaman sıralı model doğrulama yardımcıları.

Bu modül veriyi karıştırmadan eğitim ve test bölümlerine ayırır.
Böylece modeller yalnızca geçmiş veriden öğrenir ve daha sonraki
dönem üzerinde değerlendirilir.
"""

from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor
from statsmodels.tsa.arima.model import ARIMA


def _build_models() -> Dict[str, object]:
    """Backtest için kullanılan model örneklerini oluşturur."""
    return {
        "Linear_Regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("model", LinearRegression()),
            ]
        ),
        "Random_Forest": RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
        ),
        "SVR": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("model", SVR(C=1.0, epsilon=0.2)),
            ]
        ),
        "XGBoost": XGBRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42,
            n_jobs=-1,
            objective="reg:squarederror",
        ),
    }


def _chronological_split(
    data: pd.DataFrame,
    test_ratio: float,
    minimum_train_size: int,
    minimum_test_size: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Veriyi zaman sırasını bozmadan eğitim ve test olarak ayırır."""
    if not 0.05 <= test_ratio <= 0.50:
        raise ValueError("Test oranı 0.05 ile 0.50 arasında olmalıdır.")

    total_rows = len(data)

    if total_rows < minimum_train_size + minimum_test_size:
        raise ValueError(
            "Backtest için yeterli veri yok. "
            f"En az {minimum_train_size + minimum_test_size} satır gerekir."
        )

    calculated_test_size = int(round(total_rows * test_ratio))
    test_size = max(minimum_test_size, calculated_test_size)
    test_size = min(test_size, total_rows - minimum_train_size)

    split_index = total_rows - test_size

    train_data = data.iloc[:split_index].copy()
    test_data = data.iloc[split_index:].copy()

    return train_data, test_data


def _direction_accuracy(
    actual_values: np.ndarray,
    predicted_values: np.ndarray,
    reference_values: np.ndarray,
) -> float:
    """
    Tahmin edilen fiyat yönünün gerçekleşen yönle uyuşma oranını hesaplar.
    """
    actual_direction = np.sign(actual_values - reference_values)
    predicted_direction = np.sign(predicted_values - reference_values)

    matches = actual_direction == predicted_direction

    return float(np.mean(matches) * 100.0)


def _build_expanding_folds(
    total_rows: int,
    minimum_train_size: int,
    minimum_test_size: int,
    maximum_folds: int,
) -> List[Tuple[int, int]]:
    """Genişleyen pencere için eğitim bitişlerini ve test bitişlerini üretir."""
    if maximum_folds < 2:
        raise ValueError("Walk-forward için en az 2 pencere gerekir.")

    available_test_rows = total_rows - minimum_train_size

    if available_test_rows < minimum_test_size:
        raise ValueError(
            "Walk-forward backtesti için yeterli test verisi yok."
        )

    fold_count = min(
        maximum_folds,
        max(2, available_test_rows // minimum_test_size),
    )

    test_block_size = max(
        minimum_test_size,
        available_test_rows // fold_count,
    )

    folds: List[Tuple[int, int]] = []
    train_end = minimum_train_size

    while train_end < total_rows and len(folds) < fold_count:
        test_end = min(train_end + test_block_size, total_rows)

        if test_end - train_end < minimum_test_size:
            break

        folds.append((train_end, test_end))
        train_end = test_end

    if len(folds) < 2:
        raise ValueError(
            "Walk-forward için en az iki geçerli pencere oluşturulamadı."
        )

    return folds


def _calculate_stability_score(
    rmse_mean: float,
    rmse_std: float,
    direction_mean: float,
    direction_std: float,
) -> float:
    """Hata ve yön sapmasına göre 0-100 arası stabilite skoru üretir."""
    rmse_cv = rmse_std / max(rmse_mean, 1e-12)
    rmse_stability = 1.0 / (1.0 + rmse_cv)

    direction_consistency = 1.0 - min(direction_std / 50.0, 1.0)
    direction_quality = float(np.clip(direction_mean / 50.0, 0.0, 1.0))

    score = (
        0.55 * rmse_stability
        + 0.25 * direction_consistency
        + 0.20 * direction_quality
    ) * 100.0

    return float(np.clip(score, 0.0, 100.0))


def evaluate_regression_models(
    data: pd.DataFrame,
    features: List[str],
    target_column: str = "Target",
    reference_column: str = "Close",
    minimum_train_size: int = 80,
    minimum_test_size: int = 20,
    maximum_folds: int = 5,
) -> pd.DataFrame:
    """
    Regresyon modellerini genişleyen pencere walk-forward yöntemiyle test eder.

    Her model için pencere bazlı metriklerin ortalaması, sapması ve
    stabilite skoru hesaplanır.
    """
    required_columns = set(features + [target_column, reference_column])
    missing_columns = required_columns.difference(data.columns)

    if missing_columns:
        raise ValueError(
            "Backtest için eksik sütunlar: "
            + ", ".join(sorted(missing_columns))
        )

    clean_data = (
        data[features + [target_column, reference_column]]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .copy()
    )

    folds = _build_expanding_folds(
        total_rows=len(clean_data),
        minimum_train_size=minimum_train_size,
        minimum_test_size=minimum_test_size,
        maximum_folds=maximum_folds,
    )

    rows = []

    for model_name, template_model in _build_models().items():
        fold_mae = []
        fold_rmse = []
        fold_direction = []
        total_observations = 0
        errors = []

        for fold_number, (train_end, test_end) in enumerate(
            folds,
            start=1,
        ):
            train_data = clean_data.iloc[:train_end]
            test_data = clean_data.iloc[train_end:test_end]

            try:
                model = clone(template_model)

                x_train = train_data[features]
                y_train = train_data[target_column]
                x_test = test_data[features]

                actual = test_data[target_column].to_numpy(dtype=float)
                reference = test_data[reference_column].to_numpy(dtype=float)

                model.fit(x_train, y_train)
                predicted = np.asarray(
                    model.predict(x_test),
                    dtype=float,
                ).reshape(-1)

                if len(predicted) != len(actual):
                    raise ValueError(
                        "Tahmin uzunluğu test verisiyle uyumlu değil."
                    )

                if not np.isfinite(predicted).all():
                    raise ValueError(
                        "Model geçersiz sayısal tahmin üretti."
                    )

                fold_mae.append(
                    float(mean_absolute_error(actual, predicted))
                )
                fold_rmse.append(
                    float(np.sqrt(mean_squared_error(actual, predicted)))
                )
                fold_direction.append(
                    _direction_accuracy(
                        actual_values=actual,
                        predicted_values=predicted,
                        reference_values=reference,
                    )
                )
                total_observations += len(actual)
            except (
                ValueError,
                TypeError,
                RuntimeError,
                FloatingPointError,
            ) as exc:
                errors.append(
                    f"Pencere {fold_number}: {exc}"
                )

        successful_folds = len(fold_rmse)

        if successful_folds < 2:
            rows.append(
                {
                    "Model": model_name,
                    "MAE": np.nan,
                    "RMSE": np.nan,
                    "RMSE Sapması": np.nan,
                    "Yön Doğruluğu %": np.nan,
                    "Yön Sapması": np.nan,
                    "Stabilite Skoru": np.nan,
                    "Test Penceresi": successful_folds,
                    "Test Gözlemi": total_observations,
                    "Durum": "Başarısız",
                    "Backtest Türü": "Walk-Forward Genişleyen Pencere",
                    "Hata": " | ".join(errors) or (
                        "En az iki başarılı test penceresi gerekir."
                    ),
                }
            )
            continue

        mae_mean = float(np.mean(fold_mae))
        rmse_mean = float(np.mean(fold_rmse))
        rmse_std = float(np.std(fold_rmse, ddof=0))
        direction_mean = float(np.mean(fold_direction))
        direction_std = float(np.std(fold_direction, ddof=0))

        rows.append(
            {
                "Model": model_name,
                "MAE": mae_mean,
                "RMSE": rmse_mean,
                "RMSE Sapması": rmse_std,
                "Yön Doğruluğu %": direction_mean,
                "Yön Sapması": direction_std,
                "Stabilite Skoru": _calculate_stability_score(
                    rmse_mean=rmse_mean,
                    rmse_std=rmse_std,
                    direction_mean=direction_mean,
                    direction_std=direction_std,
                ),
                "Test Penceresi": successful_folds,
                "Test Gözlemi": total_observations,
                "Durum": "Başarılı",
                "Backtest Türü": "Walk-Forward Genişleyen Pencere",
                "Hata": (
                    f"{len(errors)} pencere atlandı."
                    if errors
                    else ""
                ),
            }
        )

    result = pd.DataFrame(rows)

    if not result.empty:
        result = result.sort_values(
            by=["Durum", "Stabilite Skoru", "RMSE"],
            ascending=[True, False, True],
            na_position="last",
        ).reset_index(drop=True)

    return result


def _calculate_metric_row(
    model_name: str,
    actual_values: np.ndarray,
    predicted_values: np.ndarray,
    reference_values: np.ndarray,
    backtest_type: str,
) -> Dict[str, object]:
    """Ortak backtest metrik satırını üretir."""
    actual = np.asarray(actual_values, dtype=float).reshape(-1)
    predicted = np.asarray(predicted_values, dtype=float).reshape(-1)
    reference = np.asarray(reference_values, dtype=float).reshape(-1)

    if not (
        len(actual) == len(predicted) == len(reference)
        and len(actual) > 0
    ):
        raise ValueError("Backtest dizilerinin uzunlukları uyumlu değil.")

    if not (
        np.isfinite(actual).all()
        and np.isfinite(predicted).all()
        and np.isfinite(reference).all()
    ):
        raise ValueError("Backtest dizilerinde geçersiz sayısal değer var.")

    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
    direction_accuracy = _direction_accuracy(
        actual_values=actual,
        predicted_values=predicted,
        reference_values=reference,
    )

    return {
        "Model": model_name,
        "MAE": mae,
        "RMSE": rmse,
        "Yön Doğruluğu %": direction_accuracy,
        "RMSE Sapması": 0.0,
        "Yön Sapması": 0.0,
        "Stabilite Skoru": _calculate_stability_score(
            rmse_mean=rmse,
            rmse_std=0.0,
            direction_mean=direction_accuracy,
            direction_std=0.0,
        ),
        "Test Penceresi": len(actual),
        "Test Gözlemi": len(actual),
        "Durum": "Başarılı",
        "Backtest Türü": backtest_type,
        "Hata": "",
    }


def evaluate_arima_and_monte_carlo(
    close_prices: pd.Series,
    horizon: int,
    test_ratio: float = 0.20,
    minimum_train_size: int = 120,
    minimum_test_origins: int = 8,
    maximum_test_origins: int = 20,
    arima_order: Tuple[int, int, int] = (1, 1, 1),
) -> pd.DataFrame:
    """
    ARIMA ve Monte Carlo modellerini genişleyen pencereyle değerlendirir.

    Her test başlangıcında yalnızca o tarihe kadar bilinen fiyatlar kullanılır.
    Gerçekleşen hedef, `horizon` gözlem sonrasındaki kapanış fiyatıdır.
    """
    horizon = int(horizon)

    if horizon <= 0:
        raise ValueError("Backtest ufku sıfırdan büyük olmalıdır.")

    prices = (
        pd.to_numeric(close_prices, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .astype(float)
    )

    if (prices <= 0).any():
        raise ValueError("ARIMA/Monte Carlo backtesti pozitif fiyat gerektirir.")

    total_rows = len(prices)
    latest_origin = total_rows - horizon - 1

    if latest_origin < minimum_train_size:
        raise ValueError(
            "ARIMA/Monte Carlo backtesti için yeterli geçmiş veri yok."
        )

    available_origins = latest_origin - minimum_train_size + 1
    requested_origins = max(
        minimum_test_origins,
        int(round(available_origins * test_ratio)),
    )
    test_origin_count = min(
        maximum_test_origins,
        available_origins,
        requested_origins,
    )

    if test_origin_count < minimum_test_origins:
        raise ValueError(
            "ARIMA/Monte Carlo için yeterli test başlangıç noktası yok."
        )

    origins = np.linspace(
        latest_origin - available_origins + 1,
        latest_origin,
        num=test_origin_count,
        dtype=int,
    )
    origins = np.unique(origins)

    actual_values = []
    reference_values = []
    arima_predictions = []
    monte_carlo_predictions = []

    arima_errors = []
    monte_carlo_errors = []

    for origin in origins:
        history = prices.iloc[: origin + 1]
        reference_price = float(history.iloc[-1])
        actual_price = float(prices.iloc[origin + horizon])

        actual_values.append(actual_price)
        reference_values.append(reference_price)

        try:
            arima_fit = ARIMA(
                history.to_numpy(dtype=float),
                order=arima_order,
            ).fit()
            arima_forecast = np.asarray(
                arima_fit.forecast(steps=horizon),
                dtype=float,
            ).reshape(-1)
            arima_prediction = float(arima_forecast[-1])

            if (
                not np.isfinite(arima_prediction)
                or arima_prediction <= 0
            ):
                raise ValueError("ARIMA geçersiz hedef fiyat üretti.")

            arima_predictions.append(arima_prediction)
        except (
            ValueError,
            TypeError,
            RuntimeError,
            FloatingPointError,
            np.linalg.LinAlgError,
        ) as exc:
            arima_predictions.append(np.nan)
            arima_errors.append(str(exc))

        try:
            log_returns = np.log(
                history.to_numpy(dtype=float)[1:]
                / history.to_numpy(dtype=float)[:-1]
            )
            log_returns = log_returns[np.isfinite(log_returns)]

            if len(log_returns) < 20:
                raise ValueError(
                    "Monte Carlo için yeterli geçerli getiri yok."
                )

            mean_log_return = float(np.mean(log_returns))

            # GBM altında beklenen uç fiyatın deterministik karşılığı.
            monte_carlo_prediction = reference_price * np.exp(
                mean_log_return * horizon
            )

            if (
                not np.isfinite(monte_carlo_prediction)
                or monte_carlo_prediction <= 0
            ):
                raise ValueError(
                    "Monte Carlo geçersiz hedef fiyat üretti."
                )

            monte_carlo_predictions.append(
                float(monte_carlo_prediction)
            )
        except (
            ValueError,
            TypeError,
            FloatingPointError,
        ) as exc:
            monte_carlo_predictions.append(np.nan)
            monte_carlo_errors.append(str(exc))

    actual_array = np.asarray(actual_values, dtype=float)
    reference_array = np.asarray(reference_values, dtype=float)
    rows = []

    for model_name, predictions, errors in (
        ("ARIMA", arima_predictions, arima_errors),
        ("Monte_Carlo", monte_carlo_predictions, monte_carlo_errors),
    ):
        prediction_array = np.asarray(predictions, dtype=float)
        valid_mask = np.isfinite(prediction_array)

        try:
            if int(valid_mask.sum()) < minimum_test_origins:
                raise ValueError(
                    f"Yeterli geçerli tahmin yok: "
                    f"{int(valid_mask.sum())}/{len(prediction_array)}"
                )

            row = _calculate_metric_row(
                model_name=model_name,
                actual_values=actual_array[valid_mask],
                predicted_values=prediction_array[valid_mask],
                reference_values=reference_array[valid_mask],
                backtest_type="Genişleyen Pencere",
            )

            if errors:
                row["Hata"] = (
                    f"{len(errors)} başlangıç noktası atlandı."
                )

            rows.append(row)
        except (ValueError, TypeError, FloatingPointError) as exc:
            rows.append(
                {
                    "Model": model_name,
                    "MAE": np.nan,
                    "RMSE": np.nan,
                    "Yön Doğruluğu %": np.nan,
                    "RMSE Sapması": np.nan,
                    "Yön Sapması": np.nan,
                    "Stabilite Skoru": np.nan,
                    "Test Penceresi": int(valid_mask.sum()),
                    "Test Gözlemi": int(valid_mask.sum()),
                    "Durum": "Başarısız",
                    "Backtest Türü": "Genişleyen Pencere",
                    "Hata": str(exc),
                }
            )

    return pd.DataFrame(rows)


def calculate_dynamic_model_weights(
    backtest_results: pd.DataFrame,
    active_models: Iterable[str],
    base_weights: Optional[Mapping[str, float]] = None,
    minimum_direction_accuracy: float = 45.0,
) -> Dict[str, float]:
    """
    Aktif modeller için backtest destekli dinamik konsensüs ağırlıkları üretir.

    Mantık:
        - Düşük ortalama RMSE daha yüksek puan alır.
        - Yön doğruluğu düşükse model puanı azaltılır.
        - Pencereler arası performansı istikrarsız olan modelin puanı düşürülür.
        - Backtesti başarısız olan regresyon modeli ağırlık alamaz.
        - Geçerli backtest sonucu olmayan aktif model ağırlık alamaz.
        - Son ağırlıkların toplamı 1.0 olur.
    """
    active_model_names = list(dict.fromkeys(str(name) for name in active_models))

    if not active_model_names:
        raise ValueError("Ağırlık hesaplamak için aktif model bulunamadı.")

    default_base_weights = {
        "ARIMA": 0.20,
        "Monte_Carlo": 0.25,
        "Random_Forest": 0.20,
        "XGBoost": 0.15,
        "Linear_Regression": 0.10,
        "SVR": 0.10,
    }

    configured_base_weights = dict(
        base_weights or default_base_weights
    )

    fallback_scores = {
        model_name: max(
            float(configured_base_weights.get(model_name, 0.10)),
            0.0,
        )
        for model_name in active_model_names
    }

    required_columns = {
        "Model",
        "RMSE",
        "Yön Doğruluğu %",
        "Durum",
    }

    if (
        backtest_results is None
        or not isinstance(backtest_results, pd.DataFrame)
        or backtest_results.empty
        or not required_columns.issubset(backtest_results.columns)
    ):
        total_fallback = sum(fallback_scores.values())

        if total_fallback <= 0:
            equal_weight = 1.0 / len(active_model_names)
            return {
                model_name: equal_weight
                for model_name in active_model_names
            }

        return {
            model_name: score / total_fallback
            for model_name, score in fallback_scores.items()
        }

    successful = backtest_results[
        backtest_results["Durum"].astype(str).str.lower() == "başarılı"
    ].copy()

    successful["RMSE"] = pd.to_numeric(
        successful["RMSE"],
        errors="coerce",
    )
    successful["Yön Doğruluğu %"] = pd.to_numeric(
        successful["Yön Doğruluğu %"],
        errors="coerce",
    )
    if "Stabilite Skoru" in successful.columns:
        successful["Stabilite Skoru"] = pd.to_numeric(
            successful["Stabilite Skoru"],
            errors="coerce",
        )
    else:
        successful["Stabilite Skoru"] = 100.0
    successful = successful.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna(
        subset=["RMSE", "Yön Doğruluğu %"]
    )
    successful = successful[successful["RMSE"] > 0]

    valid_rmse_values = successful["RMSE"].to_numpy(dtype=float)
    median_rmse = (
        float(np.median(valid_rmse_values))
        if valid_rmse_values.size > 0
        else 1.0
    )

    model_rows = {
        str(row["Model"]): row
        for _, row in successful.iterrows()
    }

    scores: Dict[str, float] = {}

    for model_name in active_model_names:
        base_score = fallback_scores[model_name]
        row = model_rows.get(model_name)

        if row is None:
            # Geçerli backtest sonucu olmayan model konsensüse katılmaz.
            scores[model_name] = 0.0
            continue

        rmse = float(row["RMSE"])
        direction_accuracy = float(row["Yön Doğruluğu %"])

        inverse_error_factor = median_rmse / max(rmse, 1e-12)
        inverse_error_factor = float(
            np.clip(inverse_error_factor, 0.25, 4.0)
        )

        direction_factor = direction_accuracy / 50.0
        direction_factor = float(
            np.clip(direction_factor, 0.20, 1.50)
        )

        if direction_accuracy < minimum_direction_accuracy:
            direction_factor *= 0.50

        stability_score = float(
            row.get("Stabilite Skoru", 100.0)
        )
        stability_factor = float(
            np.clip(stability_score / 100.0, 0.20, 1.0)
        )

        scores[model_name] = (
            base_score
            * inverse_error_factor
            * direction_factor
            * stability_factor
        )

    positive_scores = {
        model_name: score
        for model_name, score in scores.items()
        if np.isfinite(score) and score > 0
    }

    if not positive_scores:
        total_fallback = sum(fallback_scores.values())

        if total_fallback <= 0:
            equal_weight = 1.0 / len(active_model_names)
            return {
                model_name: equal_weight
                for model_name in active_model_names
            }

        return {
            model_name: score / total_fallback
            for model_name, score in fallback_scores.items()
        }

    total_score = sum(positive_scores.values())

    return {
        model_name: (
            positive_scores.get(model_name, 0.0) / total_score
        )
        for model_name in active_model_names
    }

