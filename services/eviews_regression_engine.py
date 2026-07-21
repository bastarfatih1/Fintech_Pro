from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson, jarque_bera

from services.factor_matrix_engine import build_factor_matrix, normalize_index, safe_close


def _drop_highly_correlated_features(x: pd.DataFrame, threshold: float = 0.98) -> tuple[pd.DataFrame, list[str]]:
    if x.empty or x.shape[1] <= 1:
        return x, []

    corr = x.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    drop_cols = [col for col in upper.columns if any(upper[col] > threshold)]

    if drop_cols:
        return x.drop(columns=drop_cols), drop_cols

    return x, []


def _build_vif_table(x_const: pd.DataFrame) -> pd.DataFrame:
    rows = []

    try:
        for idx, col in enumerate(x_const.columns):
            if col == "const":
                continue

            rows.append({
                "Değişken": col,
                "VIF": float(variance_inflation_factor(x_const.values, idx)),
            })
    except Exception:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def _build_effect_table(model, x: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    x_std = x.std(ddof=0).replace(0, np.nan)
    y_std = y.std(ddof=0)

    rows = []

    for col in x.columns:
        beta = float(model.params.get(col, 0.0))
        std_beta = 0.0

        if (
            y_std
            and np.isfinite(y_std)
            and col in x_std
            and np.isfinite(x_std[col])
        ):
            std_beta = float(beta * x_std[col] / y_std)

        rows.append({
            "Faktör": col,
            "Etki Yönü": "Pozitif" if std_beta > 0 else "Negatif" if std_beta < 0 else "Nötr",
            "Standart Beta": std_beta,
            "Mutlak Etki": abs(std_beta),
            "p-Değeri": float(model.pvalues.get(col, np.nan)),
        })

    table = pd.DataFrame(rows)

    if table.empty:
        return table

    total_abs = table["Mutlak Etki"].sum()

    if total_abs > 0:
        table["Etki Payı %"] = table["Mutlak Etki"] / total_abs * 100.0
    else:
        table["Etki Payı %"] = 0.0

    return table.sort_values("Etki Payı %", ascending=False)


def build_eviews_regression(
    target_data: pd.DataFrame,
    forecast_days: int,
    market_symbol: str,
    asset_name: str,
    asset_type: str | None = None,
    period: str = "10y",
) -> dict[str, Any]:
    matrix = build_factor_matrix(
        target_data=target_data,
        forecast_days=forecast_days,
        market_symbol=market_symbol,
        asset_name=asset_name,
        asset_type=asset_type,
        period=period,
    )

    dataset = matrix["dataset"]
    feature_columns = matrix["feature_columns"]
    target_column = matrix["target_column"]

    if len(feature_columns) < 2:
        raise ValueError("Çoklu regresyon için en az 2 bağımsız değişken gerekir.")

    if len(dataset) < 120:
        raise ValueError(
            f"Çoklu regresyon için yeterli gözlem yok. Mevcut: {len(dataset)}, gerekli: 120+"
        )

    y = dataset[target_column].astype(float)
    x = dataset[feature_columns].astype(float)

    x, dropped_cols = _drop_highly_correlated_features(x)

    if x.shape[1] < 2:
        raise ValueError("Korelasyon filtresinden sonra yeterli bağımsız değişken kalmadı.")

    x_const = sm.add_constant(x, has_constant="add")
    model = sm.OLS(y, x_const).fit()

    coef_table = pd.DataFrame({
        "Değişken": model.params.index,
        "Katsayı": model.params.values,
        "Std. Hata": model.bse.values,
        "t-Statistic": model.tvalues.values,
        "Prob.": model.pvalues.values,
    })

    effect_table = _build_effect_table(model=model, x=x, y=y)
    vif_table = _build_vif_table(x_const)

    residuals = model.resid
    jb_stat, jb_pvalue, skew, kurtosis = jarque_bera(residuals)
    dw = durbin_watson(residuals)

    try:
        bp_stat, bp_pvalue, _, _ = het_breuschpagan(residuals, x_const)
    except Exception:
        bp_pvalue = np.nan

    try:
        lb = acorr_ljungbox(
            residuals,
            lags=[min(10, max(1, len(residuals) // 10))],
            return_df=True,
        )
        lb_pvalue = float(lb["lb_pvalue"].iloc[-1])
    except Exception:
        lb_pvalue = np.nan

    stats_table = pd.DataFrame([
        {"Metrik": "Dependent Variable", "Değer": target_column},
        {"Metrik": "Method", "Değer": "Least Squares / OLS"},
        {"Metrik": "Included Observations", "Değer": int(model.nobs)},
        {"Metrik": "R-squared", "Değer": float(model.rsquared)},
        {"Metrik": "Adjusted R-squared", "Değer": float(model.rsquared_adj)},
        {"Metrik": "S.E. of regression", "Değer": float(np.sqrt(model.mse_resid))},
        {"Metrik": "Sum squared resid", "Değer": float(np.sum(residuals ** 2))},
        {"Metrik": "Log likelihood", "Değer": float(model.llf)},
        {"Metrik": "Akaike info criterion", "Değer": float(model.aic)},
        {"Metrik": "Schwarz criterion", "Değer": float(model.bic)},
        {"Metrik": "F-statistic", "Değer": float(model.fvalue) if model.fvalue is not None else np.nan},
        {"Metrik": "Prob(F-statistic)", "Değer": float(model.f_pvalue) if model.f_pvalue is not None else np.nan},
        {"Metrik": "Durbin-Watson stat", "Değer": float(dw)},
        {"Metrik": "Jarque-Bera Prob.", "Değer": float(jb_pvalue)},
        {"Metrik": "Breusch-Pagan Prob.", "Değer": float(bp_pvalue)},
        {"Metrik": "Ljung-Box Prob.", "Değer": float(lb_pvalue)},
    ])

    latest_x = x.iloc[[-1]]
    latest_x_const = sm.add_constant(latest_x, has_constant="add")
    predicted_return = float(model.predict(latest_x_const).iloc[0])

    close = safe_close(normalize_index(target_data))
    current_price = float(close.iloc[-1])
    predicted_price = current_price * float(np.exp(predicted_return))

    return {
        "asset_name": asset_name,
        "market_symbol": market_symbol,
        "formula": target_column + " = C + " + " + ".join(x.columns),
        "dataset": dataset,
        "coef_table": coef_table,
        "effect_table": effect_table,
        "vif_table": vif_table,
        "stats_table": stats_table,
        "factor_diagnostics": matrix["factor_diagnostics"],
        "predicted_return": predicted_return,
        "current_price": current_price,
        "predicted_price": predicted_price,
        "dropped_correlated_factors": dropped_cols,
        "feature_columns": list(x.columns),
    }


def build_multi_factor_ols_route(
    target_data: pd.DataFrame,
    forecast_days: int,
    current_price: float,
    market_symbol: str,
    asset_name: str,
    asset_type: str | None = None,
) -> np.ndarray:
    result = build_eviews_regression(
        target_data=target_data,
        forecast_days=forecast_days,
        market_symbol=market_symbol,
        asset_name=asset_name,
        asset_type=asset_type,
    )

    start_price = float(current_price)
    target_price = float(result["predicted_price"])

    if not np.isfinite(start_price) or start_price <= 0:
        raise ValueError("Multi_Factor_OLS başlangıç fiyatı geçersiz.")

    if not np.isfinite(target_price) or target_price <= 0:
        raise ValueError("Multi_Factor_OLS hedef fiyatı geçersiz.")

    days = int(forecast_days)

    if days <= 0:
        raise ValueError("Multi_Factor_OLS vade gün sayısı geçersiz.")

    progress = np.linspace(0.0, 1.0, days)
    route = start_price * np.exp(np.log(target_price / start_price) * progress)
    route[-1] = target_price

    return route.astype(float)


def evaluate_multi_factor_ols_backtest(
    target_data: pd.DataFrame,
    market_symbol: str,
    asset_name: str,
    asset_type: str | None = None,
    test_window: int = 5,
    max_windows: int = 250,
    min_train_rows: int = 252,
) -> pd.DataFrame:
    """
    Multi_Factor_OLS için walk-forward benzeri backtest üretir.

    Mantık:
    - Her test gününde sadece geçmiş verilerle OLS kurulur.
    - O tarihten test_window gün sonrası tahmin edilir.
    - Tahmin edilen fiyat gerçek fiyatla karşılaştırılır.
    - Naive_Last_Price referansına göre RMSE iyileşmesi hesaplanır.
    """

    horizon = int(test_window)

    if horizon <= 0:
        raise ValueError("Multi_Factor_OLS backtest test_window geçersiz.")

    matrix = build_factor_matrix(
        target_data=target_data,
        forecast_days=horizon,
        market_symbol=market_symbol,
        asset_name=asset_name,
        asset_type=asset_type,
        period="10y",
    )

    dataset = matrix["dataset"].copy()
    feature_columns = list(matrix["feature_columns"])
    target_column = matrix["target_column"]

    if len(feature_columns) < 2:
        raise ValueError("Multi_Factor_OLS backtest için yeterli faktör yok.")

    if len(dataset) < min_train_rows + 20:
        raise ValueError(
            f"Multi_Factor_OLS backtest için yeterli gözlem yok. Mevcut: {len(dataset)}"
        )

    close = safe_close(normalize_index(target_data))
    close = close.reindex(dataset.index).dropna()

    dataset = dataset.loc[dataset.index.intersection(close.index)].copy()

    if len(dataset) < min_train_rows + 20:
        raise ValueError("Multi_Factor_OLS backtest veri hizalaması sonrası yetersiz kaldı.")

    start_index = max(min_train_rows, len(dataset) - int(max_windows))

    predicted_prices = []
    actual_prices = []
    reference_prices = []
    direction_hits = []

    for i in range(start_index, len(dataset)):
        train = dataset.iloc[:i].copy()
        test_row = dataset.iloc[[i]].copy()

        y_train = train[target_column].astype(float)
        x_train = train[feature_columns].astype(float)

        x_train, dropped = _drop_highly_correlated_features(x_train)

        if x_train.shape[1] < 2:
            continue

        x_const = sm.add_constant(x_train, has_constant="add")
        model = sm.OLS(y_train, x_const).fit()

        x_test = test_row[x_train.columns].astype(float)
        x_test_const = sm.add_constant(x_test, has_constant="add")

        pred_return = float(model.predict(x_test_const).iloc[0])
        actual_return = float(test_row[target_column].iloc[0])

        start_price = float(close.loc[test_row.index[0]])

        pred_price = start_price * float(np.exp(pred_return))
        actual_price = start_price * float(np.exp(actual_return))
        ref_price = start_price

        if not (
            np.isfinite(pred_price)
            and np.isfinite(actual_price)
            and np.isfinite(ref_price)
            and pred_price > 0
            and actual_price > 0
            and ref_price > 0
        ):
            continue

        predicted_prices.append(pred_price)
        actual_prices.append(actual_price)
        reference_prices.append(ref_price)

        pred_dir = np.sign(pred_price - start_price)
        actual_dir = np.sign(actual_price - start_price)
        direction_hits.append(float(pred_dir == actual_dir))

    if len(predicted_prices) < 20:
        raise ValueError(
            f"Multi_Factor_OLS backtest için yeterli geçerli test üretilemedi. Geçerli: {len(predicted_prices)}"
        )

    predicted = np.asarray(predicted_prices, dtype=float)
    actual = np.asarray(actual_prices, dtype=float)
    reference = np.asarray(reference_prices, dtype=float)

    rmse = float(np.sqrt(np.mean((predicted - actual) ** 2)))
    reference_rmse = float(np.sqrt(np.mean((reference - actual) ** 2)))

    if not np.isfinite(rmse) or not np.isfinite(reference_rmse) or reference_rmse <= 0:
        raise ValueError("Multi_Factor_OLS backtest RMSE hesaplanamadı.")

    improvement = (reference_rmse - rmse) / reference_rmse * 100.0
    passed = rmse < reference_rmse

    direction_accuracy = float(np.mean(direction_hits) * 100.0)

    stability_score = float(
        max(
            0.0,
            min(
                100.0,
                (direction_accuracy * 0.5) + (max(improvement, 0.0) * 0.5),
            ),
        )
    )

    return pd.DataFrame([
        {
            "Model": "Multi_Factor_OLS",
            "Durum": "başarılı",
            "RMSE": round(rmse, 2),
            "Referans RMSE": round(reference_rmse, 2),
            "RMSE İyileşme %": round(improvement, 1),
            "Referansı Geçti": "Evet" if passed else "Hayır",
            "Yön Doğruluğu %": round(direction_accuracy, 1),
            "Stabilite Skoru": round(stability_score, 1),
            "Test Penceresi": horizon,
            "Test Gözlemi": int(len(predicted_prices)),
            "Backtest Türü": "Dynamic Factor Walk-Forward OLS",
        }
    ])
