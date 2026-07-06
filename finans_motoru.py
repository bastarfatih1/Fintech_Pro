import numpy as np
import pandas as pd
import gc
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from datetime import timedelta

# Makine Öğrenimi Kütüphaneleri
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.linear_model import LinearRegression

# Ağır kütüphaneleri (LSTM, ARIMA, XGBoost) import ederken sistemin çökmemesi için try-except kullanıyoruz.
try:
    from statsmodels.tsa.arima.model import ARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False





def get_kurlar():
    # API KEY'inizi buraya girin
    API_KEY = "de8106e54912c5541f0b97fa" 
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
    
    try:
        # Sunucu takılmalarına karşı timeout (5 saniye) eklendi
        response = requests.get(url, timeout=5)
        response.raise_for_status() # HTTP 200 harici hatada (örn: sınır aşımı) direkt except'e atlar
        
        rates = response.json().get('conversion_rates', {})
        
        # Dönüştürücü modülünün matematiksel olarak doğru çalışması için
        # kurların "1 USD = X Birim" formatında saf olarak dönmesi zorunludur.[cite: 2]
        return {
            "USD": 1.0, 
            "TRY": rates.get('TRY', 34.0), 
            "EUR": rates.get('EUR', 0.92), 
            "CNY": rates.get('CNY', 7.25),
            "RUB": rates.get('RUB', 88.0), 
            "SAR": rates.get('SAR', 3.75),
            "KWD": rates.get('KWD', 0.30), 
            "JPY": rates.get('JPY', 160.0)
        }
    except Exception as e:
        print(f"[API Hatası] {e}")
        # API çökerse veya sınır (limit) aşılırsa çeviri matematiğini bozmayacak DOĞRU yedek oranlar[cite: 2]
        return {
            "USD": 1.0, "TRY": 34.0, "EUR": 0.92, "CNY": 7.25, "RUB": 88.0, "SAR": 3.75, "KWD": 0.30, "JPY": 160.0
        }

def hesapla_gecmis_performans(data, curr_price, ana_para, kur_val, sembol):
    # Bu fonksiyon önceki halinde çok iyi tasarlandığı için aynı bırakıldı.
    sonuclar = []
    bugun = data.index[-1].tz_localize(None) 
    
    kur_data = None
    curr_kur = 1.0
    
    if sembol == "₺":
        try:
            import yfinance as yf
            kur_ticker = yf.Ticker("USDTRY=X")
            kur_data = kur_ticker.history(period="10y")
            kur_data.index = kur_data.index.tz_localize(None)
            if not kur_data.empty:
                curr_kur = float(kur_data['Close'].iloc[-1])
        except:
            pass 
            
    zaman_farklari = {
        "1 Gün": timedelta(days=1), "1 Hafta": timedelta(days=7),
        "1 Ay": timedelta(days=30), "3 Ay": timedelta(days=90),
        "6 Ay": timedelta(days=180), "1 Yıl": timedelta(days=365),
        "3 Yıl": timedelta(days=1095), "5 Yıl": timedelta(days=1825)
    }
    
    data_temiz = data.copy()
    data_temiz.index = data_temiz.index.tz_localize(None)
    
    for isim, fark in zaman_farklari.items():
        hedef_tarih = bugun - fark
        gecmis_veri = data_temiz[data_temiz.index <= hedef_tarih]
        
        if not gecmis_veri.empty:
            gecmis_fiyat_usd = float(gecmis_veri['Close'].iloc[-1])
            curr_fiyat_usd = curr_price
            
            if kur_data is not None and sembol == "₺":
                gecmis_kur_veri = kur_data[kur_data.index <= hedef_tarih]
                if not gecmis_kur_veri.empty:
                    gecmis_kur = float(gecmis_kur_veri['Close'].iloc[-1])
                    gecmis_fiyat = gecmis_fiyat_usd * gecmis_kur
                    curr_fiyat = curr_fiyat_usd * curr_kur
                else:
                    gecmis_fiyat = gecmis_fiyat_usd
                    curr_fiyat = curr_fiyat_usd
            else:
                gecmis_fiyat = gecmis_fiyat_usd
                curr_fiyat = curr_fiyat_usd
                
            getiri_yuzde = ((curr_fiyat - gecmis_fiyat) / gecmis_fiyat) * 100
            kar_zarar_miktari = ana_para * (getiri_yuzde / 100)
            toplam_bakiye = ana_para + kar_zarar_miktari
            isaret = "+" if kar_zarar_miktari >= 0 else "-"
            
            sonuclar.append({
                "Dönem": isim,
                "Gerçekleşen Getiri": f"%{'+' if getiri_yuzde >= 0 else ''}{getiri_yuzde:.1f}",
                "Net Kâr / Zarar": f"{isaret} {sembol}{abs(kar_zarar_miktari):,.0f}",
                "Toplam Bakiye": f"{sembol}{toplam_bakiye:,.0f}"
            })
        else:
            sonuclar.append({"Dönem": isim, "Gerçekleşen Getiri": "Veri Yok", "Net Kâr / Zarar": "-", "Toplam Bakiye": "-"})
            
    return pd.DataFrame(sonuclar)

