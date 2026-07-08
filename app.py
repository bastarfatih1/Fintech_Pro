import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf
from finans_motoru import get_kurlar, hesapla_gecmis_performans, gelecek_senaryolari_hesapla
from haber_motoru import canli_rss_haber_cek, ai_etki_analizi, ai_teknik_analiz_yorumu, ai_model_yorumu
import streamlit as st
# Basit bir kullanıcı/şifre kontrolü
def check_password():
    st.sidebar.text_input("Kullanıcı Adı", key="user")
    st.sidebar.text_input("Şifre", type="password", key="password")
    if st.sidebar.button("Giriş Yap"):
        if st.session_state.user == "fatih" and st.session_state.password == "123456":
            st.session_state.logged_in = True

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Fintech Alpha Pro Final", layout="wide")
st.markdown("""
    <style>
    .metric-up { color: #00ff88; font-weight: bold; }
    .metric-down { color: #ff4d4d; font-weight: bold; }
    .kur-box { 
        background-color: #1c2541; padding: 15px; border-radius: 10px; 
        text-align: center; border: 1px solid #3a506b;
        color: #ffffff !important; font-size: 18px; font-weight: 700;
        margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .model-desc { font-size: 12px; color: #a0a0a0; margin-top: -10px; padding-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ FinTech Alpha: Kurumsal Risk & Gelişmiş Kantitatif Projeksiyon")
st.markdown("---")

# --- 2. GLOBAL PARAMETRELER VE ÇEVİRİCİ ---
@st.cache_data(ttl=900)
def kurlari_getir_cache():
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        response = requests.get(url, timeout=5).json()
        rates = response['rates']
        return {
            "USD": 1.0, 
            "TRY": float(rates.get('TRY', 34.20)), 
            "EUR": float(rates.get('EUR', 0.92)), 
            "CNY": float(rates.get('CNY', 7.25)),
            "RUB": float(rates.get('RUB', 88.0)), 
            "SAR": float(rates.get('SAR', 3.75)),
            "KWD": float(rates.get('KWD', 0.31)), 
            "JPY": float(rates.get('JPY', 155.0))
        }
    except:
        return {"USD": 1.0, "TRY": 34.20, "EUR": 0.92, "CNY": 7.25, "RUB": 88.0, "SAR": 3.75, "KWD": 0.31, "JPY": 155.0}
kurlar = kurlari_getir_cache()

col_g1, col_g2, col_g3 = st.columns([2, 1, 1])
ana_para = col_g1.number_input("Stratejik Yatırım Tutarı:", value=0.0, step=10000.0)
secilen_kur = col_g2.selectbox("Baz Para Birimi:", ["TRY", "USD", "EUR", "CNY", "RUB", "JPY", "SAR", "KWD"])

enstrumanlar = {
    "BIST 100": "XU100.IS", 
    "Bitcoin (BTC)": "BTC-USD", 
    "Altın (Ons)": "GC=F", 
    "Gümüş (Ons)": "SI=F", 
    "S&P 500": "^GSPC"
}    
secilen_varlik = col_g3.selectbox("Analiz Edilecek Varlık:", list(enstrumanlar.keys()))

sembol_sozluk = {"TRY": "₺", "USD": "$", "EUR": "€", "CNY": "¥", "RUB": "₽", "JPY": "¥", "SAR": "﷼", "KWD": "د.ك"}
s = sembol_sozluk[secilen_kur]
kur_val = kurlar.get(secilen_kur, 1.0)
usd_baz = ana_para / kurlar[secilen_kur] if ana_para > 0 else 0.0

st.write("💵 **Mevduatın Anlık Karşılığı:**")
k1, k2, k3, k4 = st.columns(4)
k5, k6, k7, k8 = st.columns(4)

def hesapla_ve_goster(col, bayrak, hedef_kod, birim):
    if hedef_kod in kurlar and secilen_kur in kurlar:
        tutar = (ana_para / kurlar[secilen_kur]) * kurlar[hedef_kod]
        col.markdown(f"<div class='kur-box'>{bayrak} {tutar:,.2f} {birim}</div>", unsafe_allow_html=True)
    else:
        col.markdown(f"<div class='kur-box'>{bayrak} N/A {birim}</div>", unsafe_allow_html=True)

hesapla_ve_goster(k1, "🇹🇷", "TRY", "TL")
hesapla_ve_goster(k2, "🇺🇸", "USD", "USD")
hesapla_ve_goster(k3, "🇪🇺", "EUR", "EUR")
hesapla_ve_goster(k4, "🇨🇳", "CNY", "CNY")
hesapla_ve_goster(k5, "🇷🇺", "RUB", "RUB")
hesapla_ve_goster(k6, "🇯🇵", "JPY", "JPY")
hesapla_ve_goster(k7, "🇸🇦", "SAR", "SAR")
hesapla_ve_goster(k8, "🇰🇼", "KWD", "KWD")

st.divider()

# --- 3. PİYASA KARTLARI ---
def show_card(col, label, kur_key, yf_symbol=""):
    try:
        kurlar_kart = kurlari_getir_cache()
        usd_try = kurlar_kart.get("TRY", 34.20)
        
        if kur_key == "USD":
            val = usd_try
        else:
            hedef_usd_parite = kurlar_kart.get(kur_key, 1.0)
            val = usd_try / hedef_usd_parite if hedef_usd_parite > 0 else 0.0
            
        pct_text = "▲ 0.00%"
        pct_color = "#00ff88"
        
        if yf_symbol:
            try:
                import yfinance as yf
                
                if yf_symbol in ["CNYTRY=X", "RUBTRY=X", "SARTRY=X", "KWDTRY=X"]:
                    hedef_kod = yf_symbol[:3]
                    
                    usd_try_data = yf.Ticker("USDTRY=X").history(period="5d")
                    usd_hedef_data = yf.Ticker(f"{hedef_kod}=X").history(period="5d")
                    
                    if len(usd_try_data) >= 2 and len(usd_hedef_data) >= 2:
                        prev_cross = usd_try_data['Close'].iloc[-2] / usd_hedef_data['Close'].iloc[-2]
                        curr_cross = usd_try_data['Close'].iloc[-1] / usd_hedef_data['Close'].iloc[-1]
                        
                        pct = ((curr_cross - prev_cross) / prev_cross) * 100
                        pct_color = "#00ff88" if pct >= 0 else "#ff4d4d"
                        pct_text = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.2f}%"
                        
                else:
                    data = yf.Ticker(yf_symbol).history(period="5d")
                    if len(data) >= 2:
                        prev = data['Close'].iloc[-2]
                        curr = data['Close'].iloc[-1]
                        
                        pct = ((curr - prev) / prev) * 100
                        pct_color = "#00ff88" if pct >= 0 else "#ff4d4d"
                        pct_text = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.2f}%"
            except Exception:
                pass
                
        with col:
            with st.container(border=True):
                st.write(f"**{label}**")
                st.markdown(f"### {val:,.2f}")
                st.markdown(f"<span style='color: {pct_color}'>{pct_text}</span>", unsafe_allow_html=True)
                
    except Exception:
        pass

st.subheader("📊 Canlı Piyasa Göstergeleri")
r1_1, r1_2, r1_3 = st.columns(3)
show_card(r1_1, "USD/TRY", "USD", "USDTRY=X")
show_card(r1_2, "EUR/TRY", "EUR", "EURTRY=X")
show_card(r1_3, "Yuan (CNY)", "CNY", "CNYTRY=X")

r2_1, r2_2, r2_3 = st.columns(3)
show_card(r2_1, "Ruble (RUB)", "RUB", "RUBTRY=X")
show_card(r2_2, "Riyal (SAR)", "SAR", "SARTRY=X")
show_card(r2_3, "Dinar (KWD)", "KWD", "KWDTRY=X")

st.divider()

# --- 4. ANALİZ ODASI & BUTON HAFIZASI ---
@st.cache_data(ttl=600)
def haberleri_getir_cache(kelime):
    return canli_rss_haber_cek(kelime)

if "analiz_tamam" not in st.session_state:
    st.session_state.analiz_tamam = False

sembol = enstrumanlar[secilen_varlik]

if st.button("🚀 Gelişmiş AI & Gelecek Projeksiyonunu Başlat", use_container_width=True, type="primary"):
    st.session_state.analiz_tamam = True

if st.session_state.analiz_tamam:
    
    with st.spinner(f'{secilen_varlik} verileri işleniyor, Trading görünümü oluşturuluyor...'):
        ticker = yf.Ticker(sembol)
        data = ticker.history(period="10y")
        
        if data is not None and not data.empty:
            curr = float(data['Close'].iloc[-1])
            haberler = haberleri_getir_cache(secilen_varlik.split("(")[0])
            gelecek = gelecek_senaryolari_hesapla(data, curr, ana_para, kur_val, s)
            
            # --- 1. EN ÜST: TRADINGVIEW BENZERİ PROFESYONEL GRAFİK ---
            st.markdown(f"### 📡 {secilen_varlik} - Canlı Etkileşimli Piyasa Terminali")
            
            grafik_veri = data.tail(150).copy() 
            grafik_veri['SMA20'] = grafik_veri['Close'].rolling(window=20).mean() 
            
            fig_ana = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            fig_ana.add_trace(go.Candlestick(x=grafik_veri.index, open=grafik_veri['Open'], 
                                             high=grafik_veri['High'], low=grafik_veri['Low'], 
                                             close=grafik_veri['Close'], name='Fiyat'), row=1, col=1)
            
            fig_ana.add_trace(go.Scatter(x=grafik_veri.index, y=grafik_veri['SMA20'], 
                                         line=dict(color='orange', width=1.5), name='SMA 20'), row=1, col=1)
            
            colors = ['#00ff88' if row['Close'] >= row['Open'] else '#ff4d4d' for index, row in grafik_veri.iterrows()]
            fig_ana.add_trace(go.Bar(x=grafik_veri.index, y=grafik_veri['Volume'], 
                                     marker_color=colors, name='Hacim'), row=2, col=1)
            
            fig_ana.update_layout(
                template="plotly_dark", height=550, margin=dict(l=0, r=0, t=10, b=0),
                xaxis_rangeslider_visible=False, showlegend=False,
                yaxis=dict(title="Fiyat"), yaxis2=dict(title="Hacim", showgrid=False)
            )
            
            fig_ana.update_xaxes(
                rangeslider_visible=False,
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1A", step="month", stepmode="backward"),
                        dict(count=3, label="3A", step="month", stepmode="backward"),
                        dict(count=6, label="6A", step="month", stepmode="backward"),
                        dict(step="all", label="Tümü")
                    ]), bgcolor="#1c2541", activecolor="#3a506b"
                )
            )
            st.plotly_chart(fig_ana, use_container_width=True)
            
            st.info(f"**🤖 AI Teknik Analiz Yorumu:** {ai_teknik_analiz_yorumu(secilen_varlik, curr, gelecek['boga'], gelecek['ayi'])}")
            
            st.divider()

            # --- SEKME SİSTEMİ ---
            tab_gecmis, tab_gelecek = st.tabs(["📅 Geçmiş Performans", "🔮 Gelecek Projeksiyonu (AI)"])
            
            with tab_gecmis:
                st.markdown("### 📊 Gerçekleşen Getiriler ve Mevduat Karşılığı")
                df_tablo = hesapla_gecmis_performans(data, curr, ana_para, kur_val, s)
                st.table(df_tablo)

            with tab_gelecek:
                st.markdown("### 🧠 AI ve ML Algoritmalarının Bireysel Mum Projeksiyonları")
                
                zaman_secenekleri = {
                    "1 Gün": 1, "1 Hafta": 7, "1 Ay": 30, "3 Ay": 90, "6 Ay": 180, 
                    "1 Yıl": 365, "2 Yıl": 730, "3 Yıl": 1095, "4 Yıl": 1460, "5 Yıl": 1825
                }
                
                c1, c2 = st.columns([1, 3])
                with c1:
                    secilen_vade = st.selectbox("Tüm Modeller İçin Projeksiyon Vadesi Seçin:", list(zaman_secenekleri.keys()), index=4) 
                hedef_gun = zaman_secenekleri[secilen_vade]
                
                st.divider()
                
                if "rotalar" in gelecek:
                    model_isimleri = list(gelecek["rotalar"].keys())
                    cols = st.columns(3)
                    
                    for i, model_adi in enumerate(model_isimleri):
                        col = cols[i % 3] 
                        with col:
                            with st.container(border=True):
                                st.markdown(f"**{model_adi.replace('_', ' ').upper()}**")
                                
                                tam_rota = gelecek["rotalar"][model_adi]
                                gosterilecek_gun = min(hedef_gun, len(tam_rota))
                                if gosterilecek_gun == 0: gosterilecek_gun = 1
                                rota_kesiti = tam_rota[:gosterilecek_gun]
                                
                                model_son_fiyat = rota_kesiti[-1]
                                model_fark = ((model_son_fiyat - curr) / curr) * 100
                                
                                renk = "#00ff88" if model_fark >= 0 else "#ff4d4d"
                                yon_ok = "▲" if model_fark >= 0 else "▼"
                                
                                np.random.seed(42) 
                                sim_open = [curr] + list(rota_kesiti[:-1])
                                sim_high = [max(o, c) * (1 + np.random.uniform(0.001, 0.005)) for o, c in zip(sim_open, rota_kesiti)]
                                sim_low = [min(o, c) * (1 - np.random.uniform(0.001, 0.005)) for o, c in zip(sim_open, rota_kesiti)]
                                
                                fig_mini = go.Figure(data=[go.Candlestick(
                                    x=list(range(len(rota_kesiti))), open=sim_open, high=sim_high, low=sim_low, close=rota_kesiti
                                )])
                                
                                fig_mini.update_layout(
                                    height=120, margin=dict(l=0, r=0, t=0, b=0),
                                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode=False,
                                    xaxis_rangeslider_visible=False
                                )
                                st.plotly_chart(fig_mini, use_container_width=True)
                                
                                st.markdown(f"<h4 style='text-align: center; color: {renk}; margin-top:-10px;'>{yon_ok} %{abs(model_fark):.2f}</h4>", unsafe_allow_html=True)
                                
                                with st.spinner(f"AI Analiz Ediyor..."):
                                    ai_aciklama = ai_model_yorumu(model_adi, secilen_varlik, curr, model_son_fiyat, secilen_vade)
                                st.markdown(f"<div class='model-desc'>🤖 {ai_aciklama}</div>", unsafe_allow_html=True)
                
                st.divider()

                # --- 4. ORTAK PAYDA KONSENSÜSÜ ---
                st.markdown("### 🎯 Kolektif Gelecek Projeksiyonu (Ortak Payda)")
                
                if "konsensus_rota" in gelecek:
                    tam_rota = gelecek["konsensus_rota"]
                    gosterilecek_gun = min(hedef_gun, len(tam_rota)) 
                    rota_kesiti = tam_rota[:gosterilecek_gun]
                    
                    gelecek_tarihler = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=len(rota_kesiti))
                    
                    fig_gelecek = go.Figure()
                    fig_gelecek.add_trace(go.Scatter(x=gelecek_tarihler, y=rota_kesiti, mode='lines', fill='tozeroy', name='Ortak Payda', line=dict(color='#00bbff', width=2)))
                    fig_gelecek.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=10, b=0))
                    
                    st.plotly_chart(fig_gelecek, use_container_width=True)
                
                st.markdown(f"**Tüm Vadeler İçin Detaylı Projeksiyon Tablosu**")
                st.table(gelecek["gelecek_df"])
