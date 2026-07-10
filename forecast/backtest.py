"""
Zaman sıralı model doğrulama yardımcıları.

Bu modül veriyi karıştırmadan eğitim ve test bölümlerine ayırır.
Böylece modeller yalnızca geçmiş veriden öğrenir ve daha sonraki
dönem üzerinde değerlendirilir.
"""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor


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


def evaluate_regression_models(
    data: pd.DataFrame,
    features: List[str],
    target_column: str = "Target",
    reference_column: str = "Close",
    test_ratio: float = 0.20,
    minimum_train_size: int = 60,
    minimum_test_size: int = 20,
) -> pd.DataFrame:
    """
    Regresyon modellerini zaman sıralı test verisi üzerinde değerlendirir.

    Dönen sütunlar:
        Model, MAE, RMSE, Yön Doğruluğu %, Test Gözlemi, Durum
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

    train_data, test_data = _chronological_split(
        clean_data,
        test_ratio=test_ratio,
        minimum_train_size=minimum_train_size,
        minimum_test_size=minimum_test_size,
    )

    x_train = train_data[features]
    y_train = train_data[target_column]

    x_test = test_data[features]
    y_test = test_data[target_column].to_numpy(dtype=float)
    reference_values = test_data[reference_column].to_numpy(dtype=float)

    rows = []

    for model_name, model in _build_models().items():
        try:
            model.fit(x_train, y_train)
            predictions = np.asarray(
                model.predict(x_test),
                dtype=float,
            ).reshape(-1)

            if len(predictions) != len(y_test):
                raise ValueError(
                    "Tahmin uzunluğu test verisiyle uyumlu değil."
                )

            if not np.isfinite(predictions).all():
                raise ValueError(
                    "Model geçersiz sayısal tahmin üretti."
                )

            mae = float(mean_absolute_error(y_test, predictions))
            rmse = float(
                np.sqrt(mean_squared_error(y_test, predictions))
            )
            direction_accuracy = _direction_accuracy(
                actual_values=y_test,
                predicted_values=predictions,
                reference_values=reference_values,
            )

            rows.append(
                {
                    "Model": model_name,
                    "MAE": mae,
                    "RMSE": rmse,
                    "Yön Doğruluğu %": direction_accuracy,
                    "Test Gözlemi": len(y_test),
                    "Durum": "Başarılı",
                    "Hata": "",
                }
            )
        except (
            ValueError,
            TypeError,
            RuntimeError,
            FloatingPointError,
        ) as exc:
            rows.append(
                {
                    "Model": model_name,
                    "MAE": np.nan,
                    "RMSE": np.nan,
                    "Yön Doğruluğu %": np.nan,
                    "Test Gözlemi": len(y_test),
                    "Durum": "Başarısız",
                    "Hata": str(exc),
                }
            )

    result = pd.DataFrame(rows)

    if not result.empty:
        result = result.sort_values(
            by=["Durum", "RMSE"],
            ascending=[True, True],
            na_position="last",
        ).reset_index(drop=True)

    return result
