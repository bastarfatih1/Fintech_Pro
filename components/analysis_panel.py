"""
Ana analiz paneli.

Bu bileşen risk metriklerini, RSI uyarısını,
fiyat grafiğini ve AI teknik analiz özetini gösterir.
"""

from typing import Any, Mapping, Optional

import pandas as pd
import streamlit as st
from components.premium_charts import render_premium_plotly_chart
from components.premium_ui import render_premium_table

from charts.candlestick import create_price_volume_chart
from charts.rsi import analyze_rsi
from components.metrics import render_risk_metrics
from components.ui_icons import icon_html
from haber_motoru import ai_teknik_analiz_yorumu
from components.education_layer import (
    build_plain_market_summary,
    render_chart_explanation,
    render_plain_explainer,
    render_term_grid,
)



def _inject_premium_summary_style() -> None:
    """Analiz özetine premium terminal görünümü verir."""
    st.markdown(
        """
        <style>

        .fp-exec-pulse {
            border: 1px solid rgba(56, 189, 248, 0.30);
            border-radius: 24px;
            padding: 20px 22px;
            margin: 8px 0 18px 0;
            background:
                radial-gradient(circle at 12% 10%, rgba(56, 189, 248, 0.22), transparent 34%),
                radial-gradient(circle at 86% 16%, rgba(134, 239, 172, 0.13), transparent 30%),
                linear-gradient(135deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.94));
            box-shadow: 0 22px 58px rgba(2, 6, 23, 0.34);
        }
        .fp-exec-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) minmax(260px, 0.75fr);
            gap: 18px;
            align-items: stretch;
        }
        .fp-exec-kicker {
            color: #93c5fd;
            font-size: 0.74rem;
            letter-spacing: 0.17em;
            text-transform: uppercase;
            font-weight: 850;
            margin-bottom: 8px;
        }
        .fp-exec-signal {
            color: #f8fafc;
            font-size: 1.72rem;
            line-height: 1.12;
            font-weight: 900;
            letter-spacing: -0.03em;
            margin-bottom: 9px;
        }
        .fp-exec-summary {
            color: #cbd5e1;
            line-height: 1.58;
            font-size: 0.96rem;
            max-width: 860px;
        }
        .fp-exec-stack {
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 18px;
            padding: 14px 15px;
            background: rgba(15, 23, 42, 0.54);
        }
        .fp-exec-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }
        .fp-exec-row:last-child {
            border-bottom: 0;
        }
        .fp-exec-label {
            color: #94a3b8;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .fp-exec-value {
            color: #f8fafc;
            font-size: 0.86rem;
            font-weight: 850;
            text-align: right;
        }
        .fp-exec-positive {
            color: #86efac;
        }
        .fp-exec-negative {
            color: #fca5a5;
        }
        .fp-exec-neutral {
            color: #cbd5e1;
        }
        .fp-exec-note {
            margin-top: 12px;
            color: #94a3b8;
            font-size: 0.76rem;
            line-height: 1.45;
        }
        @media (max-width: 860px) {
            .fp-exec-grid {
                grid-template-columns: 1fr;
            }
        }

        .fp-hero {
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 22px;
            padding: 22px 24px;
            margin: 10px 0 18px 0;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.22), transparent 34%),
                radial-gradient(circle at bottom right, rgba(34, 197, 94, 0.16), transparent 30%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.92));
            box-shadow: 0 18px 48px rgba(2, 6, 23, 0.28);
        }
        .fp-eyebrow {
            color: #93c5fd;
            font-size: 0.78rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .fp-title {
            color: #f8fafc;
            font-size: 1.48rem;
            font-weight: 850;
            margin-bottom: 6px;
        }
        .fp-subtitle {
            color: #cbd5e1;
            font-size: 0.95rem;
            line-height: 1.55;
            max-width: 920px;
        }
        .fp-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }
        .fp-pill {
            border: 1px solid rgba(226, 232, 240, 0.18);
            border-radius: 999px;
            padding: 6px 10px;
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.48);
            font-size: 0.78rem;
        }
        .fp-card {
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 18px;
            padding: 15px 16px;
            background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
            min-height: 122px;
        }
        .fp-card-label {
            color: #94a3b8;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 7px;
        }
        .fp-card-value {
            color: #f8fafc;
            font-size: 1.30rem;
            font-weight: 850;
            line-height: 1.18;
        }
        .fp-card-delta-positive {
            color: #86efac;
            font-size: 0.82rem;
            margin-top: 8px;
            font-weight: 750;
        }
        .fp-card-delta-negative {
            color: #fca5a5;
            font-size: 0.82rem;
            margin-top: 8px;
            font-weight: 750;
        }
        .fp-card-delta-neutral {
            color: #cbd5e1;
            font-size: 0.82rem;
            margin-top: 8px;
            font-weight: 750;
        }
        .fp-status {
            border-left: 4px solid #38bdf8;
            border-radius: 14px;
            padding: 12px 14px;
            background: rgba(14, 165, 233, 0.10);
            color: #e2e8f0;
            line-height: 1.55;
            margin-top: 14px;
        }
        .fp-mini-note {
            color: #94a3b8;
            font-size: 0.78rem;
            margin-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_money(value: float) -> str:
    """Büyük sayıları sade ve etkileyici biçimde gösterir."""
    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"{value:,.2f}"

    return f"{value:.2f}"


def _get_return_tone(value: float) -> str:
    """Getiriye göre HTML sınıfı belirler."""
    if value > 2:
        return "fp-card-delta-positive"
    if value < -2:
        return "fp-card-delta-negative"
    return "fp-card-delta-neutral"


def _get_insight_badge(
    risk_level: str,
    confidence: float,
    nominal_return: float,
) -> str:
    """Özet için kullanıcıyı yakalayan kısa durum rozeti üretir."""
    if confidence >= 70 and nominal_return > 5 and risk_level != "Yüksek":
        return "Güçlü model uyumu"
    if confidence < 40:
        return "Düşük güven modu"
    if risk_level == "Yüksek":
        return "Yüksek risk radarı"
    if nominal_return > 5:
        return "Pozitif senaryo"
    if nominal_return < -5:
        return "Defansif görünüm"
    return "Nötr izleme modu"


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Sayısal değeri güvenli şekilde float'a çevirir."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return default

    if pd.isna(numeric_value):
        return default

    return numeric_value


def _get_primary_horizon_row(forecast_data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Özet için ilk uygun gelecek senaryosu satırını döndürür."""
    future_table = forecast_data.get("gelecek_df")

    if not isinstance(future_table, pd.DataFrame) or future_table.empty:
        return {}

    preferred_horizons = ("1 Ay", "3 Ay", "6 Ay", "1 Yıl")

    if "Vade" in future_table.columns:
        for horizon in preferred_horizons:
            matched = future_table[
                future_table["Vade"].astype(str) == horizon
            ]
            if not matched.empty:
                return matched.iloc[0].to_dict()

    return future_table.iloc[0].to_dict()


def _calculate_model_confidence(forecast_data: Mapping[str, Any]) -> float:
    """
    Model güvenini basit ve açıklanabilir bir skor olarak hesaplar.

    Bu skor yatırım garantisi değildir; yalnızca çalışan modellerin
    ağırlık, backtest ve stabilite görünümünü özetler.
    """
    model_weights = forecast_data.get("model_agirliklari", {})
    backtest_table = forecast_data.get("backtest_df")

    active_weight = 0.0

    if isinstance(model_weights, Mapping):
        for raw_weight in model_weights.values():
            active_weight += max(_safe_float(raw_weight), 0.0)

    active_weight_score = min(active_weight, 1.0) * 100.0

    if not isinstance(backtest_table, pd.DataFrame) or backtest_table.empty:
        return round(active_weight_score * 0.6, 1)

    evaluated = backtest_table.copy()

    if "Model" in evaluated.columns:
        evaluated = evaluated[
            evaluated["Model"].astype(str) != "Naive_Last_Price"
        ]

    if evaluated.empty:
        return round(active_weight_score * 0.6, 1)

    reference_score = 50.0

    if "Referansı Geçti" in evaluated.columns:
        passed = (
            evaluated["Referansı Geçti"]
            .astype(str)
            .str.lower()
            .eq("evet")
        )
        reference_score = float(passed.mean() * 100.0)

    stability_score = 50.0

    if "Stabilite Skoru" in evaluated.columns:
        stability_values = pd.to_numeric(
            evaluated["Stabilite Skoru"],
            errors="coerce",
        ).dropna()

        if not stability_values.empty:
            stability_score = float(stability_values.mean())

    confidence = (
        active_weight_score * 0.45
        + reference_score * 0.35
        + stability_score * 0.20
    )

    return round(float(max(0.0, min(confidence, 100.0))), 1)


def _classify_risk_level(stats: Mapping[str, Any]) -> str:
    """Risk metriklerinden basit risk seviyesi etiketi üretir."""
    volatility = _safe_float(
        stats.get("Yıllık Volatilite", stats.get("Volatilite", 0.0))
    )
    max_drawdown = abs(
        _safe_float(
            stats.get("Maksimum Düşüş", stats.get("Max Drawdown", 0.0))
        )
    )
    beta = abs(_safe_float(stats.get("Beta", 1.0), default=1.0))

    risk_points = 0

    if volatility > 35:
        risk_points += 2
    elif volatility > 20:
        risk_points += 1

    if max_drawdown > 35:
        risk_points += 2
    elif max_drawdown > 20:
        risk_points += 1

    if beta > 1.4:
        risk_points += 1

    if risk_points >= 4:
        return "Yüksek"
    if risk_points >= 2:
        return "Orta"
    return "Düşük"


def _build_general_status(
    current_price: float,
    base_target: float,
    lower_target: float,
    upper_target: float,
    confidence: float,
) -> str:
    """Özet için kısa, tavsiye olmayan genel durum cümlesi üretir."""
    current = max(float(current_price), 1e-9)
    base_return = ((base_target - current) / current) * 100.0
    band_width = ((upper_target - lower_target) / current) * 100.0

    if base_return > 5:
        direction = "Baz senaryo pozitif yönde ayrışıyor"
    elif base_return < -5:
        direction = "Baz senaryo negatif yönde ayrışıyor"
    else:
        direction = "Baz senaryo sınırlı değişim gösteriyor"

    if band_width > 35:
        uncertainty = "belirsizlik yüksek"
    elif band_width > 18:
        uncertainty = "belirsizlik orta"
    else:
        uncertainty = "belirsizlik görece düşük"

    if confidence < 40:
        confidence_text = "model güveni zayıf"
    elif confidence < 70:
        confidence_text = "model güveni orta"
    else:
        confidence_text = "model güveni güçlü"

    return f"{direction}; {uncertainty} ve {confidence_text}."


def _classify_executive_signal(
    risk_level: str,
    confidence: float,
    nominal_return: float,
    band_width: float,
) -> tuple[str, str]:
    """Al/sat dili kullanmadan üst seviye model sentezi üretir."""
    if confidence < 40:
        return "Düşük Güven Modu", "fp-exec-neutral"

    if band_width > 35 and risk_level == "Yüksek":
        return "Yüksek Belirsizlik", "fp-exec-negative"

    if nominal_return > 5 and risk_level != "Yüksek":
        return "Pozitif Senaryo", "fp-exec-positive"

    if nominal_return < -5:
        return "Negatif Baskı", "fp-exec-negative"

    if confidence >= 70:
        return "Model Uyumu Güçlü", "fp-exec-positive"

    return "Nötr Görünüm", "fp-exec-neutral"


def _render_executive_market_pulse(
    signal_label: str,
    signal_class: str,
    horizon: str,
    risk_level: str,
    confidence: float,
    nominal_return: float,
    band_width: float,
    general_status: str,
) -> None:
    """Grafikten önce görünen üst düzey sentez kartını gösterir."""
    st.markdown(
        f"""
        <div class="fp-exec-pulse">
            <div class="fp-exec-grid">
                <div>
                    <div class="fp-exec-kicker">Executive Market Pulse</div>
                    <div class="fp-exec-signal {signal_class}">
                        {signal_label}
                    </div>
                    <div class="fp-exec-summary">
                        {general_status}
                        Seçili vade için model çıktısı; risk, güven ve senaryo
                        genişliği birlikte değerlendirilerek özetlenmiştir.
                    </div>
                    <div class="fp-exec-note">
                        Bu sentez al/sat yönlendirmesi değildir. Modelin mevcut
                        veri setindeki senaryo görünümünü sadeleştirir.
                    </div>
                </div>
                <div class="fp-exec-stack">
                    <div class="fp-exec-row">
                        <div class="fp-exec-label">Vade</div>
                        <div class="fp-exec-value">{horizon}</div>
                    </div>
                    <div class="fp-exec-row">
                        <div class="fp-exec-label">Model Güveni</div>
                        <div class="fp-exec-value">%{confidence:.1f}</div>
                    </div>
                    <div class="fp-exec-row">
                        <div class="fp-exec-label">Risk Seviyesi</div>
                        <div class="fp-exec-value">{risk_level}</div>
                    </div>
                    <div class="fp-exec-row">
                        <div class="fp-exec-label">Senaryo Farkı</div>
                        <div class="fp-exec-value {signal_class}">{nominal_return:+.2f}%</div>
                    </div>
                    <div class="fp-exec-row">
                        <div class="fp-exec-label">Bant Genişliği</div>
                        <div class="fp-exec-value">%{band_width:.1f}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _get_ai_bundle_text(ai_bundle: Optional[Mapping[str, Any]], key: str) -> str:
    """AI bundle içinden güvenli metin okur."""
    if not isinstance(ai_bundle, Mapping):
        return ""

    value = ai_bundle.get(key, "")

    if value is None:
        return ""

    return str(value).strip()


def _news_effect_tone(effect: str) -> str:
    """Haber etkisine göre güvenli CSS sınıfı döndürür."""
    upper_effect = str(effect).upper()

    if "POZ" in upper_effect:
        return "fp-exec-positive"
    if "NEG" in upper_effect:
        return "fp-exec-negative"
    return "fp-exec-neutral"


def _render_news_effect_summary(ai_bundle: Optional[Mapping[str, Any]]) -> None:
    """Haber etkisini genel analiz içine ekler."""
    if not isinstance(ai_bundle, Mapping):
        return

    effect = _get_ai_bundle_text(ai_bundle, "overall_news_effect") or "NÖTR"
    summary = _get_ai_bundle_text(ai_bundle, "news_effect_summary")
    synthesis = _get_ai_bundle_text(ai_bundle, "market_synthesis")

    if not summary and not synthesis:
        return

    tone = _news_effect_tone(effect)

    st.markdown(
        f"""
        <div class="fp-status">
            <strong>Haber Etkisi:</strong>
            <span class="{tone}">{effect}</span>
            <br/>
            <span>{summary or synthesis}</span>
            <br/>
            <span class="fp-mini-note">
                Haber etkisi, fiyat tahmini yerine haber başlıklarının genel
                senaryo okumasına katkısını gösterir. Yatırım tavsiyesi değildir.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _render_professional_summary(
    current_price: float,
    currency_rate: float,
    forecast_data: Mapping[str, Any],
    ai_bundle: Optional[Mapping[str, Any]] = None,
) -> None:
    """Analiz sonucunu premium terminal tarzı bir özetle gösterir."""
    summary_row = _get_primary_horizon_row(forecast_data)

    if not summary_row:
        return

    base_target = _safe_float(
        summary_row.get("Baz Senaryo", summary_row.get("Tahmin")),
        default=0.0,
    )
    lower_target = _safe_float(
        summary_row.get("Kötümser Senaryo"),
        default=base_target,
    )
    upper_target = _safe_float(
        summary_row.get("İyimser Senaryo"),
        default=base_target,
    )
    nominal_return = _safe_float(summary_row.get("Nominal Getiri %"))
    horizon = str(summary_row.get("Vade", "Seçili Vade"))

    current_display = current_price * currency_rate
    confidence = _calculate_model_confidence(forecast_data)
    risk_level = _classify_risk_level(forecast_data.get("stats", {}))
    general_status = _build_general_status(
        current_price=current_display,
        base_target=base_target,
        lower_target=lower_target,
        upper_target=upper_target,
        confidence=confidence,
    )
    badge = _get_insight_badge(
        risk_level=risk_level,
        confidence=confidence,
        nominal_return=nominal_return,
    )

    band_width = 0.0
    if current_display > 0:
        band_width = ((upper_target - lower_target) / current_display) * 100.0

    _inject_premium_summary_style()

    signal_label, signal_class = _classify_executive_signal(
        risk_level=risk_level,
        confidence=confidence,
        nominal_return=nominal_return,
        band_width=band_width,
    )

    _render_executive_market_pulse(
        signal_label=signal_label,
        signal_class=signal_class,
        horizon=horizon,
        risk_level=risk_level,
        confidence=confidence,
        nominal_return=nominal_return,
        band_width=band_width,
        general_status=general_status,
    )

    render_plain_explainer(
        title="Bu ekran neyi anlatıyor?",
        simple=build_plain_market_summary(
            signal_label=signal_label,
            risk_level=risk_level,
            confidence=confidence,
            nominal_return=nominal_return,
            band_width=band_width,
        ),
        why=(
            "Bu bölüm fiyatı, riski, model güvenini "
            "ve senaryo aralığını aynı yerde sade biçimde okur."
        ),
        watch="Bu özet yatırım tavsiyesi değildir; yalnızca veriyi anlaşılır hale getirir.",
    )

    st.markdown(
        f"""
        <div class="fp-hero">
            <div class="fp-eyebrow">Fintech Pro Intelligence Layer</div>
            <div class="fp-title"><span class="fp-title-with-icon">{icon_html("insight_lens")}</span>Veri Odaklı Analiz Özeti</div>
            <div class="fp-subtitle">
                Model konsensüsü, backtest sonuçları, risk profili ve senaryo aralığı
                tek ekranda okunabilir bir değerlendirme özetine dönüştürüldü.
            <div class="fp-pill-row">
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("scenario_path", "fp-icon-small")}</span>{horizon}</div>
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("consensus_mesh", "fp-icon-small")}</span>Model Güveni %{confidence:.1f}</div>
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("risk_shield", "fp-icon-small")}</span>Risk: {risk_level}</div>
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("signal_node", "fp-icon-small")}</span>{badge}</div>
        """,
        unsafe_allow_html=True,
    )

    col_price, col_base, col_range = st.columns(3)

    with col_price:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-card-label">Güncel Fiyat</div>
                <div class="fp-card-value">{_format_money(current_display)}</div>
                <div class="fp-card-delta-neutral">Seçili veri kaynağına göre hesaplandı</div>
            """,
            unsafe_allow_html=True,
        )

    with col_base:
        delta_class = _get_return_tone(nominal_return)
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-card-label">Baz Senaryo · {horizon}</div>
                <div class="fp-card-value">{_format_money(base_target)}</div>
                <div class="{delta_class}">{nominal_return:+.2f}% senaryo farkı</div>
            """,
            unsafe_allow_html=True,
        )

    with col_range:
        st.markdown(
            f"""
            <div class="fp-card">
                <div class="fp-card-label">Kalibre Senaryo Aralığı</div>
                <div class="fp-card-value">{_format_money(lower_target)} - {_format_money(upper_target)}</div>
                <div class="fp-card-delta-neutral">Bant genişliği: %{band_width:.1f}</div>
            """,
            unsafe_allow_html=True,
        )

    col_risk, col_confidence = st.columns(2)

    with col_risk:
        st.metric(
            "Risk Seviyesi",
            risk_level,
        )

    with col_confidence:
        st.metric(
            "Model Güveni",
            f"%{confidence:.1f}",
        )

    st.markdown(
        f"""
        <div class="fp-status">
            <strong>Genel durum:</strong> {general_status}
            <br/>
            <span class="fp-mini-note">
                Model güven skoru; geçmiş veri üzerindeki tutarlılık,
                backtest sonucu ve model ağırlıklarına dayanan istatistiksel
                bir göstergedir. Risk seviyesi tarihsel oynaklık ve düşüş
                metriklerini özetler. Bu alan yatırım tavsiyesi değildir.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_news_effect_summary(ai_bundle)


def _render_rsi_status(close_prices: pd.Series) -> None:
    """RSI sonucunu uygun Streamlit mesaj kutusunda gösterir."""
    try:
        rsi_result = analyze_rsi(close_prices)
    except Exception as exc:
        st.warning(
            "RSI analizi tamamlanamadı. "
            f"Detay: {exc}"
        )
        return

    if rsi_result.status == "overbought":
        st.warning(f"RSI uyarısı: {rsi_result.message}")
    elif rsi_result.status == "oversold":
        st.success(f"RSI sinyali: {rsi_result.message}")
    else:
        st.info(f"RSI durumu: {rsi_result.message}")


def _render_ai_summary(
    asset_name: str,
    current_price: float,
    bull_target: float,
    bear_target: float,
    ai_bundle: Optional[Mapping[str, Any]] = None,
) -> None:
    """AI teknik analiz özetini güvenli şekilde gösterir."""
    bundled_summary = _get_ai_bundle_text(ai_bundle, "technical_summary")
    bundled_synthesis = _get_ai_bundle_text(ai_bundle, "market_synthesis")
    bundled_risk_note = _get_ai_bundle_text(ai_bundle, "risk_note")

    if bundled_summary:
        ai_summary = bundled_summary
    else:
        try:
            ai_summary = ai_teknik_analiz_yorumu(
                asset_name,
                current_price,
                bull_target,
                bear_target,
            )
        except Exception as exc:
            st.warning(
                "AI teknik analiz özeti oluşturulamadı. "
                f"Detay: {exc}"
            )
            return

    st.markdown(
        f"""
        <div class="fp-status">
            <strong>AI analiz yorumu:</strong> {ai_summary}
            <br/>
            <span class="fp-mini-note">
                Bu görünür AI bölümü teknik model çıktısını ve haber etkisini daha anlaşılır
                bir özet haline getirir. Yatırım tavsiyesi değildir.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if bundled_synthesis:
        st.markdown(
            f"""
            <div class="fp-status">
                <strong>Piyasa sentezi:</strong> {bundled_synthesis}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if bundled_risk_note:
        st.caption(bundled_risk_note)


def render_analysis_panel(
    data: pd.DataFrame,
    asset_name: str,
    current_price: float,
    currency_rate: float,
    forecast_data: Mapping[str, Any],
    ai_bundle: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Ana analiz sekmesinin tamamını oluşturur.

    Args:
        data: Varlığın tarihsel fiyat verisi.
        asset_name: Kullanıcıya gösterilen varlık adı.
        current_price: Varlığın güncel fiyatı.
        currency_rate: Seçilen para birimi dönüşüm oranı.
        forecast_data: Risk metrikleri ve tahmin hedeflerini içeren sözlük.
    """
    required_keys = {"stats", "ayi", "boga"}
    missing_keys = required_keys.difference(forecast_data.keys())

    if missing_keys:
        st.error(
            "Ana analiz paneli için eksik veri alanları: "
            + ", ".join(sorted(missing_keys))
        )
        return

    st.markdown(f"### {asset_name} - Merkezi Terminal")

    _render_professional_summary(
        current_price=current_price,
        currency_rate=currency_rate,
        forecast_data=forecast_data,
        ai_bundle=ai_bundle,
    )

    _render_ai_summary(
        asset_name=asset_name,
        current_price=current_price,
        bull_target=float(forecast_data["boga"]),
        bear_target=float(forecast_data["ayi"]),
        ai_bundle=ai_bundle,
    )

    st.markdown("---")

    render_risk_metrics(forecast_data["stats"])

    st.markdown("---")

    if "Close" not in data.columns:
        st.error("RSI ve fiyat grafiği için Close sütunu bulunamadı.")
        return

    _render_rsi_status(data["Close"])

    try:
        price_figure = create_price_volume_chart(
            data=data,
            currency_rate=currency_rate,
            current_price=current_price,
            bear_target=forecast_data["ayi"],
            bull_target=forecast_data["boga"],
        )
    except Exception as exc:
        st.error(
            "Fiyat grafiği oluşturulamadı. "
            f"Detay: {exc}"
        )
    else:
        render_premium_plotly_chart(
            price_figure,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "responsive": True,
            },
        )

