import numpy as np
import pandas as pd
import requests
import warnings
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor
from statsmodels.tsa.arima.model import ARIMA
import yfinance as yf

warnings.filterwarnings('ignore')

def get_kurlar():
    API_KEY = "de8106e54912c5541f0b97fa" 
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        rates = response.json().get('conversion_rates', {})
        return {
            "USD": 1.0, "TRY": rates.get('TRY', 34.20), "EUR": rates.get('EUR', 0.92), 
            "CNY": rates.get('CNY', 7.25), "RUB": rates.get('RUB', 88.0), 
            "SAR": rates.get('SAR', 3.75), "KWD": rates.get('KWD', 0.31), "JPY": rates.get('JPY', 155.0)
        }
    except Exception:
        return {
            "USD": 1.0, "TRY": 34.20, "EUR": 0.92, "CNY": 7.25, 
            "RUB": 88.0, "SAR": 3.75, "KWD": 0.31, "JPY": 155.0
        }

def volatile_path_generator(curr, target, days, daily_vol):
    if days <= 1:
        return np.array([target])
    returns = np.random.normal(0, daily_vol, days)
    returns = returns - np.mean(returns)
    path = np.exp(np.cumsum(returns))
    scaled_path = curr + (path - path[0]) * ((target - curr) / (path[-1] - path[0] + 1e-9))
    return scaled_path

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

    returns = np.diff(hist_prices) / hist_prices[:-1]
    sharpe = float(np.mean(returns) / (np.std(returns) + 1e-9) * np.sqrt(252)) if len(returns) > 1 else 0.0
    downside_returns = returns[returns < 0]
    sortino_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-9
    sortino = float(np.mean(returns) / sortino_std * np.sqrt(252)) if len(returns) > 1 else 0.0
    var_95 = float(np.percentile(returns, 5)) if len(returns) > 1 else 0.0
    cum_returns = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(cum_returns)
    max_dd = float(np.min((cum_returns - peak) / (peak + 1e-9))) if len(cum_returns) > 1 else 0.0
    
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
        "stats": {"VaR": var_95, "Sharpe": sharpe, "Sortino": sortino, "MaxDD": max_dd, "Beta": beta},
        "gelecek_df": pd.DataFrame(gelecek_tablo),
        "boga": float(np.max(konsensus_rota) * kur_val),
        "ayi": float(np.min(konsensus_rota) * kur_val),
        "destek": destek * kur_val,
        "direnc": direnc * kur_val
    }
