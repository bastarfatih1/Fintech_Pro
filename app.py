
def _inject_compact_analysis_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            padding: 0.35rem 0.45rem !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.72rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.15rem !important;
            line-height: 1.15 !important;
        }

        [data-testid="stCaptionContainer"] {
            font-size: 0.78rem !important;
            line-height: 1.35 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding-top: 0.65rem !important;
            padding-bottom: 0.65rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


import time
import os



os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import streamlit as st
from services.runtime_monitor import mark_app_rerun, mark_analysis_start, mark_analysis_end

mark_app_rerun()
import pandas as pd
from components.ui_theme import inject_global_premium_theme
from components.header import render_app_intro, render_market_ticker
from components.input_panel import render_input_panel
from core.startup import initialize_application
from core.session import initialize_analysis_state, render_analysis_button
from core.market_calendar import normalize_asset_type
from components.footer import render_action_footer
from components.runtime_diagnostics_panel import render_runtime_diagnostics_panel
from components.safe_panel import safe_render_panel
from components.analysis_panel import render_analysis_panel
from components.landing_panel import render_landing_panel
from components.first_overview_panel import render_first_overview_panel
from components.strategic_ai_panel import render_strategic_ai_panel
from components.developer_diagnostics_panel import render_developer_diagnostics_panel
from components.eviews_regression_panel import render_eviews_regression_panel
from components.horizon_validation_panel import render_horizon_validation_panel
from components.backtest_decision_panel import render_backtest_decision_panel
from components.premium_ui import render_plain_guide, render_premium_table
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
from haber_motoru import ai_haberleri_toplu_analiz_et


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





def _clean_analysis_market_data(data):
    """
    App seviyesinde analiz verisini temizler.
    Son satır NaN olsa bile son geçerli pozitif Close kalır.
    """
    import numpy as np
    import pandas as pd

    if data is None or not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError("Seçilen varlık için piyasa verisi bulunamadı.")

    fixed = data.copy()

    if "Close" not in fixed.columns:
        raise ValueError("Seçilen varlık için Close fiyat sütunu bulunamadı.")

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in fixed.columns:
            fixed[col] = pd.to_numeric(fixed[col], errors="coerce")
            fixed[col] = fixed[col].replace([np.inf, -np.inf], np.nan)

    fixed = fixed.dropna(subset=["Close"])
    fixed = fixed[fixed["Close"] > 0]

    if fixed.empty:
        raise ValueError("Seçilen varlık için geçerli pozitif kapanış fiyatı bulunamadı.")

    for col in ["Open", "High", "Low"]:
        if col not in fixed.columns:
            fixed[col] = fixed["Close"]
        else:
            fixed[col] = fixed[col].fillna(fixed["Close"])
            fixed.loc[fixed[col] <= 0, col] = fixed["Close"]

    if "Volume" not in fixed.columns:
        fixed["Volume"] = 0.0
    else:
        fixed["Volume"] = fixed["Volume"].fillna(0.0)

    fixed = fixed[~fixed.index.duplicated(keep="last")]
    fixed = fixed.sort_index()

    return fixed


def _get_last_valid_close(data) -> float:
    """
    Güncel fiyat için ham son satırı değil,
    son geçerli pozitif Close değerini döndürür.
    """
    import numpy as np
    import pandas as pd

    close = pd.to_numeric(data["Close"], errors="coerce")
    close = close.replace([np.inf, -np.inf], np.nan)
    close = close.dropna()
    close = close[close > 0]

    if close.empty:
        raise ValueError("Güncel fiyat için geçerli Close değeri bulunamadı.")

    return float(close.iloc[-1])

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





def _ai_num(value, default=None):
    try:
        if value is None:
            return default
        n = float(value)
        if pd.isna(n):
            return default
        return n
    except Exception:
        return default


def _ai_money(value, symbol="₺"):
    n = _ai_num(value)

    if n is None:
        return "veri yok"

    s = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} {symbol}"


def _ai_pct(value):
    n = _ai_num(value)

    if n is None:
        return "veri yok"

    sign = "+" if n > 0 else "-" if n < 0 else ""
    return f"{sign}%{abs(n):.2f}".replace(".", ",")


def _clean_ai_text(value) -> str:
    text = str(value or "").strip()

    replacements = {
        "POZİTİF": "olumlu eğilim",
        "NEGATİF": "risk baskısı",
        "NÖTR": "dengeli görünüm",
        "AL": "yukarı yönlü sinyal",
        "SAT": "aşağı yönlü risk",
        "OLLAMA": "",
        "OPENAI": "",
        "GPT": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split()).strip()


