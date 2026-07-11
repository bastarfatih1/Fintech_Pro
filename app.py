import os

os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import streamlit as st
from components.ui_theme import inject_global_premium_theme
from components.header import render_app_intro, render_market_ticker
from components.input_panel import render_input_panel
from components.sidebar import render_sidebar_header
from core.startup import initialize_application
from core.session import initialize_analysis_state, render_analysis_button
from core.market_calendar import normalize_asset_type
from components.footer import render_action_footer
from components.analysis_panel import render_analysis_panel
from components.landing_panel import render_landing_panel
from components.consensus_panel import render_consensus_panel
from components.news_panel import render_news_panel
from components.performance_panel import render_performance_panel
from components.progress import AnalysisProgress, render_analysis_error
from components.tabs import create_main_tabs
from services.cache_service import (
    get_cached_asset_history_with_metadata,
    get_cached_currencies_with_metadata,
    get_cached_news,
)
from finans_motoru import (
    gelecek_senaryolari_hesapla,
)
from haber_motoru import ai_haberleri_toplu_analiz_et, render_premium_ai_loading


def render_data_source_notice(metadata) -> None:
    """Piyasa verisinin kaynak bilgisini sade bir şekilde gösterir."""
    if metadata is None:
        return

    source_name = getattr(metadata, "source_name", "Bilinmiyor")
    provider_type = getattr(metadata, "provider_type", "Bilinmiyor")
    license_status = getattr(metadata, "license_status", "Bilinmiyor")
    is_production_allowed = bool(
        getattr(metadata, "is_production_allowed", False)
    )
    fallback_used = bool(getattr(metadata, "fallback_used", False))
    data_delay = getattr(metadata, "data_delay", "Bilinmiyor")
    note = getattr(metadata, "note", "")

    provider_label = str(provider_type).title()

    if fallback_used:
        st.warning(
            f"Veri kaynağı: {source_name} | Fallback kullanıldı."
        )
    else:
        st.caption(
            f"Veri: {source_name} · {provider_label}"
        )

    with st.expander("Veri kaynağı detayı", expanded=False):
        st.write(f"**Kaynak:** {source_name}")
        st.write(f"**Durum:** {provider_label}")
        st.write(
            "**Üretime uygun:** "
            f"{'Evet' if is_production_allowed else 'Hayır'}"
        )
        st.write(f"**Lisans:** {license_status}")
        st.write(f"**Gecikme:** {data_delay}")
        if note:
            st.caption(note)



def render_currency_source_notice(metadata) -> None:
    """Döviz kuru kaynağını sade bir şekilde gösterir."""
    if metadata is None:
        return

    source_name = getattr(metadata, "source_name", "Bilinmiyor")
    provider_type = getattr(metadata, "provider_type", "Bilinmiyor")
    license_status = getattr(metadata, "license_status", "Bilinmiyor")
    is_production_allowed = bool(
        getattr(metadata, "is_production_allowed", False)
    )
    fallback_used = bool(getattr(metadata, "fallback_used", False))
    data_delay = getattr(metadata, "data_delay", "Bilinmiyor")
    note = getattr(metadata, "note", "")

    provider_label = str(provider_type).title()

    if fallback_used:
        st.warning(
            f"Kur kaynağı: {source_name} | Fallback kur tablosu kullanıldı."
        )
    else:
        st.caption(
            f"Kur: {source_name} · {provider_label}"
        )

    with st.expander("Kur kaynağı detayı", expanded=False):
        st.write(f"**Kaynak:** {source_name}")
        st.write(f"**Durum:** {provider_label}")
        st.write(f"**Fallback:** {'Evet' if fallback_used else 'Hayır'}")
        st.write(
            "**Üretime uygun:** "
            f"{'Evet' if is_production_allowed else 'Hayır'}"
        )
        st.write(f"**Lisans:** {license_status}")
        st.write(f"**Güncellik:** {data_delay}")
        if note:
            st.caption(note)



