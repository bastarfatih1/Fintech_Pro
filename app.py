import os
import time

os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.header import render_market_ticker
from components.sidebar import render_sidebar_header
from config.constants import CURRENCY_SYMBOLS
from config.markets import FORECAST_PERIODS, INSTRUMENTS
from core.startup import initialize_application
from components.footer import render_action_footer
from components.metrics import render_risk_metrics
from components.tabs import create_main_tabs
from charts.candlestick import create_price_volume_chart
from services.cache_service import (
    get_cached_asset_history,
    get_cached_currencies,
    get_cached_news,
)
from finans_motoru import (
    gelecek_senaryolari_hesapla,
    hesapla_gecmis_performans,
)
from haber_motoru import (
    ai_etki_analizi,
    ai_teknik_analiz_yorumu,
    ai_toplu_model_yorumlari,
    
)

initialize_application()
render_market_ticker()
render_sidebar_header()



kurlar = get_cached_currencies()

# Ana Parametreler
col_g1, col_g2, col_g3, col_g4 = st.columns([2, 1, 1, 1])
ana_para = col_g1.number_input("Stratejik Yatırım Tutarı:", value=0.0, step=10000.0)
secilen_kur = col_g2.selectbox("Baz Para Birimi:", ["TRY", "USD", "EUR", "CNY", "RUB", "JPY", "SAR", "KWD"])

  
secilen_varlik = col_g3.selectbox(
    "Analiz Edilecek Varlık:",
    list(INSTRUMENTS.keys()),
)

secilen_vade = col_g4.selectbox(
    "Projeksiyon Vadesi:",
    list(FORECAST_PERIODS.keys()),
    index=3,
)
hedef_gun = FORECAST_PERIODS[secilen_vade]

s = CURRENCY_SYMBOLS[secilen_kur]
kur_val = kurlar.get(secilen_kur, 1.0)

st.divider()


if "analiz_tamam" not in st.session_state:
    st.session_state.analiz_tamam = False

sembol = INSTRUMENTS[secilen_varlik]

if st.button("🚀 Kurumsal Gelişmiş AI Projeksiyonunu Başlat", use_container_width=True, type="primary"):
    st.session_state.analiz_tamam = True

if st.session_state.analiz_tamam:
    progress_text = "Veriler işleniyor, kantitatif modeller çalıştırılıyor..."
    my_bar = st.progress(0, text=progress_text)
    
    try:
        data = get_cached_asset_history(sembol)
        my_bar.progress(30, text="Finansal geçmiş yüklendi.")
        
        if data is not None and not data.empty:
            curr = float(data['Close'].iloc[-1])
            haberler = get_cached_news(
                secilen_varlik.split("(")[0]
            )
            my_bar.progress(50, text="Monte Carlo simülasyonları ve ML rota optimizasyonu tamamlanıyor...")
            
            gelecek = gelecek_senaryolari_hesapla(
                data=data, curr=curr, ana_para=ana_para, periyot_gun=hedef_gun, kur_val=kur_val
            )
            my_bar.progress(80, text="Risk metrikleri hesaplanıyor...")
            
            # Üst Menü (Tabs)
            tabs = create_main_tabs()
            my_bar.progress(100, text="Tamamlandı.")
            time.sleep(0.5)
            my_bar.empty()
            
            with tabs[0]:
                st.markdown(f"### 📡 {secilen_varlik} - Merkezi Terminal")
                
                stats = gelecek["stats"]
                render_risk_metrics(stats)
                
                st.markdown("---") 
                
                # TRADINGVIEW SEVİYESİ GRAFİK
                grafik_veri = data.tail(250).copy() 
               
                
                # RSI Uyarısı
                rsi_son = grafik_veri['Close'].diff().apply(lambda x: x if x > 0 else 0).rolling(14).mean() / (abs(grafik_veri['Close'].diff().apply(lambda x: x if x < 0 else 0)).rolling(14).mean() + 1e-9)
                rsi_val = 100 - (100 / (1 + rsi_son.iloc[-1]))
                if rsi_val > 70:
                    st.warning(f"⚠️ Teknik Uyarı: RSI seviyesi ({rsi_val:.1f}) varlığın aşırı alındığına işaret ediyor.")
                elif rsi_val < 30:
                    st.success(f"✅ Teknik Uyarı: RSI seviyesi ({rsi_val:.1f}) varlığın aşırı satıldığını (dip) gösteriyor.")

                fig_ana = create_price_volume_chart(
                    data=data,
                    currency_rate=kur_val,
                    current_price=curr,
                    bear_target=gelecek["ayi"],
                    bull_target=gelecek["boga"],
                )

                st.plotly_chart(
                    fig_ana,
                    use_container_width=True,
                    config={
                        "scrollZoom": True,
                        "displaylogo": False,
                        "responsive": True,
                    },
                )
                
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

render_action_footer()