def _professional_effect_label(effect: str, base_return=None) -> str:
    ret = _ai_num(base_return)

    if ret is not None:
        if ret > 3:
            return "olumlu eğilim"
        if ret < -3:
            return "risk baskısı"

    effect_upper = str(effect or "").upper()

    if "POZ" in effect_upper:
        return "olumlu eğilim"
    if "NEG" in effect_upper:
        return "risk baskısı"

    return "dengeli görünüm"


def _ai_future_table(forecast_data):
    if not isinstance(forecast_data, dict):
        return pd.DataFrame()

    for key in ["gelecek_df", "future_table", "forecast_table", "senaryo_tablosu"]:
        candidate = forecast_data.get(key)

        if isinstance(candidate, pd.DataFrame) and not candidate.empty:
            return candidate.copy()

    for value in forecast_data.values():
        if isinstance(value, pd.DataFrame) and not value.empty and "Vade" in value.columns:
            return value.copy()

    return pd.DataFrame()



def _ai_pick_row(forecast_data, selected_label=None):
    df = _ai_future_table(forecast_data)

    if df.empty:
        return {}

    if selected_label and "Vade" in df.columns:
        label = str(selected_label).strip().casefold()

        match = df[
            df["Vade"]
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq(label)
        ]

        if not match.empty:
            return match.iloc[0].to_dict()

    return df.iloc[-1].to_dict()

def _ai_model_summary(forecast_data) -> str:
    if not isinstance(forecast_data, dict):
        return "Model verisi sınırlı olduğu için sonuçlar temkinli okunmalıdır."

    weights = forecast_data.get("model_agirliklari", {})
    active_models = 0

    if isinstance(weights, dict):
        active_models = len([
            v for v in weights.values()
            if (_ai_num(v, 0.0) or 0.0) > 0
        ])

    backtest_df = forecast_data.get("backtest_df")
    passed = None
    total = None

    if isinstance(backtest_df, pd.DataFrame) and not backtest_df.empty:
        total = len(backtest_df)

        if "Başarılı mı?" in backtest_df.columns:
            passed = int(backtest_df["Başarılı mı?"].astype(bool).sum())
        elif "Durum" in backtest_df.columns:
            passed = int(
                backtest_df["Durum"]
                .astype(str)
                .str.contains("başar|success|geçti", case=False, regex=True)
                .sum()
            )

    parts = []

    if active_models:
        parts.append(f"Konsensüse {active_models} aktif model katkı veriyor.")

    if passed is not None and total:
        parts.append(f"Test ve backtest tarafında {passed}/{total} kontrol olumlu görünüyor.")

    if not parts:
        parts.append("Model konsensüsü senaryo üretmiş olsa da doğrulama detayları sınırlı okunmalıdır.")

    parts.append("Bu nedenle sonuçlar kesin fiyat tahmini değil, olasılık temelli karar destek senaryosu olarak değerlendirilmelidir.")

    return " ".join(parts)


def _ai_direction_reasons(base_return, news_text, model_text):
    ret = _ai_num(base_return, 0.0) or 0.0

    up = []
    down = []

    if ret > 0:
        up.append("baz senaryonun seçili vadede pozitif getiri üretmesi")
    elif ret < 0:
        down.append("baz senaryonun seçili vadede negatif getiri üretmesi")
    else:
        down.append("baz senaryonun belirgin bir yukarı yön üretmemesi")

    news_lower = news_text.casefold()
    model_lower = model_text.casefold()

    if "olumlu" in news_lower or "destek" in news_lower:
        up.append("haber akışının fiyatı destekleyebilecek tonda olması")
    elif "risk" in news_lower or "baskı" in news_lower or "negatif" in news_lower:
        down.append("haber akışında baskı veya belirsizlik işaretleri bulunması")
    else:
        up.append("haber akışında sert negatif baskının öne çıkmaması")

    if "aktif model" in model_lower or "backtest" in model_lower or "test" in model_lower:
        up.append("model konsensüsünün ölçülebilir ve test edilebilir senaryo üretmesi")
    else:
        down.append("model doğrulama bilgisinin sınırlı olması")

    down.append("oynaklık, dış haber akışı veya piyasa likiditesindeki bozulma")
    down.append("kötümser senaryonun baz beklentiden belirgin ayrışması")

    return up[:4], down[:4]


