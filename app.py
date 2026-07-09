import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf
import time

from finans_motoru import (
    get_kurlar, 
    hesapla_gecmis_performans, 
    gelecek_senaryolari_hesapla
)
from haber_motoru import (
    canli_rss_haber_cek, 
    ai_etki_analizi, 
    ai_teknik_analiz_yorumu,
    ai_toplu_model_yorumlari
)

# --- 1. AYARLAR VE TASARIM (Koyu Tema & Kurumsal) ---
st.set_page_config(
    page_title="Fintech Alpha Pro | Kurumsal Risk Terminali", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Kurumsal Koyu Tema (Bloomberg Hissi) */
    .stApp { background-color: #0B1020; }
    
    /* Canlı Ticker Bar */
    .ticker-bar {
        background: linear-gradient(90deg, #131a30 0%, #1c2541 50%, #131a30 100%);
        color: #00bbff; padding: 10px; font-weight: bold; font-family: monospace;
        border-bottom: 2px solid #233556; margin-bottom: 20px;
    }
    
    /* Kart Gölgeleri ve Yüzeyler */
    .kur-box { 
        background: linear-gradient(145deg, #1a2238, #131a2f); 
        padding: 15px; border-radius: 8px; text-align: center; 
        border: 1px solid #233556; color: #ffffff !important; 
        font-size: 18px; font-weight: 700; margin-bottom: 10px; 
        box-shadow: 0px 4px 12px rgba(0,0,0,0.5);
    }
    .metric-up { color: #00ff88; font-weight: bold; }
    .metric-down { color: #ff4d4d; font-weight: bold; }
    
    .news-card {
        background-color: #131a30; padding: 18px; border-radius: 8px;
        border: 1px solid #233556; margin-bottom: 15px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.3); transition: 0.3s;
    }
    .news-card:hover { border-color: #00bbff; }
    
    /* Alt Sabit Menü (Action Buttons) */
    .floating-action-bar {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #0B1020; border-top: 1px solid #233556;
        padding: 10px 50px; z-index: 999; display: flex; justify-content: space-around;
    }
    
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #131a30, #0B1020);
        border: 1px solid #233556; padding: 20px; border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] { color: #00ff88; font-size: 1.8rem; font-weight: 800; }        
    </style>
""", unsafe_allow_html=True)

# Canlı Ticker
st.markdown('<div class="ticker-bar"><marquee scrollamount="5">S&P 500: ▲ 5,420.20 (+0.4%) &nbsp;&nbsp;|&nbsp;&nbsp; NASDAQ: ▲ 17,215.30 (+0.6%) &nbsp;&nbsp;|&nbsp;&nbsp; BIST 100: ▼ 9,850.40 (-1.2%) &nbsp;&nbsp;|&nbsp;&nbsp; BTC/USD: ▲ 66,200 (+1.8%) &nbsp;&nbsp;|&nbsp;&nbsp; XAU/USD: ▲ 2,340 (+0.2%)</marquee></div>', unsafe_allow_html=True)

# --- YAPAY ZEKA KONTROL PANELİ ---
st.sidebar.title("🏛️ Terminal Kontrolü")
st.sidebar.caption("Yapay Zeka & Kantitatif Risk Motoru")
st.sidebar.divider()

@st.cache_data(ttl=900)
def kurlari_getir_cache():
    return get_kurlar()

kurlar = kurlari_getir_cache()

# Ana Parametreler
col_g1, col_g2, col_g3, col_g4 = st.columns([2, 1, 1, 1])
ana_para = col_g1.number_input("Stratejik Yatırım Tutarı:", value=0.0, step=10000.0)
secilen_kur = col_g2.selectbox("Baz Para Birimi:", ["TRY", "USD", "EUR", "CNY", "RUB", "JPY", "SAR", "KWD"])

enstrumanlar = {
    "BIST 100": "XU100.IS", 
    "Bitcoin (BTC)": "BTC-USD", 
    "Altın (Ons)": "GC=F", 
    "Gümüş (Ons)": "SI=F", 
    "S&P 500": "^GSPC",
    "NVIDIA": "NVDA",
    "APPLE": "AAPL"
}    
secilen_varlik = col_g3.selectbox("Analiz Edilecek Varlık:", list(enstrumanlar.keys()))

zaman_secenekleri = {
    "1 Ay": 30, "3 Ay": 90, "6 Ay": 180, "1 Yıl": 365, "3 Yıl": 1095, "5 Yıl": 1825
}
secilen_vade = col_g4.selectbox("Projeksiyon Vadesi:", list(zaman_secenekleri.keys()), index=3)
hedef_gun = zaman_secenekleri[secilen_vade]

sembol_sozluk = {"TRY": "₺", "USD": "$", "EUR": "€", "CNY": "¥", "RUB": "₽", "JPY": "¥", "SAR": "﷼", "KWD": "د.k"}
s = sembol_sozluk[secilen_kur]
kur_val = kurlar.get(secilen_kur, 1.0)

st.divider()

@st.cache_data(ttl=600)
def haberleri_getir_cache(kelime):
    return canli_rss_haber_cek(kelime)

@st.cache_data(ttl=3600)
def varlik_verisi_getir(sembol):
    return yf.Ticker(sembol).history(period="10y")

if "analiz_tamam" not in st.session_state:
    st.session_state.analiz_tamam = False

sembol = enstrumanlar[secilen_varlik]

if st.button("🚀 Kurumsal Gelişmiş AI Projeksiyonunu Başlat", use_container_width=True, type="primary"):
    st.session_state.analiz_tamam = True

if st.session_state.analiz_tamam:
    progress_text = "Veriler işleniyor, kantitatif modeller çalıştırılıyor..."
    my_bar = st.progress(0, text=progress_text)
    
    try:
        data = varlik_verisi_getir(sembol)
        my_bar.progress(30, text="Finansal geçmiş yüklendi.")
        
        if data is not None and not data.empty:
            curr = float(data['Close'].iloc[-1])
            haberler = haberleri_getir_cache(secilen_varlik.split("(")[0])
            my_bar.progress(50, text="Monte Carlo simülasyonları ve ML rota optimizasyonu tamamlanıyor...")
            
            gelecek = gelecek_senaryolari_hesapla(
                data=data, curr=curr, ana_para=ana_para, periyot_gun=hedef_gun, kur_val=kur_val
            )
            my_bar.progress(80, text="Risk metrikleri hesaplanıyor...")
            
            # Üst Menü (Tabs)
            tabs = st.tabs(["📊 Dashboard (Grafik & Risk)", "🔮 AI Forecast & Modeller", "📰 Haber Analizi", "📈 Performans"])
            my_bar.progress(100, text="Tamamlandı.")
            time.sleep(0.5)
            my_bar.empty()
            
            with tabs[0]:
                st.markdown(f"### 📡 {secilen_varlik} - Merkezi Terminal")
                
                # RİSK METRİKLERİ KARTLARI
                stats = gelecek["stats"]
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("📉 Max Drawdown", f"%{stats['MaxDD']*100:.2f}")
                c2.metric("🛡️ 95% VaR", f"%{stats['VaR']*100:.2f}")
                c3.metric("⚖️ Sharpe Rasyosu", f"{stats['Sharpe']:.2f}")
                c4.metric("⚖️ Sortino Rasyosu", f"{stats['Sortino']:.2f}")
                c5.metric("🔗 Beta Katsayısı", f"{stats['Beta']:.2f}")
                
                st.markdown("---") 
                
                # TRADINGVIEW SEVİYESİ GRAFİK
                grafik_veri = data.tail(250).copy() 
                grafik_veri['EMA20'] = grafik_veri['Close'].ewm(span=20, adjust=False).mean()
                grafik_veri['EMA50'] = grafik_veri['Close'].ewm(span=50, adjust=False).mean()
                grafik_veri['EMA200'] = grafik_veri['Close'].ewm(span=200, adjust=False).mean()
                
                # RSI Uyarısı
                rsi_son = grafik_veri['Close'].diff().apply(lambda x: x if x > 0 else 0).rolling(14).mean() / (abs(grafik_veri['Close'].diff().apply(lambda x: x if x < 0 else 0)).rolling(14).mean() + 1e-9)
                rsi_val = 100 - (100 / (1 + rsi_son.iloc[-1]))
                if rsi_val > 70:
                    st.warning(f"⚠️ Teknik Uyarı: RSI seviyesi ({rsi_val:.1f}) varlığın aşırı alındığına işaret ediyor.")
                elif rsi_val < 30:
                    st.success(f"✅ Teknik Uyarı: RSI seviyesi ({rsi_val:.1f}) varlığın aşırı satıldığını (dip) gösteriyor.")
                
                fig_ana = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                
                # Mumlar
                fig_ana.add_trace(go.Candlestick(x=grafik_veri.index, open=grafik_veri['Open'], high=grafik_veri['High'], low=grafik_veri['Low'], close=grafik_veri['Close'], name='Fiyat'), row=1, col=1)
                
                # EMAs
                fig_ana.add_trace(go.Scatter(x=grafik_veri.index, y=grafik_veri['EMA20'], line=dict(color='blue', width=1), name='EMA 20'), row=1, col=1)
                fig_ana.add_trace(go.Scatter(x=grafik_veri.index, y=grafik_veri['EMA50'], line=dict(color='orange', width=1.2), name='EMA 50'), row=1, col=1)
                fig_ana.add_trace(go.Scatter(x=grafik_veri.index, y=grafik_veri['EMA200'], line=dict(color='white', width=1.5, dash='dot'), name='EMA 200'), row=1, col=1)
                
                # Hedef Bölgeleri (Yarı saydam)
                fig_ana.add_hrect(y0=gelecek['ayi'], y1=curr*kur_val, fillcolor="red", opacity=0.05, layer="below", line_width=0, row=1, col=1)
                fig_ana.add_hrect(y0=curr*kur_val, y1=gelecek['boga'], fillcolor="green", opacity=0.05, layer="below", line_width=0, row=1, col=1)

                # Renkli Hacim
                colors = ['#00ff88' if r['Close'] >= r['Open'] else '#ff4d4d' for idx, r in grafik_veri.iterrows()]
                fig_ana.add_trace(go.Bar(x=grafik_veri.index, y=grafik_veri['Volume'], marker_color=colors, name='Hacim'), row=2, col=1)
                
                # Grafik Ayarları (Zoom, Pan, Crosshair)
                fig_ana.update_layout(
                    template="plotly_dark", height=650, margin=dict(l=0, r=0, t=10, b=0), 
                    xaxis_rangeslider_visible=False, showlegend=True,
                    hovermode='x unified', dragmode='pan'
                )
                fig_ana.update_xaxes(showspikes=True, spikecolor="gray", spikesnap="cursor", spikemode="across")
                fig_ana.update_yaxes(showspikes=True, spikecolor="gray", spikemode="across")
                st.plotly_chart(fig_ana, use_container_width=True, config={'scrollZoom': True})
                
                st.info(f"**🤖 AI Sentezi:** {ai_teknik_analiz_yorumu(secilen_varlik, curr, gelecek['boga'], gelecek['ayi'])}")

            with tabs[1]:
                st.markdown("### 🎯 Kurumsal Konsensüs & AI Projeksiyonu")
                
                # KONSENSÜS GRAFİĞİ (GÜVEN KORİDORLU)
                rota_kesiti = gelecek["konsensus_rota"]
                mc_upper = gelecek["mc_upper"]
                mc_lower = gelecek["mc_lower"]
                gelecek_tarihler = pd.date_range(start=data.index[-1] + pd.Timedelta(days=1), periods=len(rota_kesiti))
                
                fig_gelecek = go.Figure()
                
                # %90 Güven Bandı (Monte Carlo)
                fig_gelecek.add_trace(go.Scatter(x=gelecek_tarihler, y=mc_upper, mode='lines', line=dict(width=0), showlegend=False))
                fig_gelecek.add_trace(go.Scatter(x=gelecek_tarihler, y=mc_lower, mode='lines', fill='tonexty', fillcolor='rgba(0, 187, 255, 0.1)', line=dict(width=0), name='90% MC Güven Koridoru'))
                
                # Modeller
                renk_paleti = ['#FF4B4B', '#00E676', '#E040FB', '#FFD54F', '#00B0FF', '#FF9100']
                for i, (m_adi, m_rota) in enumerate(gelecek["rotalar"].items()):
                    if m_adi != "Monte_Carlo":
                        fig_gelecek.add_trace(go.Scatter(x=gelecek_tarihler, y=m_rota, mode='lines', name=m_adi.upper(), line=dict(color=renk_paleti[i % len(renk_paleti)], width=1.5, dash='dash')))
                
                # Ana Konsensüs
                fig_gelecek.add_trace(go.Scatter(x=gelecek_tarihler, y=rota_kesiti, mode='lines', name='🎯 AĞIRLIKLI KONSENSÜS', line=dict(color='#00ff88', width=4)))
                
                fig_gelecek.update_layout(template="plotly_dark", height=550, hovermode='x unified')
                st.plotly_chart(fig_gelecek, use_container_width=True)

                st.markdown("#### Detaylı Gelecek Değerlemeleri")
                st.table(gelecek["gelecek_df"])

            with tabs[2]:
                st.markdown("### 📰 Gerçek Zamanlı AI Duyarlılık (Sentiment) Analizi")
                if haberler:
                    for h in haberler:
                        with st.container():
                            st.markdown(f"<div class='news-card'><h4><a href='{h['link']}' target='_blank' style='color:#00bbff; text-decoration:none;'>{h['title']}</a></h4><p style='color:#a0a0a0; font-size:12px;'>📰 Kaynak: {h['media']} | 📅 Tarih: {h['date']}</p></div>", unsafe_allow_html=True)
                            
                            etki_analiz_sonucu = ai_etki_analizi(h['title'], secilen_varlik)
                            try:
                                etki_yonu, etki_yuzde, guven_skoru, ozet = etki_analiz_sonucu.split("|")
                                renk = "#00ff88" if "POZİTİF" in etki_yonu else "#ff4d4d" if "NEGATİF" in etki_yonu else "#a0a0a0"
                                st.markdown(f"**Yön:** <span style='color:{renk};'>{etki_yonu}</span> | **Etki:** %{etki_yuzde.strip()} | **AI Güven Skoru:** {guven_skoru.strip()}/100<br>📝 *Özet:* {ozet.strip()}", unsafe_allow_html=True)
                            except:
                                st.markdown(f"🤖 **Analiz Sonucu:** {etki_analiz_sonucu}")
                            st.divider()
                else:
                    st.info("Kritik haber akışı bulunamadı.")

            with tabs[3]:
                st.markdown("### 📊 Tarihsel Verim & Enflasyon Karşılaştırması")
                df_tablo = hesapla_gecmis_performans(data, curr, ana_para, kur_val, s)
                st.table(df_tablo)
                st.caption("Not: Reel Getiri hesaplanırken ortalama küresel enflasyon etkisi varsayılmıştır.")
                
    except Exception as e:
        st.error(f"Sistem Hatası: Veri çekilirken veya işlenirken bir sorun oluştu. Detay: {e}")
        st.info("Lütfen internet bağlantınızı ve girdiğiniz parametreleri kontrol edin.")

# --- ALT SABİT AKSİYON MENÜSÜ ---
st.markdown("""
<div class="floating-action-bar">
    <button style="background:transparent; border:none; color:white; font-size:16px;">🔄 Yenile</button>
    <button style="background:transparent; border:none; color:white; font-size:16px;">⭐ İzleme Listesi</button>
    <button style="background:transparent; border:none; color:white; font-size:16px;">📤 Rapor İndir</button>
    <button style="background:transparent; border:none; color:#00bbff; font-weight:bold; font-size:16px;">🤖 AI Analiz Raporu</button>
</div>
""", unsafe_allow_html=True)