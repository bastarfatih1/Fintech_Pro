import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import warnings
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor
from statsmodels.tsa.arima.model import ARIMA
from risk.metrics import calculate_risk_metrics
from core.market_calendar import get_market_calendar_config
from services.data_provider import get_market_history
from forecast.backtest import (
    calculate_dynamic_model_weights,
    calculate_weighted_calibration_error,
    evaluate_arima_and_monte_carlo,
    evaluate_regression_models,
)

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

FALLBACK_CURRENCY_RATES = {
    "USD": 1.0,
    "TRY": 34.20,
    "EUR": 0.92,
    "CNY": 7.25,
    "RUB": 88.0,
    "SAR": 3.75,
    "KWD": 0.31,
    "JPY": 155.0,
}


def _load_local_env() -> None:
    """
    Proje kökündeki .env dosyasını ek paket gerektirmeden yükler.

    Mevcut sistem ortam değişkenleri korunur.
    """
    env_path = Path(__file__).resolve().parent / ".env"

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


_load_local_env()


def get_kurlar():
    """
    Güncel döviz kurlarını getirir.

    API anahtarı EXCHANGE_RATE_API_KEY ortam değişkeninden okunur.
    Anahtar yoksa veya istek başarısız olursa güvenli yedek değerler döner.
    """
    api_key = os.getenv("EXCHANGE_RATE_API_KEY", "").strip()

    if not api_key:
        return FALLBACK_CURRENCY_RATES.copy()

    url = (
        "https://v6.exchangerate-api.com/v6/"
        f"{api_key}/latest/USD"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        payload = response.json()
        rates = payload.get("conversion_rates", {})

        if not rates:
            return FALLBACK_CURRENCY_RATES.copy()

        return {
            "USD": 1.0,
            "TRY": rates.get("TRY", FALLBACK_CURRENCY_RATES["TRY"]),
            "EUR": rates.get("EUR", FALLBACK_CURRENCY_RATES["EUR"]),
            "CNY": rates.get("CNY", FALLBACK_CURRENCY_RATES["CNY"]),
            "RUB": rates.get("RUB", FALLBACK_CURRENCY_RATES["RUB"]),
            "SAR": rates.get("SAR", FALLBACK_CURRENCY_RATES["SAR"]),
            "KWD": rates.get("KWD", FALLBACK_CURRENCY_RATES["KWD"]),
            "JPY": rates.get("JPY", FALLBACK_CURRENCY_RATES["JPY"]),
        }
    except (requests.RequestException, ValueError, TypeError):
        return FALLBACK_CURRENCY_RATES.copy()

def volatile_path_generator(
    curr,
    target,
    days,
    daily_vol,
    random_state=42,
):
    """
    Başlangıç fiyatından hedef fiyata kontrollü ve pozitif rota üretir.

    Not:
        Bu rota gerçek model tahmini değildir.
        Yalnızca tek hedef fiyatın görselleştirilmesi içindir.
    """
    curr = float(curr)
    target = float(target)
    days = int(days)

    if days <= 0:
        return np.array([], dtype=float)

    if curr <= 0:
        raise ValueError("Başlangıç fiyatı pozitif olmalıdır.")

    if not np.isfinite(target) or target <= 0:
        target = curr

    if days == 1:
        return np.array([target], dtype=float)

    rng = np.random.default_rng(random_state)

    progress = np.linspace(0.0, 1.0, days)

    base_path = curr * np.exp(
        np.log(target / curr) * progress
    )

    noise = rng.normal(
        loc=0.0,
        scale=min(float(daily_vol), 0.05),
        size=days,
    )

    noise[0] = 0.0
    noise[-1] = 0.0

    noise = np.cumsum(noise)
    noise = noise - np.linspace(
        noise[0],
        noise[-1],
        days,
    )

    path = base_path * np.exp(noise)

    lower_limit = curr * 0.05
    upper_limit = curr * 20.0

    path = np.clip(
        path,
        lower_limit,
        upper_limit,
    )

    path[0] = curr
    path[-1] = target

    return path


def _build_calibrated_scenario_bands(
    consensus_path,
    current_price,
    daily_volatility,
    horizon,
    calibration_log_error,
    monte_carlo_lower=None,
    monte_carlo_upper=None,
    include_monte_carlo=False,
):
    """
    Backtest hata dağılımı ve tarihsel volatiliteyle senaryo bantları üretir.

    Bantlar çarpımsal log-fiyat ölçeğinde oluşturulur. Böylece alt bant
    sıfır veya negatif fiyat üretemez.
    """
    consensus = np.asarray(
        consensus_path,
        dtype=float,
    ).reshape(-1)
    horizon = int(horizon)
    current_price = float(current_price)

    if len(consensus) != horizon or horizon <= 0:
        raise ValueError("Senaryo bandı uzunluğu tahmin vadesiyle uyumsuz.")

    if (
        current_price <= 0
        or not np.isfinite(consensus).all()
        or np.any(consensus <= 0)
    ):
        raise ValueError("Senaryo bantları pozitif geçerli fiyat gerektirir.")

    volatility_error = (
        1.645
        * max(float(daily_volatility), 1e-6)
        * np.sqrt(horizon)
    )

    if (
        calibration_log_error is None
        or not np.isfinite(float(calibration_log_error))
        or float(calibration_log_error) < 0
    ):
        endpoint_log_error = volatility_error
        calibration_source = "Tarihsel volatilite yedeği"
    else:
        endpoint_log_error = max(
            float(calibration_log_error),
            volatility_error,
        )
        calibration_source = (
            "Backtest %90 log hata ve tarihsel volatilite"
        )

    # Sayısal taşmayı engeller; çok yüksek belirsizlik yine geniş bant üretir.
    endpoint_log_error = float(
        np.clip(endpoint_log_error, 0.01, 3.0)
    )

    progress = (
        np.arange(1, horizon + 1, dtype=float)
        / float(horizon)
    )
    widening = endpoint_log_error * np.sqrt(progress)

    lower = consensus * np.exp(-widening)
    upper = consensus * np.exp(widening)

    if include_monte_carlo:
        mc_lower = np.asarray(
            monte_carlo_lower,
            dtype=float,
        ).reshape(-1)
        mc_upper = np.asarray(
            monte_carlo_upper,
            dtype=float,
        ).reshape(-1)

        if (
            len(mc_lower) == horizon
            and len(mc_upper) == horizon
        ):
            valid_mc = (
                np.isfinite(mc_lower)
                & np.isfinite(mc_upper)
                & (mc_lower > 0)
                & (mc_upper > 0)
            )
            lower = np.where(
                valid_mc,
                np.minimum(lower, mc_lower),
                lower,
            )
            upper = np.where(
                valid_mc,
                np.maximum(upper, mc_upper),
                upper,
            )
            calibration_source += " + Monte Carlo %5-%95 zarfı"

    positive_floor = max(current_price * 0.01, 1e-9)
    lower = np.maximum(lower, positive_floor)
    lower = np.minimum(lower, consensus)
    upper = np.maximum(upper, consensus)

    return (
        lower,
        upper,
        endpoint_log_error,
        calibration_source,
    )


def destek_direnc_bul(df, window=20):
    destek = df['Low'].rolling(window=window).min().iloc[-1]
    direnc = df['High'].rolling(window=window).max().iloc[-1]
    return destek, direnc

def get_sp500_data(start_date, end_date):
    """
    S&P 500 kapanış verisini provider katmanı üzerinden güvenli şekilde getirir.

    Beta hesabı için kullanılan ^GSPC verisi artık doğrudan yfinance ile
    çekilmez. Böylece ileride lisanslı veya farklı bir endeks sağlayıcısına
    geçiş tek provider katmanından yapılabilir.
    """
    try:
        result = get_market_history(
            symbol="^GSPC",
            asset_type="index",
            start_date=start_date,
            end_date=end_date,
        )

        if result.is_empty or "Close" not in result.data.columns:
            return pd.Series(dtype=float)

        return result.data["Close"]
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        logger.warning("S&P 500 verisi alınamadı: %s", exc)
        return pd.Series(dtype=float)

def hesapla_gecmis_performans(data, curr, ana_para, kur_val, s):
    try:
        close_prices = data['Close']
        son = float(close_prices.iloc[-1])
        periyotlar = [
            ("1 Hafta Önce", 7), ("1 Ay Önce", 30), ("3 Ay Önce", 90),
            ("6 Ay Önce", 180), ("1 Yıl Önce", 252), ("3 Yıl Önce", 252 * 3), ("5 Yıl Önce", 252 * 5)
        ]
        gecmis_tablo = []
        for etiket, gun in periyotlar:
            if len(close_prices) >= gun:
                eski_fiyat = float(close_prices.iloc[-gun])
                degisim = ((son - eski_fiyat) / eski_fiyat) * 100
                sermaye_degeri = ana_para * (son / eski_fiyat) if eski_fiyat != 0 else ana_para
                yil_katsayisi = gun / 365
                enflasyon_etkisi = (1.035 ** yil_katsayisi) - 1
                reel_getiri = degisim - (enflasyon_etkisi * 100)
                gecmis_tablo.append({
                    "Dönem": etiket,
                    "Eski Fiyat": f"{eski_fiyat * kur_val:,.2f} {s}",
                    "Güncel Fiyat": f"{son * kur_val:,.2f} {s}",
                    "Nominal Getiri": f"{degisim:+.2f}%",
                    "Reel Getiri": f"{reel_getiri:+.2f}%",
                    "Sermaye Değeri": f"{sermaye_degeri:,.2f} {s}"
                })
        return pd.DataFrame(gecmis_tablo)
    except Exception:
        return pd.DataFrame([{"Dönem": "Veri Yok", "Eski Fiyat": "-", "Güncel Fiyat": "-", "Nominal Getiri": "-", "Reel Getiri": "-", "Sermaye Değeri": "-"}])

def gelecek_senaryolari_hesapla(
    data,
    periyot_gun,
    ana_para,
    curr,
    kur_val=1.0,
    asset_type=None,
    market_symbol=None,
):
    calendar_config = get_market_calendar_config(
        asset_type=asset_type,
        market_symbol=market_symbol,
    )
    df = data.copy()
    df['Lag_1'] = df['Close'].shift(1)
    df['Lag_2'] = df['Close'].shift(2)
    df['Lag_3'] = df['Close'].shift(3)
    df['MA_14'] = df['Close'].rolling(window=14).mean()
    df['Vol_14'] = df['Close'].rolling(window=14).std()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['Target'] = df['Close'].shift(-periyot_gun)
    
    features = ['Lag_1', 'Lag_2', 'Lag_3', 'MA_14', 'Vol_14', 'RSI']
    train_df = df.dropna(subset=features + ['Target'])
    latest_features = df.dropna(subset=features)
    
    if not latest_features.empty:
        X_latest = latest_features[features].iloc[-1].values.reshape(1, -1)
    else:
        X_latest = np.zeros((1, len(features)))
        
    rotalar = {}
    model_durumlari = {}
    rota_turleri = {}

    hist_prices = df["Close"].dropna().values
    log_returns = np.log(hist_prices[1:] / hist_prices[:-1])
    daily_vol = np.std(log_returns) if np.std(log_returns) > 0 else 0.01

    if train_df.empty:
        raise ValueError(
            "Seçilen tahmin vadesi için yeterli eğitim verisi bulunamadı."
        )

    backtest_frames = []
    backtest_messages = []

    try:
        regression_backtest = evaluate_regression_models(
            data=train_df,
            features=features,
            target_column="Target",
            reference_column="Close",
        )
        backtest_frames.append(regression_backtest)
    except ValueError as exc:
        logger.warning("Regresyon backtesti çalıştırılamadı: %s", exc)
        backtest_messages.append(f"Regresyon: {exc}")

    try:
        time_series_backtest = evaluate_arima_and_monte_carlo(
            close_prices=df["Close"],
            horizon=periyot_gun,
        )
        backtest_frames.append(time_series_backtest)
    except ValueError as exc:
        logger.warning(
            "ARIMA/Monte Carlo backtesti çalıştırılamadı: %s",
            exc,
        )
        backtest_messages.append(f"ARIMA/Monte Carlo: {exc}")

    if backtest_frames:
        backtest_df = pd.concat(
            backtest_frames,
            ignore_index=True,
            sort=False,
        )
        if "Model" in backtest_df.columns:
            backtest_df = backtest_df.drop_duplicates(
                subset=["Model"],
                keep="first",
            ).reset_index(drop=True)
        backtest_status = (
            "tamamlandı"
            if not backtest_messages
            else "kısmi: " + " | ".join(backtest_messages)
        )
    else:
        backtest_df = pd.DataFrame(
            columns=[
                "Model",
                "MAE",
                "RMSE",
                "Yön Doğruluğu %",
                "Test Gözlemi",
                "Durum",
                "Backtest Türü",
                "Hata",
            ]
        )
        backtest_status = (
            " | ".join(backtest_messages)
            or "Backtest sonucu üretilemedi."
        )

    def kaydet_basarili_model(
        model_adi,
        rota,
        rota_turu="Model Tahmin Rotası",
    ):
        """Başarılı model rotasını doğrular ve kaydeder."""
        rota = np.asarray(rota, dtype=float).reshape(-1)

        if len(rota) != periyot_gun:
            raise ValueError(
                f"{model_adi} rota uzunluğu beklenen vadeyle uyumlu değil."
            )

        if not np.isfinite(rota).all():
            raise ValueError(
                f"{model_adi} geçersiz sayısal değer üretti."
            )

        if np.any(rota <= 0):
            raise ValueError(
                f"{model_adi} sıfır veya negatif fiyat üretti."
            )

        rotalar[model_adi] = rota
        rota_turleri[model_adi] = rota_turu
        model_durumlari[model_adi] = {
            "durum": "başarılı",
            "hata": None,
        }

    def kaydet_basarisiz_model(model_adi, hata):
        """Başarısız modeli konsensüsten çıkarır ve hata bilgisini kaydeder."""
        logger.warning("%s modeli başarısız: %s", model_adi, hata)
        model_durumlari[model_adi] = {
            "durum": "başarısız",
            "hata": str(hata),
        }

    try:
        lr = LinearRegression()
        lr.fit(train_df[features], train_df["Target"])
        lr_target = float(lr.predict(X_latest)[0])
        kaydet_basarili_model(
            "Linear_Regression",
            volatile_path_generator(
                curr,
                lr_target,
                periyot_gun,
                daily_vol,
                random_state=11,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("Linear_Regression", exc)

    try:
        rf = RandomForestRegressor(
            n_estimators=50,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(train_df[features], train_df["Target"])
        rf_target = float(rf.predict(X_latest)[0])
        kaydet_basarili_model(
            "Random_Forest",
            volatile_path_generator(
                curr,
                rf_target,
                periyot_gun,
                daily_vol,
                random_state=22,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("Random_Forest", exc)

    try:
        svr = SVR(C=1.0, epsilon=0.2)
        svr.fit(train_df[features], train_df["Target"])
        svr_target = float(svr.predict(X_latest)[0])
        kaydet_basarili_model(
            "SVR",
            volatile_path_generator(
                curr,
                svr_target,
                periyot_gun,
                daily_vol,
                random_state=33,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("SVR", exc)

    try:
        xgb = XGBRegressor(
            n_estimators=50,
            random_state=42,
            n_jobs=-1,
        )
        xgb.fit(train_df[features], train_df["Target"])
        xgb_target = float(xgb.predict(X_latest)[0])
        kaydet_basarili_model(
            "XGBoost",
            volatile_path_generator(
                curr,
                xgb_target,
                periyot_gun,
                daily_vol,
                random_state=44,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("XGBoost", exc)

    try:
        arima_model = ARIMA(hist_prices, order=(1, 1, 1))
        arima_fit = arima_model.fit()
        kaydet_basarili_model(
            "ARIMA",
            arima_fit.forecast(steps=periyot_gun),
        )
    except (ValueError, TypeError, RuntimeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("ARIMA", exc)

    n_sim = 10000

    try:
        rng = np.random.default_rng(55)
        mu = np.mean(log_returns)
        z_values = rng.normal(0, 1, (n_sim, periyot_gun))
        drift = mu - 0.5 * (daily_vol ** 2)
        growth = np.exp(drift + daily_vol * z_values)
        cum_growth = np.cumprod(growth, axis=1)
        mc_paths = curr * cum_growth

        monte_carlo_mean = np.mean(mc_paths, axis=0)
        mc_upper = np.percentile(mc_paths, 95, axis=0)
        mc_lower = np.percentile(mc_paths, 5, axis=0)

        kaydet_basarili_model(
            "Monte_Carlo",
            monte_carlo_mean,
        )
    except (ValueError, TypeError, FloatingPointError, MemoryError) as exc:
        kaydet_basarisiz_model("Monte_Carlo", exc)
        mc_upper = np.full(periyot_gun, np.nan)
        mc_lower = np.full(periyot_gun, np.nan)

    if not rotalar:
        raise RuntimeError(
            "Tahmin modellerinin hiçbiri geçerli sonuç üretemedi."
        )

    model_agirliklari = calculate_dynamic_model_weights(
        backtest_results=backtest_df,
        active_models=rotalar.keys(),
    )

    base_path = np.zeros(periyot_gun, dtype=float)
    toplam_w = 0.0

    for model_adi, model_rotasi in rotalar.items():
        agirlik = float(model_agirliklari.get(model_adi, 0.0))

        if agirlik <= 0:
            continue

        base_path += model_rotasi * agirlik
        toplam_w += agirlik

    if toplam_w <= 0:
        raise RuntimeError(
            "Geçerli konsensüs ağırlığı üretilemedi."
        )

    konsensus_rota = base_path / toplam_w

    if not backtest_df.empty and "Model" in backtest_df.columns:
        backtest_df = backtest_df.copy()
        backtest_df["Konsensüs Ağırlığı %"] = (
            backtest_df["Model"]
            .map(model_agirliklari)
            .fillna(0.0)
            .astype(float)
            * 100.0
        )

    if "Monte_Carlo" not in rotalar:
        mc_upper = konsensus_rota.copy()
        mc_lower = konsensus_rota.copy()

    calibration_log_error = calculate_weighted_calibration_error(
        backtest_results=backtest_df,
        model_weights=model_agirliklari,
    )

    monte_carlo_is_active = (
        float(model_agirliklari.get("Monte_Carlo", 0.0)) > 0
        and "Monte_Carlo" in rotalar
    )

    (
        senaryo_alt_rota,
        senaryo_ust_rota,
        kalibrasyon_log_hata_90,
        guven_araligi_yontemi,
    ) = _build_calibrated_scenario_bands(
        consensus_path=konsensus_rota,
        current_price=curr,
        daily_volatility=daily_vol,
        horizon=periyot_gun,
        calibration_log_error=calibration_log_error,
        monte_carlo_lower=mc_lower,
        monte_carlo_upper=mc_upper,
        include_monte_carlo=monte_carlo_is_active,
    )

    risk_stats = calculate_risk_metrics(df["Close"])
    
    # DÜZELTİLMİŞ BETA HESAPLAMASI
    sp500_data = get_sp500_data(data.index[0], data.index[-1])
    beta = 1.0
    if not sp500_data.empty and len(sp500_data) > 10:
        df_beta = pd.concat([data['Close'], sp500_data], axis=1, join='inner')
        df_beta.columns = ['Stock', 'SP500']
        stock_returns = df_beta['Stock'].pct_change().dropna()
        sp_returns = df_beta['SP500'].pct_change().dropna()
        min_len = min(len(stock_returns), len(sp_returns))
        if min_len > 1:
            stock_returns = stock_returns.iloc[-min_len:].values.flatten()
            sp_returns = sp_returns.iloc[-min_len:].values.flatten()
            cov_matrix = np.cov(stock_returns, sp_returns)
            beta = float(cov_matrix[0, 1] / (cov_matrix[1, 1] + 1e-9))

    gelecek_tablo = []
    periyotlar = calendar_config.horizons
    for l, d in periyotlar:
        if d <= periyot_gun:
            alt_native = float(senaryo_alt_rota[d - 1])
            baz_native = float(konsensus_rota[d - 1])
            ust_native = float(senaryo_ust_rota[d - 1])

            baz_getiri = (baz_native - curr) / curr
            alt_getiri = (alt_native - curr) / curr
            ust_getiri = (ust_native - curr) / curr

            gelecek_tablo.append(
                {
                    "Vade": l,
                    "Kötümser Senaryo": round(
                        alt_native * kur_val,
                        2,
                    ),
                    "Baz Senaryo": round(
                        baz_native * kur_val,
                        2,
                    ),
                    "İyimser Senaryo": round(
                        ust_native * kur_val,
                        2,
                    ),
                    # Mevcut arayüz uyumluluğu için baz senaryo alias'ı.
                    "Tahmin": round(
                        baz_native * kur_val,
                        2,
                    ),
                    "Kötümser Getiri %": round(
                        alt_getiri * 100.0,
                        2,
                    ),
                    "Nominal Getiri %": round(
                        baz_getiri * 100.0,
                        2,
                    ),
                    "İyimser Getiri %": round(
                        ust_getiri * 100.0,
                        2,
                    ),
                    "Kötümser Sermaye": round(
                        ana_para * (1.0 + alt_getiri),
                        2,
                    ),
                    "Sermaye Karşılığı": round(
                        ana_para * (1.0 + baz_getiri),
                        2,
                    ),
                    "İyimser Sermaye": round(
                        ana_para * (1.0 + ust_getiri),
                        2,
                    ),
                }
            )

    destek, direnc = destek_direnc_bul(df)
    return {
        "konsensus_rota": konsensus_rota * kur_val,
        "senaryo_alt": senaryo_alt_rota * kur_val,
        "senaryo_ust": senaryo_ust_rota * kur_val,
        "mc_upper": mc_upper * kur_val,
        "mc_lower": mc_lower * kur_val,
        "mc_raw_upper": mc_upper * kur_val,
        "mc_raw_lower": mc_lower * kur_val,
        "rotalar": {k: v * kur_val for k, v in rotalar.items()},
        "model_durumlari": model_durumlari,
        "model_agirliklari": model_agirliklari,
        "rota_turleri": rota_turleri,
        "projeksiyon_bildirimi": (
            "Regresyon modellerinin ara dönem çizgileri görsel senaryo "
            "rotasıdır; modelin doğrudan günlük tahmini değildir. "
            "Vade sonu hedefleri ve ARIMA/Monte Carlo yolları ayrı "
            "değerlendirilmelidir. Kötümser ve iyimser senaryo bantları "
            "backtest hataları, tarihsel volatilite ve uygun olduğunda "
            "Monte Carlo dağılımıyla kalibre edilir. "
            f"Takvim standardı: {calendar_config.calendar_name}."
        ),
        "varlik_turu": calendar_config.asset_type,
        "varlik_turu_etiketi": calendar_config.display_name,
        "market_symbol": str(market_symbol or ""),
        "vade_birimi": calendar_config.period_unit,
        "takvim_frekansi": calendar_config.date_frequency,
        "takvim_adi": calendar_config.calendar_name,
        "takvim_aciklamasi": calendar_config.calendar_note,
        "vade_standardlari": [
            {"etiket": etiket, "periyot": gun}
            for etiket, gun in calendar_config.horizons
        ],
        "guven_araligi_yontemi": guven_araligi_yontemi,
        "kalibrasyon_log_hata_90": kalibrasyon_log_hata_90,
        "backtest_df": backtest_df,
        "backtest_status": backtest_status,
        "stats": {
            **risk_stats,
            "Beta": beta,
        },
        "gelecek_df": pd.DataFrame(gelecek_tablo),
        "boga": float(senaryo_ust_rota[-1] * kur_val),
        "ayi": float(senaryo_alt_rota[-1] * kur_val),
        "destek": destek * kur_val,
        "direnc": direnc * kur_val
    }