def render_ai_result_card(
    ai_bundle,
    *,
    inputs=None,
    forecast_data=None,
    current_price=None,
    investment_amount=None,
    currency_symbol="₺",
) -> None:
    """AI yorumunu tek blokta, profesyonel düz metin olarak gösterir."""
    if not isinstance(ai_bundle, dict):
        ai_bundle = {}

    forecast_data = forecast_data or {}

    selected_horizon = getattr(inputs, "forecast_label", None) or "seçili vade"
    asset_name = getattr(inputs, "asset_name", "seçili varlık")
    invested = _ai_num(investment_amount, None)

    row = _ai_pick_row(forecast_data, selected_horizon)

    base_return = _ai_num(row.get("Nominal Getiri %"))
    bad_return = _ai_num(row.get("Kötümser Getiri %"))
    good_return = _ai_num(row.get("İyimser Getiri %"))

    base_capital = _ai_num(row.get("Sermaye Karşılığı"))
    bad_capital = _ai_num(row.get("Kötümser Sermaye"))
    good_capital = _ai_num(row.get("İyimser Sermaye"))

    base_price = _ai_num(row.get("Baz Senaryo", row.get("Tahmin")))
    bad_price = _ai_num(row.get("Kötümser Senaryo"))
    good_price = _ai_num(row.get("İyimser Senaryo"))

    if invested is not None:
        if base_capital is None and base_return is not None:
            base_capital = invested * (1 + base_return / 100.0)
        if bad_capital is None and bad_return is not None:
            bad_capital = invested * (1 + bad_return / 100.0)
        if good_capital is None and good_return is not None:
            good_capital = invested * (1 + good_return / 100.0)

    base_gain = base_capital - invested if base_capital is not None and invested is not None else None
    bad_gain = bad_capital - invested if bad_capital is not None and invested is not None else None
    good_gain = good_capital - invested if good_capital is not None and invested is not None else None

    technical_summary = _clean_ai_text(ai_bundle.get("technical_summary", ""))
    market_synthesis = _clean_ai_text(ai_bundle.get("market_synthesis", ""))
    risk_note = _clean_ai_text(ai_bundle.get("risk_note", ""))
    news_effect = str(ai_bundle.get("overall_news_effect", "NÖTR")).strip()

    news_text = (
        market_synthesis
        or technical_summary
        or "Haber akışı sınırlı olduğu için yorum ağırlıklı olarak model senaryosu, geçmiş fiyat davranışı ve teknik görünüm üzerinden yapılmıştır."
    )

    model_text = _ai_model_summary(forecast_data)
    effect_label = _professional_effect_label(news_effect, base_return)

    up_reasons, down_reasons = _ai_direction_reasons(
        base_return=base_return,
        news_text=news_text,
        model_text=model_text,
    )

    if base_return is not None and base_return > 0:
        direction_sentence = (
            f"Modelin baz senaryosu {selected_horizon} vadede yukarı yönlü bir beklenti üretmektedir."
        )
    elif base_return is not None and base_return < 0:
        direction_sentence = (
            f"Modelin baz senaryosu {selected_horizon} vadede aşağı yönlü risk üretmektedir."
        )
    else:
        direction_sentence = (
            f"Modelin baz senaryosu {selected_horizon} vadede belirgin bir yön avantajı göstermemektedir."
        )

    up_text = "; ".join(up_reasons)
    down_text = "; ".join(down_reasons)

    with st.container(border=True):
        st.markdown("### Yapay Zekâ Stratejik Yorum")

        st.write(
            f"{asset_name} için genel görünüm **{effect_label}** olarak okunmaktadır. "
            f"{direction_sentence} Seçilen yatırım tutarı **{_ai_money(invested, currency_symbol)}** "
            f"olduğunda, baz senaryoda sermayenin yaklaşık **{_ai_money(base_capital, currency_symbol)}** "
            f"seviyesine ulaşması beklenir. Bu sonuç yaklaşık **{_ai_money(base_gain, currency_symbol)}** "
            f"nominal fark ve **{_ai_pct(base_return)}** getiri anlamına gelir."
        )

        st.write(
            f"Kötümser senaryoda aynı yatırım tutarı yaklaşık **{_ai_money(bad_capital, currency_symbol)}** "
            f"seviyesine gerileyebilir; bu durumda yaklaşık **{_ai_money(bad_gain, currency_symbol)}** "
            f"sonuç ve **{_ai_pct(bad_return)}** performans oluşur. İyimser senaryoda ise sermaye "
            f"yaklaşık **{_ai_money(good_capital, currency_symbol)}** seviyesine çıkabilir; bu durumda "
            f"yaklaşık **{_ai_money(good_gain, currency_symbol)}** sonuç ve **{_ai_pct(good_return)}** "
            f"performans oluşur."
        )

        st.write(
            f"Fiyat hedefleri tarafında kötümser hedef **{_ai_money(bad_price, currency_symbol)}**, "
            f"baz hedef **{_ai_money(base_price, currency_symbol)}**, iyimser hedef ise "
            f"**{_ai_money(good_price, currency_symbol)}** olarak okunmaktadır. "
            f"Bu aralığın genişliği, senaryolar arasındaki belirsizliğin de dikkate alınması gerektiğini gösterir."
        )

        st.markdown("#### Haber, model ve test yorumu")

        st.write(
            f"Haber akışı genel olarak şöyle okunmaktadır: {news_text} "
            f"Model tarafında ise {model_text}"
        )

        st.markdown("#### Neden artabilir / neden azalabilir?")

        st.write(
            f"Fiyatın artmasını destekleyebilecek ana nedenler: {up_text}. "
            f"Fiyatın azalmasına veya baz senaryodan sapmasına neden olabilecek başlıca riskler: {down_text}."
        )

        st.markdown("#### Sonuç")

        if risk_note:
            st.write(
                f"Risk notu: {risk_note} "
                "Bu nedenle çıktı tek başına alım-satım kararı olarak değil, haber, model, test ve senaryo verilerini birleştiren karar destek yorumu olarak değerlendirilmelidir."
            )
        else:
            st.write(
                "Sonuç olarak bu analiz, seçilen vade ve yatırım tutarı için olasılık temelli bir senaryo üretir. "
                "Geçmiş performans geleceği garanti etmez; model çıktıları tek başına alım-satım kararı için kullanılmamalıdır."
            )