# --- YENİ EKLENEN KISIM: ORKESTRATÖR VE KONSENSÜS MOTORU ---

def hazirla_ml_verisi(data):
    df = pd.DataFrame(data['Close'].copy())
    df['Lag_1'] = df['Close'].shift(1)
    df['Lag_3'] = df['Close'].shift(3)
    df['Lag_7'] = df['Close'].shift(7)
    df['MA_14'] = df['Close'].rolling(window=14).mean()
    df = df.dropna()
    
    X = df[['Lag_1', 'Lag_3', 'Lag_7', 'MA_14']].values
    y = df['Close'].values
    
    # HATA DÜZELTİLDİ: Boyut uyuşmazlığı nedeniyle modellerin çökmesi (Düz çizgi hatası) engellendi.
    X_gelecek = np.array([
        df['Close'].iloc[-1],  
        df['Lag_1'].iloc[-1], 
        df['Lag_3'].iloc[-1], 
        df['MA_14'].iloc[-1]   
    ]).reshape(1, -1)
    
    return X, y, X_gelecek

# periyot_gun argümanını varsayılan olarak 1095 (3 yıl) olarak değiştirdik[cite: 2]
def gelecek_senaryolari_hesapla(data, curr, ana_para, kur_val, sembol_isareti, periyot_gun=1095):
    data_kisa = data.tail(1500).copy()
    tahmin_havuzu = {}
    rotalar = {}
    
    # 1. Monte Carlo Simülasyonu
    returns = data_kisa['Close'].pct_change().dropna()
    mu, sigma = returns.mean(), returns.std()
    sim = np.zeros((periyot_gun, 500))
    for i in range(500):
        sim[:, i] = curr * np.exp(np.cumsum((mu - 0.5 * sigma**2) + sigma * np.random.normal(0, 1, periyot_gun)))
    
    mc_path = np.mean(sim, axis=1)
    tahmin_havuzu['monte_carlo'] = mc_path[-1]
    rotalar['monte_carlo'] = mc_path

    # --- ML VERİ HAZIRLIĞI & MODEL ÇÖKME KORUMASI ---
    X, y, X_gelecek = hazirla_ml_verisi(data_kisa)
    
    def smooth_path(start, end, steps):
        return np.geomspace(start, end, steps)

    # 2. Linear Regression
    try:
        lr_model = LinearRegression()
        lr_model.fit(X, y)
        pred = lr_model.predict(X_gelecek)[0]
        tahmin_havuzu['lin_reg'] = pred
        rotalar['lin_reg'] = smooth_path(curr, pred, periyot_gun)
    except:
        tahmin_havuzu['lin_reg'] = curr
        rotalar['lin_reg'] = np.full(periyot_gun, curr)

    # 3. Random Forest
    try:
        rf_model = RandomForestRegressor(n_estimators=30, max_depth=4, random_state=42)
        rf_model.fit(X, y)
        pred = rf_model.predict(X_gelecek)[0]
        tahmin_havuzu['random_forest'] = pred
        rotalar['random_forest'] = smooth_path(curr, pred, periyot_gun)
    except:
        tahmin_havuzu['random_forest'] = curr
        rotalar['random_forest'] = np.full(periyot_gun, curr)

    # 4. SVR
    try:
        svr_model = SVR(kernel='rbf', C=1.0)
        svr_model.fit(X, y)
        pred = svr_model.predict(X_gelecek)[0]
        tahmin_havuzu['svm'] = pred
        rotalar['svm'] = smooth_path(curr, pred, periyot_gun)
    except:
        tahmin_havuzu['svm'] = curr
        rotalar['svm'] = np.full(periyot_gun, curr)

    # 5. XGBoost
    try:
        import xgboost as xgb
        xgb_model = xgb.XGBRegressor(n_estimators=30, max_depth=3, learning_rate=0.1)
        xgb_model.fit(X, y)
        pred = float(xgb_model.predict(X_gelecek)[0])
        tahmin_havuzu['xgboost'] = pred
        rotalar['xgboost'] = smooth_path(curr, pred, periyot_gun)
    except:
        tahmin_havuzu['xgboost'] = curr
        rotalar['xgboost'] = np.full(periyot_gun, curr)

    # 6. ARIMA
    try:
        from statsmodels.tsa.arima.model import ARIMA
        arima_model = ARIMA(data_kisa['Close'].values[-300:], order=(3,1,0))
        arima_fit = arima_model.fit()
        arima_path = arima_fit.forecast(steps=periyot_gun)
        tahmin_havuzu['arima'] = arima_path[-1]
        rotalar['arima'] = arima_path
    except:
        tahmin_havuzu['arima'] = curr
        rotalar['arima'] = np.full(periyot_gun, curr)

    # Ortak Konsensüs Rotası
    agirliklar = {'xgboost': 0.25, 'arima': 0.20, 'monte_carlo': 0.15, 'lin_reg': 0.15, 'random_forest': 0.15, 'svm': 0.10}
    konsensus_rota = np.zeros(periyot_gun)
    toplam_agirlik = 0
    
    for m, path in rotalar.items():
        w = agirliklar.get(m, 0)
        konsensus_rota += np.array(path) * w
        toplam_agirlik += w
        
    konsensus_rota = konsensus_rota / toplam_agirlik if toplam_agirlik > 0 else np.full(periyot_gun, curr)
    konsensus_fiyat = konsensus_rota[-1]

    # --- DEĞİŞİKLİK BURADA: 5 Yıl satırı tablodan tamamen çıkarıldı, maksimum sınır 3 Yıl (1095 Gün) yapıldı ---
    periyotlar = [
        ("1 Gün", 1), 
        ("1 Hafta", 7), 
        ("1 Ay", 30), 
        ("3 Ay", 90), 
        ("6 Ay", 180), 
        ("1 Yıl", 365), 
        ("3 Yıl", 1095)
    ]
    
    gelecek_tablo = []
    gunluk_getiri_orani = (konsensus_fiyat / curr) ** (1/periyot_gun) - 1 if konsensus_fiyat > 0 else 0
    
    for l, d in periyotlar:
        tahmin = curr * ((1 + gunluk_getiri_orani) ** d)
        r = (tahmin - curr) / curr
        deger = ana_para * (1 + r) if ana_para > 0 else 0
        
        gelecek_tablo.append({
            "Dönem": l, 
            "Ensemble Hedef Fiyat": f"{tahmin:,.2f}", 
            "Beklenen Getiri": f"%{r*100:+.1f}", 
            "Mevduat Karşılığı": f"{sembol_isareti}{deger:,.0f}"
        })

    return {
        "boga": np.percentile(sim[-1], 90),
        "baz": konsensus_fiyat,
        "ayi": np.percentile(sim[-1], 10),
        "gelecek_df": pd.DataFrame(gelecek_tablo).set_index("Dönem"),
        "rotalar": rotalar,
        "konsensus_rota": konsensus_rota
    }