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
import yfinance as yf

warnings.filterwarnings('ignore')

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

def destek_direnc_bul(df, window=20):
    destek = df['Low'].rolling(window=window).min().iloc[-1]
    direnc = df['High'].rolling(window=window).max().iloc[-1]
    return destek, direnc

def get_sp500_data(start_date, end_date):
    try:
        sp500 = yf.download('^GSPC', start=start_date, end=end_date, progress=False)['Close']
        return sp500
    except:
        return pd.Series()

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

def gelecek_senaryolari_hesapla(data, periyot_gun, ana_para, curr, kur_val=1.0):
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
    hist_prices = df['Close'].dropna().values
    log_returns = np.log(hist_prices[1:] / hist_prices[:-1])
    daily_vol = np.std(log_returns) if np.std(log_returns) > 0 else 0.01

    try:
        lr = LinearRegression()
        lr.fit(train_df[features], train_df['Target'])
        rotalar["Linear_Regression"] = volatile_path_generator(curr, float(lr.predict(X_latest)[0]), periyot_gun, daily_vol)
    except:
        rotalar["Linear_Regression"] = np.full(periyot_gun, curr)

    try:
        rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        rf.fit(train_df[features], train_df['Target'])
        rotalar["Random_Forest"] = volatile_path_generator(curr, float(rf.predict(X_latest)[0]), periyot_gun, daily_vol)
    except:
        rotalar["Random_Forest"] = np.full(periyot_gun, curr)

    try:
        svr = SVR(C=1.0, epsilon=0.2)
        svr.fit(train_df[features], train_df['Target'])
        rotalar["SVR"] = volatile_path_generator(curr, float(svr.predict(X_latest)[0]), periyot_gun, daily_vol)
    except:
        rotalar["SVR"] = np.full(periyot_gun, curr)

    try:
        xgb = XGBRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        xgb.fit(train_df[features], train_df['Target'])
        rotalar["XGBoost"] = volatile_path_generator(curr, float(xgb.predict(X_latest)[0]), periyot_gun, daily_vol)
    except:
        rotalar["XGBoost"] = np.full(periyot_gun, curr)

    try:
        arima_model = ARIMA(hist_prices, order=(1, 1, 1))
        arima_fit = arima_model.fit()
        rotalar["ARIMA"] = arima_fit.forecast(steps=periyot_gun)
    except:
        rotalar["ARIMA"] = np.full(periyot_gun, curr)

    n_sim = 10000
    try:
        mu = np.mean(log_returns)
        Z = np.random.normal(0, 1, (n_sim, periyot_gun))
        drift = mu - 0.5 * (daily_vol ** 2)
        growth = np.exp(drift + daily_vol * Z)
        cum_growth = np.cumprod(growth, axis=1)
        mc_paths = curr * cum_growth
        rotalar["Monte_Carlo"] = np.mean(mc_paths, axis=0)
        mc_upper = np.percentile(mc_paths, 95, axis=0)
        mc_lower = np.percentile(mc_paths, 5, axis=0)
    except:
        rotalar["Monte_Carlo"] = np.full(periyot_gun, curr)
        mc_upper = np.full(periyot_gun, curr)
        mc_lower = np.full(periyot_gun, curr)

    agirliklar = {"ARIMA": 0.20, "Monte_Carlo": 0.25, "Random_Forest": 0.20, "XGBoost": 0.15, "Linear_Regression": 0.10, "SVR": 0.10}
    base_path = np.zeros(periyot_gun)
    toplam_w = 0
    for m_adi, m_pred in rotalar.items():
        w = agirliklar.get(m_adi, 0.1)
        base_path += np.array(m_pred) * w
        toplam_w += w
    konsensus_rota = base_path / toplam_w if toplam_w > 0 else np.full(periyot_gun, curr)

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
    periyotlar = [("1 Gün", 1), ("1 Hafta", 7), ("1 Ay", 30), ("3 Ay", 90), ("6 Ay", 180), ("1 Yıl", 365), ("2 Yıl", 730), ("5 Yıl", 1825)]
    for l, d in periyotlar:
        if d <= periyot_gun:
            tahmin_native = konsensus_rota[d-1]
            tahmin_scaled = tahmin_native * kur_val
            r = (tahmin_native - curr) / curr
            gelecek_tablo.append({"Vade": l, "Tahmin": round(tahmin_scaled, 2), "Nominal Getiri %": round(r * 100, 2), "Sermaye Karşılığı": round(ana_para * (1 + r), 2)})

    destek, direnc = destek_direnc_bul(df)
    return {
        "konsensus_rota": konsensus_rota * kur_val,
        "mc_upper": mc_upper * kur_val,
        "mc_lower": mc_lower * kur_val,
        "rotalar": {k: v * kur_val for k, v in rotalar.items()},
        "stats": {
            **risk_stats,
            "Beta": beta,
        },
        "gelecek_df": pd.DataFrame(gelecek_tablo),
        "boga": float(np.max(konsensus_rota) * kur_val),
        "ayi": float(np.min(konsensus_rota) * kur_val),
        "destek": destek * kur_val,
        "direnc": direnc * kur_val
    }