def _fp_find_best_future_raw_df(forecast_data):
    import pandas as pd

    if not isinstance(forecast_data, dict):
        return pd.DataFrame()

    candidates = []

    # Öncelikli bilinen isimler.
    for key in [
        "gelecek_tablo",
        "gelecek_senaryolari",
        "future_table",
        "future_scenarios",
        "senaryo_tablo",
        "projection_table",
        "forecast_table",
    ]:
        if key in forecast_data:
            candidates.append((key, forecast_data.get(key)))

    # Forecast_data içindeki tüm tablo benzeri değerleri de tara.
    for key, value in forecast_data.items():
        if isinstance(value, (list, tuple, pd.DataFrame)):
            candidates.append((str(key), value))

        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, (list, tuple, pd.DataFrame)):
                    candidates.append((f"{key}.{sub_key}", sub_value))

    best_df = pd.DataFrame()
    best_score = -1
    best_name = "-"

    for name, candidate in candidates:
        df = _fp_as_dataframe(candidate)

        if df.empty or "Vade" not in df.columns:
            continue

        score = _fp_table_score(df)

        if score > best_score:
            best_score = score
            best_df = df
            best_name = name

    if not best_df.empty:
        try:
            best_df.attrs["source_name"] = best_name
            best_df.attrs["source_score"] = best_score
        except Exception:
            pass

    return best_df


def _fp_overview_future_df(forecast_data):
    import pandas as pd

    df = _fp_find_best_future_raw_df(forecast_data)

    if df.empty:
        return pd.DataFrame()

    # Eski/yeni kolon isimlerini tek forma indir.
    if "Baz Senaryo" in df.columns:
        df["Baz Fiyat"] = df["Baz Senaryo"]
    elif "Tahmin" in df.columns:
        df["Baz Fiyat"] = df["Tahmin"]

    if "Nominal Getiri %" in df.columns:
        df["Baz Getiri"] = df["Nominal Getiri %"]

    if "Sermaye Karşılığı" in df.columns:
        df["Baz Sermaye"] = df["Sermaye Karşılığı"]

    display = pd.DataFrame()
    display["Vade"] = df["Vade"] if "Vade" in df.columns else ""

    if "Baz Fiyat" in df.columns:
        display["Baz Senaryo"] = df["Baz Fiyat"].apply(_fp_money)

    if "Baz Getiri" in df.columns:
        display["Olası Getiri"] = df["Baz Getiri"].apply(_fp_pct)

    if "Baz Sermaye" in df.columns:
        display["Sermaye Karşılığı"] = df["Baz Sermaye"].apply(_fp_money)

    if "Konsensüs Model Sayısı" in df.columns:
        display["Model Sayısı"] = df["Konsensüs Model Sayısı"]

    if "Lider Model" in df.columns:
        display["Lider Model"] = df["Lider Model"]

    if "Lider Ağırlık %" in df.columns:
        display["Lider Ağırlık"] = df["Lider Ağırlık %"].apply(_fp_pct)

    return display


def _fp_pick_overview_row(forecast_data, selected_label=None):
    df = _fp_find_best_future_raw_df(forecast_data)

    if df.empty:
        return {}

    preferred = []
    if selected_label:
        preferred.append(str(selected_label).strip())
    preferred.extend(["1 Ay", "1 Hafta", "3 Ay", "1 Takvim Günü"])

    seen = set()
    preferred = [x for x in preferred if not (x in seen or seen.add(x))]

    if "Vade" in df.columns:
        for label in preferred:
            matched = df[df["Vade"].astype(str).str.strip() == label]
            if not matched.empty:
                return matched.iloc[0].to_dict()

    return df.iloc[0].to_dict()