def render_ai_result_card(ai_bundle) -> None:
    """AI sonucunu sekmelerden önce görünür bir premium kart olarak gösterir."""
    if not isinstance(ai_bundle, dict):
        st.warning("AI yorumu henüz oluşturulamadı.")
        return

    provider = str(ai_bundle.get("provider", "AI")).upper()
    technical_summary = str(ai_bundle.get("technical_summary", "")).strip()
    market_synthesis = str(ai_bundle.get("market_synthesis", "")).strip()
    risk_note = str(ai_bundle.get("risk_note", "")).strip()
    news_effect = str(ai_bundle.get("overall_news_effect", "NÖTR")).strip()

    if not technical_summary and not market_synthesis and not risk_note:
        st.warning("AI çıktı verdi ancak gösterilecek yorum alanı boş geldi.")
        return

    tone_class = "ai-up" if "POZ" in news_effect.upper() else "ai-down" if "NEG" in news_effect.upper() else "ai-neutral"

    st.markdown(
        """
        <style>
        .fp-ai-result-card {
            border: 1px solid rgba(56, 189, 248, 0.42);
            border-radius: 22px;
            padding: 18px 20px;
            margin: 12px 0 18px 0;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.22), transparent 34%),
                radial-gradient(circle at bottom right, rgba(134, 239, 172, 0.12), transparent 30%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.94));
            box-shadow: 0 18px 44px rgba(2, 6, 23, 0.30);
        }
        .fp-ai-result-kicker {
            color: #93c5fd;
            font-size: 0.78rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            font-weight: 900;
            margin-bottom: 7px;
        }
        .fp-ai-result-title {
            color: #f8fafc;
            font-size: 1.28rem;
            font-weight: 950;
            margin-bottom: 8px;
        }
        .fp-ai-result-text {
            color: #dbeafe;
            font-size: 1.00rem;
            line-height: 1.65;
            font-weight: 560;
        }
        .fp-ai-result-note {
            color: #cbd5e1;
            font-size: 0.90rem;
            margin-top: 8px;
            line-height: 1.52;
        }
        .ai-up { color: #86efac; font-weight: 950; }
        .ai-down { color: #fca5a5; font-weight: 950; }
        .ai-neutral { color: #fde68a; font-weight: 950; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="fp-ai-result-card">
            <div class="fp-ai-result-kicker">AI Analysis Visible Layer · {provider}</div>
            <div class="fp-ai-result-title">
                AI yorumları hazır · <span class="{tone_class}">{news_effect}</span>
            </div>
            <div class="fp-ai-result-text">{technical_summary or market_synthesis}</div>
            <div class="fp-ai-result-note">{market_synthesis}</div>
            <div class="fp-ai-result-note">{risk_note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_tabs(
    data,
    news_items,
    inputs,
    current_price,
    forecast_data,
    ai_bundle=None,
) -> None:
    """Analiz sonuçlarını dört ana sekmede gösterir."""
    tabs = create_main_tabs()

    with tabs[0]:
        render_landing_panel(
            data=data,
            asset_name=inputs.asset_name,
            current_price=current_price,
            investment_amount=inputs.investment_amount,
            currency_rate=inputs.currency_rate,
            currency_symbol=inputs.currency_symbol,
            forecast_data=forecast_data,
        )

    with tabs[1]:
        render_analysis_panel(
            data=data,
            asset_name=inputs.asset_name,
            current_price=current_price,
            currency_rate=inputs.currency_rate,
            forecast_data=forecast_data,
            ai_bundle=ai_bundle,
        )

        st.markdown("---")

        render_consensus_panel(
            forecast_data=forecast_data,
            last_date=data.index[-1],
        )

    with tabs[2]:
        render_news_panel(
            news_items=news_items,
            asset_name=inputs.asset_name,
            ai_bundle=ai_bundle,
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
        market_result = get_cached_asset_history_with_metadata(
            inputs.market_symbol
        )
        data = market_result.get("data")
        market_metadata = market_result.get("metadata")
        progress.update(30, "Finansal geçmiş yüklendi.")

        if data is None or data.empty:
            progress.close()
            if getattr(inputs, "market_symbol", "") == "GRAM_ALTIN_TRY":
                st.warning(
                    "Gram Altın için geçerli veri üretilemedi. "
                    "Ons altın veya USD/TRY geçmiş verisi alınamadı. "
                    "İnternet bağlantısını ve yfinance veri erişimini kontrol et."
                )
            else:
                st.warning(
                    "Seçilen varlık için geçerli piyasa verisi bulunamadı."
                )
            return

        current_price = float(data["Close"].iloc[-1])

        asset_type = normalize_asset_type(
            asset_type=getattr(inputs, "asset_type", None),
            market_symbol=inputs.market_symbol,
        )

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
            asset_type=asset_type,
            market_symbol=inputs.market_symbol,
        )

        progress.update(72, "Tek prompt AI sentezi hazırlanıyor...")

        ai_loading_placeholder = st.empty()
        with ai_loading_placeholder:
            render_premium_ai_loading()

        try:
            ai_bundle = ai_haberleri_toplu_analiz_et(
                varlik=inputs.asset_name,
                haberler=news_items,
                anlik=current_price,
                boga=float(forecast_data["boga"]),
                ayi=float(forecast_data["ayi"]),
            )
        finally:
            ai_loading_placeholder.empty()

        progress.update(80, "Risk metrikleri hesaplanıyor...")
        progress.complete()

        render_ai_result_card(ai_bundle)

        render_data_source_notice(market_metadata)

        render_analysis_tabs(
            data=data,
            news_items=news_items,
            inputs=inputs,
            current_price=current_price,
            forecast_data=forecast_data,
            ai_bundle=ai_bundle,
        )

    except Exception as exc:
        progress.close()
        render_analysis_error(exc)


def main() -> None:
    """Streamlit uygulamasının ana çalışma akışı."""
    initialize_application()
    inject_global_premium_theme()
    render_sidebar_header()

    render_app_intro()

    currency_result = get_cached_currencies_with_metadata()
    currencies = currency_result.get("rates", {})
    currency_metadata = currency_result.get("metadata")

    render_market_ticker(currencies)

    inputs = render_input_panel(currencies)
    render_currency_source_notice(currency_metadata)

    st.divider()

    initialize_analysis_state()
    render_analysis_button()

    if st.session_state.analiz_tamam:
        run_analysis(inputs)

    render_action_footer()


if __name__ == "__main__":
    main()
