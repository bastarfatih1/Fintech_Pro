import os

os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import streamlit as st
from components.header import render_market_ticker
from components.input_panel import render_input_panel
from components.sidebar import render_sidebar_header
from core.startup import initialize_application
from core.session import initialize_analysis_state, render_analysis_button
from components.footer import render_action_footer
from components.analysis_panel import render_analysis_panel
from components.consensus_panel import render_consensus_panel
from components.news_panel import render_news_panel
from components.performance_panel import render_performance_panel
from components.progress import AnalysisProgress, render_analysis_error
from components.tabs import create_main_tabs
from services.cache_service import (
    get_cached_asset_history,
    get_cached_currencies,
    get_cached_news,
)
from finans_motoru import (
    gelecek_senaryolari_hesapla,
)

initialize_application()
render_market_ticker()
render_sidebar_header()



kurlar = get_cached_currencies()

inputs = render_input_panel(kurlar)

ana_para = inputs.investment_amount
secilen_kur = inputs.currency_code
secilen_varlik = inputs.asset_name
hedef_gun = inputs.forecast_days
s = inputs.currency_symbol
kur_val = inputs.currency_rate
sembol = inputs.market_symbol

st.divider()


initialize_analysis_state()
render_analysis_button()

if st.session_state.analiz_tamam:
    progress = AnalysisProgress()

    try:
        data = get_cached_asset_history(sembol)
        progress.update(30, "Finansal geçmiş yüklendi.")

        if data is None or data.empty:
            progress.close()
            st.warning(
                "Seçilen varlık için geçerli piyasa verisi bulunamadı."
            )
        else:
            curr = float(data["Close"].iloc[-1])
            haberler = get_cached_news(
                secilen_varlik.split("(")[0]
            )
            progress.update(
                50,
                "Monte Carlo simülasyonları ve ML rota optimizasyonu tamamlanıyor...",
            )

            gelecek = gelecek_senaryolari_hesapla(
                data=data,
                curr=curr,
                ana_para=ana_para,
                periyot_gun=hedef_gun,
                kur_val=kur_val,
            )
            progress.update(80, "Risk metrikleri hesaplanıyor...")

            tabs = create_main_tabs()
            progress.complete()

            with tabs[0]:
                render_analysis_panel(
                    data=data,
                    asset_name=secilen_varlik,
                    current_price=curr,
                    currency_rate=kur_val,
                    forecast_data=gelecek,
                )

            with tabs[1]:
                render_consensus_panel(
                    forecast_data=gelecek,
                    last_date=data.index[-1],
                )

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

    except Exception as exc:
        progress.close()
        render_analysis_error(exc)

render_action_footer()
