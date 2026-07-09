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

def render_analysis_tabs(
    data,
    news_items,
    inputs,
    current_price,
    forecast_data,
) -> None:
    """Analiz sonuçlarını dört ana sekmede gösterir."""
    tabs = create_main_tabs()

    with tabs[0]:
        render_analysis_panel(
            data=data,
            asset_name=inputs.asset_name,
            current_price=current_price,
            currency_rate=inputs.currency_rate,
            forecast_data=forecast_data,
        )

    with tabs[1]:
        render_consensus_panel(
            forecast_data=forecast_data,
            last_date=data.index[-1],
        )

    with tabs[2]:
        render_news_panel(
            news_items=news_items,
            asset_name=inputs.asset_name,
        )

    with tabs[3]:
        render_performance_panel(
            data=data,
            current_price=current_price,
            investment_amount=inputs.investment_amount,
            currency_rate=inputs.currency_rate,
            currency_symbol=inputs.currency_symbol,
        )


def run_analysis(inputs) -> None:
    """Seçilen varlık için veri, tahmin ve panel akışını çalıştırır."""
    progress = AnalysisProgress()

    try:
        data = get_cached_asset_history(inputs.market_symbol)
        progress.update(30, "Finansal geçmiş yüklendi.")

        if data is None or data.empty:
            progress.close()
            st.warning(
                "Seçilen varlık için geçerli piyasa verisi bulunamadı."
            )
            return

        current_price = float(data["Close"].iloc[-1])

        news_items = get_cached_news(
            inputs.asset_name.split("(")[0]
        )

        progress.update(
            50,
            "Monte Carlo simülasyonları ve ML rota optimizasyonu tamamlanıyor...",
        )

        forecast_data = gelecek_senaryolari_hesapla(
            data=data,
            curr=current_price,
            ana_para=inputs.investment_amount,
            periyot_gun=inputs.forecast_days,
            kur_val=inputs.currency_rate,
        )

        progress.update(80, "Risk metrikleri hesaplanıyor...")
        progress.complete()

        render_analysis_tabs(
            data=data,
            news_items=news_items,
            inputs=inputs,
            current_price=current_price,
            forecast_data=forecast_data,
        )

    except Exception as exc:
        progress.close()
        render_analysis_error(exc)


def main() -> None:
    """Streamlit uygulamasının ana çalışma akışı."""
    initialize_application()
    render_market_ticker()
    render_sidebar_header()

    currencies = get_cached_currencies()
    inputs = render_input_panel(currencies)

    st.divider()

    initialize_analysis_state()
    render_analysis_button()

    if st.session_state.analiz_tamam:
        run_analysis(inputs)

    render_action_footer()


if __name__ == "__main__":
    main()
