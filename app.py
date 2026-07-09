import os
import time

os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import streamlit as st
from components.header import render_market_ticker
from components.sidebar import render_sidebar_header
from config.constants import CURRENCY_SYMBOLS
from config.markets import FORECAST_PERIODS, INSTRUMENTS
from core.startup import initialize_application
from components.footer import render_action_footer
from components.metrics import render_risk_metrics
from components.news_panel import render_news_panel
from components.performance_panel import render_performance_panel
from components.tabs import create_main_tabs
from charts.candlestick import create_price_volume_chart
from charts.consensus import create_consensus_chart
from charts.rsi import analyze_rsi
from services.cache_service import (
    get_cached_asset_history,
    get_cached_currencies,
    get_cached_news,
)
from finans_motoru import (
    gelecek_senaryolari_hesapla,
)
from haber_motoru import (
    ai_teknik_analiz_yorumu,
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
                
                # RSI Uyarısı
                rsi_result = analyze_rsi(data["Close"])

                if rsi_result.status == "overbought":
                    st.warning(f"⚠️ {rsi_result.message}")
                elif rsi_result.status == "oversold":
                    st.success(f"✅ {rsi_result.message}")
                else:
                    st.info(f"ℹ️ {rsi_result.message}")

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

                fig_gelecek = create_consensus_chart(
                    forecast_data=gelecek,
                    last_date=data.index[-1],
                )

                st.plotly_chart(
                    fig_gelecek,
                    use_container_width=True,
                    config={
                        "scrollZoom": True,
                        "displaylogo": False,
                        "responsive": True,
                    },
                )

                st.markdown("#### Detaylı Gelecek Değerlemeleri")
                st.table(gelecek["gelecek_df"])

            with tabs[2]:
                render_news_panel(
                    news_items=haberler,
                    asset_name=secilen_varlik,
                )

            with tabs[3]:
                render_performance_panel(
                    data=data,
                    current_price=curr,
                    investment_amount=ana_para,
                    currency_rate=kur_val,
                    currency_symbol=s,
                )

    except Exception as e:
        st.error(f"Sistem Hatası: Veri çekilirken veya işlenirken bir sorun oluştu. Detay: {e}")
        st.info("Lütfen internet bağlantınızı ve girdiğiniz parametreleri kontrol edin.")

render_action_footer()