def _fp_current_price(forecast_data, current_price=None):
    if current_price not in [None, "", "-"]:
        return current_price

    if isinstance(forecast_data, dict):
        for key in [
            "current_price",
            "guncel_fiyat",
            "son_fiyat",
            "spot_price",
            "last_price",
            "mevcut_fiyat",
        ]:
            if forecast_data.get(key) not in [None, "", "-"]:
                return forecast_data.get(key)

    return None

def render_analysis_tabs(
    data,
    news_items,
    inputs,
    current_price,
    forecast_data,
    ai_bundle=None,
) -> None:
    """Premium sekmeli analiz merkezi.

    İlk ekran sade kalır.
    Ağır test, faktör, vade ve tanı tabloları ayrı sekmelere taşınır.
    """

    st.markdown(
        """
        <style>
        .fp-workspace-title {
            margin-top: 0.4rem;
            margin-bottom: 0.7rem;
            padding: 18px 20px;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(8, 18, 35, 0.96), rgba(12, 42, 70, 0.86));
            border: 1px solid rgba(56, 189, 248, 0.25);
            box-shadow: 0 16px 38px rgba(0,0,0,0.28);
        }

        .fp-workspace-title h2 {
            margin: 0;
            color: #eaf7ff;
            font-size: 1.45rem;
            letter-spacing: 0.01em;
        }

        .fp-workspace-title p {
            margin: 6px 0 0 0;
            color: rgba(226, 242, 255, 0.72);
            font-size: 0.92rem;
        }

        .fp-section-card {
            padding: 16px 18px;
            margin: 12px 0 16px 0;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(15, 35, 60, 0.82));
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 12px 28px rgba(0,0,0,0.20);
        }

        .fp-section-card.blue {
            border-color: rgba(56, 189, 248, 0.32);
        }

        .fp-section-card.purple {
            border-color: rgba(168, 85, 247, 0.34);
        }

        .fp-section-card.green {
            border-color: rgba(34, 197, 94, 0.32);
        }

        .fp-section-card.gold {
            border-color: rgba(245, 158, 11, 0.34);
        }

        .fp-section-card.gray {
            border-color: rgba(148, 163, 184, 0.28);
        }

        .fp-section-kicker {
            text-transform: uppercase;
            letter-spacing: 0.13em;
            font-size: 0.72rem;
            color: rgba(125, 211, 252, 0.82);
            font-weight: 800;
            margin-bottom: 4px;
        }

        .fp-section-title {
            color: #f8fafc;
            font-size: 1.18rem;
            font-weight: 850;
            margin-bottom: 6px;
        }

        .fp-section-note {
            color: rgba(226, 232, 240, 0.76);
            font-size: 0.92rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(20,43,74,0.86));
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.20);
        }

        button[data-baseweb="tab"] {
            border-radius: 999px;
            padding: 8px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="fp-workspace-title">
            <h2>Finansal Analiz Merkezi</h2>
            <p>Genel özet sade tutuldu. Testler, faktörler, vade doğrulaması ve tanı panelleri ayrı bölümlere taşındı.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Genel Bakış",
            "Analiz Sonuçları",
            "Testler ve Backtest",
            "Faktör Analizi",
            "Vade Analizi",
            "AI Haberler",
            "Tanı Paneli",
        ]
    )

    def _safe_money(value):
        try:
            return f"{float(value):,.2f} {inputs.currency_symbol}"
        except Exception:
            return "-"

    def _safe_pct(value):
        try:
            return f"%{float(value) * 100:.2f}"
        except Exception:
            return "-"

    def _parse_numeric_value(value):
        """TL, yüzde, Türkçe virgül/nokta formatlarını güvenli sayıya çevirir."""
        try:
            if value is None:
                return None

            if isinstance(value, (int, float)):
                return float(value)

            text_value = str(value)
            text_value = (
                text_value
                .replace("₺", "")
                .replace("TL", "")
                .replace("%", "")
                .replace("\xa0", "")
                .replace(" ", "")
                .strip()
            )

            if not text_value:
                return None

            if "," in text_value and "." in text_value:
                # 1.055,13 gibi Türkçe format
                if text_value.rfind(",") > text_value.rfind("."):
                    text_value = text_value.replace(".", "").replace(",", ".")
                # 1,055.13 gibi İngilizce format
                else:
                    text_value = text_value.replace(",", "")
            elif "," in text_value:
                text_value = text_value.replace(".", "").replace(",", ".")

            number = float(text_value)

            if not pd.notna(number):
                return None

            return number
        except Exception:
            return None


    def _get_future_table():
        """forecast_data içindeki gelecek senaryo tablosunu güvenli bulur."""
        candidate_keys = [
            "gelecek_tablo",
            "gelecek_tablo_df",
            "future_table",
            "future_scenarios",
            "senaryo_tablosu",
        ]

        def _to_table(value):
            try:
                if isinstance(value, pd.DataFrame):
                    table = value.copy()
                elif isinstance(value, (list, tuple, dict)):
                    table = pd.DataFrame(value)
                else:
                    return None

                if table.empty:
                    return None

                useful_columns = {
                    "Vade",
                    "Baz Senaryo",
                    "Baz Fiyat",
                    "Tahmin",
                    "Nominal Getiri %",
                    "Baz Sermaye",
                    "Sermaye Karşılığı",
                }

                if useful_columns.intersection(set(table.columns)):
                    return table

                return None
            except Exception:
                return None

        for key in candidate_keys:
            table = _to_table(forecast_data.get(key))
            if table is not None:
                return table

        for value in forecast_data.values():
            table = _to_table(value)
            if table is not None:
                return table

        return None


    def _get_model_weights():
        weights = forecast_data.get("model_agirliklari")
        if isinstance(weights, dict):
            return weights
        return {}

    future_table = _get_future_table()
    model_weights = _get_model_weights()

    with tabs[0]:
        safe_render_panel(
            "Genel Bakış",
            render_first_overview_panel,
            data=data,
            asset_name=inputs.asset_name,
            market_symbol=inputs.market_symbol,
            current_price=current_price,
            investment_amount=inputs.investment_amount,
            currency_rate=inputs.currency_rate,
            currency_symbol=inputs.currency_symbol,
            forecast_data=forecast_data,
            selected_horizon=getattr(inputs, "forecast_label", None),
            forecast_days=getattr(inputs, "forecast_days", None),
        )

    with tabs[1]:


        st.markdown(
            """
            <div class="fp-section-card blue">
                <div class="fp-section-kicker">Scenario Results</div>
                <div class="fp-section-title">Analiz Sonuçları ve Senaryo Görünümü</div>
                <div class="fp-section-note">
                    Grafikler, senaryo bandı ve detaylı gelecek tabloları bu bölümde gösterilir.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        safe_render_panel("Genel Bakış", render_landing_panel,
            data=data,
            asset_name=inputs.asset_name,
            current_price=current_price,
            investment_amount=inputs.investment_amount,
            currency_rate=inputs.currency_rate,
            currency_symbol=inputs.currency_symbol,
            forecast_data=forecast_data,
            selected_horizon=getattr(inputs, "forecast_label", None),
        )

        st.markdown("---")

        safe_render_panel("Analiz Sonuçları", render_analysis_panel,
            data=data,
            asset_name=inputs.asset_name,
            current_price=current_price,
            currency_rate=inputs.currency_rate,
            forecast_data=forecast_data,
            ai_bundle=ai_bundle,
        )

        st.markdown("---")

        safe_render_panel("Konsensüs Paneli", render_consensus_panel,
            forecast_data=forecast_data,
            last_date=data.index[-1],
        )

    with tabs[2]:


        st.markdown(
            """
            <div class="fp-section-card purple">
                <div class="fp-section-kicker">Backtest Lab</div>
                <div class="fp-section-title">Testler & Backtest</div>
                <div class="fp-section-note">
                    Modellerin geçmiş performansı, benchmark karşılaştırması, konsensüs kararı ve karar nedenleri burada incelenir.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        safe_render_panel("Testler ve Backtest", render_backtest_decision_panel,
            forecast_data=forecast_data,
        )

        with st.expander("Detaylı tarihsel performans penceresi", expanded=False):
            safe_render_panel("Performans Paneli", render_performance_panel,
                data=data,
                current_price=current_price,
                investment_amount=inputs.investment_amount,
                currency_rate=inputs.currency_rate,
                currency_symbol=inputs.currency_symbol,
            )

    with tabs[3]:


        st.markdown(
            """
            <div class="fp-section-card green">
                <div class="fp-section-kicker">Dynamic Factor Engine</div>
                <div class="fp-section-title">Faktör Analizi</div>
                <div class="fp-section-note">
                    EViews benzeri OLS, katsayılar, etki payları, VIF ve faktör veri tanıları bu bölümde yer alır.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        safe_render_panel("Faktör Analizi", render_eviews_regression_panel,
            data=data,
            forecast_days=inputs.forecast_days,
            market_symbol=inputs.market_symbol,
            asset_name=inputs.asset_name,
            asset_type=inputs.asset_type,
            currency_symbol=inputs.currency_symbol,
            currency_rate=inputs.currency_rate,
        )

    with tabs[4]:


        st.markdown(
            """
            <div class="fp-section-card gold">
                <div class="fp-section-kicker">Horizon Validation</div>
                <div class="fp-section-title">Vade Bazlı Doğrulama</div>
                <div class="fp-section-note">
                    Modelin kısa, orta ve uzun vadelerde farklı benchmarklara karşı performansı burada ölçülür.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        safe_render_panel("Vade Analizi", render_horizon_validation_panel,
            data=data,
            market_symbol=inputs.market_symbol,
            asset_name=inputs.asset_name,
            asset_type=inputs.asset_type,
        )

    with tabs[5]:


        st.markdown(
            """
            <div class="fp-section-card blue">
                <div class="fp-section-kicker">AI News Layer</div>
                <div class="fp-section-title">AI Haberler ve Yorumlar</div>
                <div class="fp-section-note">
                    Haber akışı ve AI yorumları burada ayrı tutulur.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        safe_render_panel("AI Haberler", render_news_panel,
            news_items=news_items,
            asset_name=inputs.asset_name,
            ai_bundle=ai_bundle,
        )

    with tabs[6]:


        st.markdown(
            """
            <div class="fp-section-card gray">
                <div class="fp-section-kicker">Developer Diagnostics</div>
                <div class="fp-section-title">Tanı Paneli</div>
                <div class="fp-section-note">
                    Veri, feature, model ve hesaplama ön koşulları burada incelenir.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        safe_render_panel("Tanı Paneli", render_developer_diagnostics_panel,

            data=data,
            forecast_days=inputs.forecast_days,
            market_symbol=inputs.market_symbol,
            asset_name=inputs.asset_name,
        )

        safe_render_panel("Çalışma ve Performans Takibi", render_runtime_diagnostics_panel)



def _build_watchlist_snapshot(
    data,
    current_price,
    forecast_data,
    forecast_label,
    forecast_days,
    investment_amount,
    currency_rate,
):
    """İzleme listesi için geçmiş ve gelecek yatırım özetini hazırlar."""
    snapshot = {
        "selected_horizon": str(forecast_label or "Seçili vade"),
        "forecast_days": int(forecast_days or 0),
        "invested_capital": float(investment_amount or 0.0),
        "current_price": None,
        "past_price": None,
        "same_position_past_value": None,
        "past_investment_today_value": None,
        "historical_return_percent": None,
        "future_pessimistic_capital": None,
        "future_base_capital": None,
        "future_optimistic_capital": None,
        "future_base_return_percent": None,
    }

    try:
        rate = float(currency_rate or 1.0)
        current_raw = float(current_price)
        invested = float(investment_amount or 0.0)

        snapshot["current_price"] = current_raw * rate

        if data is not None and not data.empty and "Close" in data.columns:
            close_series = pd.to_numeric(
                data["Close"],
                errors="coerce",
            ).dropna()

            days = max(int(forecast_days or 1), 1)

            if len(close_series) > days:
                past_raw = float(close_series.iloc[-(days + 1)])
                past_display = past_raw * rate

                snapshot["past_price"] = past_display

                if current_raw > 0 and past_raw > 0 and invested > 0:
                    # Bugünkü yatırım tutarıyla alınan aynı miktardaki
                    # varlığın seçilen vade önceki parasal değeri.
                    snapshot["same_position_past_value"] = (
                        invested * past_raw / current_raw
                    )

                    # Seçilen vade önce aynı sermaye yatırılmış olsaydı
                    # bugün ulaşacağı yaklaşık değer.
                    snapshot["past_investment_today_value"] = (
                        invested * current_raw / past_raw
                    )

                    snapshot["historical_return_percent"] = (
                        (current_raw / past_raw) - 1.0
                    ) * 100.0

        future_df = None
        if isinstance(forecast_data, dict):
            candidate = forecast_data.get("gelecek_df")
            if isinstance(candidate, pd.DataFrame):
                future_df = candidate.copy()

        if future_df is not None and not future_df.empty:
            selected_label = str(forecast_label or "").strip().casefold()

            matching = future_df[
                future_df["Vade"]
                .astype(str)
                .str.strip()
                .str.casefold()
                .eq(selected_label)
            ]

            if matching.empty:
                future_row = future_df.iloc[-1]
            else:
                future_row = matching.iloc[0]

            def number(column_name):
                value = future_row.get(column_name)
                try:
                    numeric = pd.to_numeric(
                        pd.Series([value]),
                        errors="coerce",
                    ).iloc[0]
                    return None if pd.isna(numeric) else float(numeric)
                except Exception:
                    return None

            snapshot["future_pessimistic_capital"] = number(
                "Kötümser Sermaye"
            )
            snapshot["future_base_capital"] = number(
                "Sermaye Karşılığı"
            )
            snapshot["future_optimistic_capital"] = number(
                "İyimser Sermaye"
            )
            snapshot["future_base_return_percent"] = number(
                "Nominal Getiri %"
            )

    except Exception:
        # İzleme özeti üretilemese bile ana analiz durdurulmaz.
        pass

    return snapshot



def run_analysis(inputs) -> None:
    """Seçilen varlık için veri, tahmin ve panel akışını çalıştırır."""
    mark_analysis_start()
    progress = AnalysisProgress()

    try:
        progress.update(18, "Piyasa verileri alınıyor...")
        progress.update(18, "Piyasa verileri alınıyor...")
        market_result = get_cached_asset_history_with_metadata(
            inputs.market_symbol
        )
        progress.update(30, "Finansal geçmiş yüklendi.")
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

        data = _clean_analysis_market_data(data)
        current_price = _get_last_valid_close(data)

        asset_type = normalize_asset_type(
            asset_type=getattr(inputs, "asset_type", None),
            market_symbol=inputs.market_symbol,
        )

        progress.update(42, "Haber akışı kontrol ediliyor...")
        news_items = get_cached_news(
            inputs.asset_name.split("(")[0]
        )
        progress.update(48, "Haber akışı kontrol edildi.")

        progress.update(
            50,
            "Monte Carlo simülasyonları ve ML rota optimizasyonu tamamlanıyor...",
        )

        progress.update(58, "Tahmin modelleri hesaplanıyor...")
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

        try:
            progress.update(84, "AI haber ve teknik senaryo sentezi çalışıyor...")
            ai_bundle = ai_haberleri_toplu_analiz_et(
                varlik=inputs.asset_name,
                haberler=news_items,
                anlik=current_price,
                boga=float(forecast_data["boga"]),
                ayi=float(forecast_data["ayi"]),
            )
        finally:
            pass

        progress.update(80, "Risk metrikleri hesaplanıyor...")
        progress.complete()

        progress.update(94, "Sonuç panelleri hazırlanıyor...")
        render_strategic_ai_panel(
            ai_bundle=ai_bundle,
            forecast_data=forecast_data,
            investment_amount=inputs.investment_amount,
            current_price=current_price,
            currency_rate=inputs.currency_rate,
            currency_symbol=inputs.currency_symbol,
            asset_name=inputs.asset_name,
            selected_horizon_label=inputs.forecast_label,
        )

        render_data_source_notice(market_metadata)

        watchlist_snapshot = _build_watchlist_snapshot(
            data=data,
            current_price=current_price,
            forecast_data=forecast_data,
            forecast_label=getattr(inputs, "forecast_label", None),
            forecast_days=getattr(inputs, "forecast_days", None),
            investment_amount=getattr(inputs, "investment_amount", None),
            currency_rate=getattr(inputs, "currency_rate", None),
        )

        st.session_state["last_analysis_payload"] = {
            "asset_name": inputs.asset_name,
            "market_symbol": inputs.market_symbol,
            "forecast_label": getattr(inputs, "forecast_label", None),
            "forecast_days": getattr(inputs, "forecast_days", None),
            "investment_amount": getattr(inputs, "investment_amount", None),
            "currency_symbol": getattr(inputs, "currency_symbol", None),
            "currency_rate": getattr(inputs, "currency_rate", None),
            "current_price": current_price,
            "forecast_data": forecast_data,
            "watchlist_snapshot": watchlist_snapshot,
            "ai_bundle": ai_bundle,
            "market_metadata": market_metadata,
        }

        try:
            if isinstance(st.session_state.get("last_analysis_payload"), dict):
                st.session_state["last_analysis_payload"].update(
                    {
                        "price_data": data,
                        "forecast_data": forecast_data,
                        "ai_bundle": ai_bundle,
                        "investment_amount": inputs.investment_amount,
                        "current_price": current_price,
                        "currency_symbol": inputs.currency_symbol,
                        "forecast_label": inputs.forecast_label,
                        "asset_name": inputs.asset_name,
                        "market_symbol": inputs.market_symbol,
                    }
                )
        except Exception:
            pass

        render_analysis_tabs(
            data=data,
            news_items=news_items,
            inputs=inputs,
            current_price=current_price,
            forecast_data=forecast_data,
            ai_bundle=ai_bundle,
        )
        mark_analysis_end(success=True)

    except Exception as exc:
        progress.close()
        mark_analysis_end(success=False, error=str(exc))
        render_analysis_error(exc)


def main() -> None:
    """Streamlit uygulamasının ana çalışma akışı."""
    initialize_application()
    inject_global_premium_theme()
    render_app_intro()

    currency_result = get_cached_currencies_with_metadata()
    currencies = currency_result.get("rates", {})
    currency_metadata = currency_result.get("metadata")

    render_market_ticker(currencies)

    inputs = render_input_panel(currencies)
    render_currency_source_notice(currency_metadata)

    st.divider()

    initialize_analysis_state()
    analysis_clicked = render_analysis_button()

    if analysis_clicked:
        st.session_state["analysis_requested"] = False
        run_analysis(inputs)

    render_action_footer()


if __name__ == "__main__":
    main()
