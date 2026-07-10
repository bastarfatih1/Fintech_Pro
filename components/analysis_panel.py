"""
Ana analiz paneli.

Bu bileşen risk metriklerini, RSI uyarısını,
fiyat grafiğini ve AI teknik analiz özetini gösterir.
"""

from typing import Any, Mapping

import pandas as pd
import streamlit as st

from charts.candlestick import create_price_volume_chart
from charts.rsi import analyze_rsi
from components.metrics import render_risk_metrics
from components.ui_icons import icon_html
from haber_motoru import ai_teknik_analiz_yorumu



def _inject_premium_summary_style() -> None:
    """Analiz özetine premium terminal görünümü verir."""
    st.markdown(
        """
        <style>
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
        direction = "Model baz senaryosu pozitif eğilim gösteriyor"
    elif base_return < -5:
        direction = "Model baz senaryosu negatif eğilim gösteriyor"
    else:
        direction = "Model baz senaryosu yatay / sınırlı eğilim gösteriyor"

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


def _render_professional_summary(
    current_price: float,
    currency_rate: float,
    forecast_data: Mapping[str, Any],
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

    st.markdown(
        f"""
        <div class="fp-hero">
            <div class="fp-eyebrow">Fintech Pro Intelligence Layer</div>
            <div class="fp-title"><span class="fp-title-with-icon">{icon_html("insight_lens")}</span>Profesyonel Analiz Özeti</div>
            <div class="fp-subtitle">
                Model konsensüsü, backtest kalitesi, risk profili ve senaryo aralığı
                tek ekranda okunabilir bir karar paneline dönüştürüldü.
            </div>
            <div class="fp-pill-row">
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("scenario_path", "fp-icon-small")}</span>{horizon}</div>
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("consensus_mesh", "fp-icon-small")}</span>Model Güveni %{confidence:.1f}</div>
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("risk_shield", "fp-icon-small")}</span>Risk: {risk_level}</div>
                <div class="fp-pill"><span class="fp-pill-with-icon">{icon_html("signal_node", "fp-icon-small")}</span>{badge}</div>
            </div>
        </div>
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
                <div class="fp-card-delta-neutral">Canlı veri üzerinden hesaplandı</div>
            </div>
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
                <div class="{delta_class}">{nominal_return:+.2f}% model getirisi</div>
            </div>
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
            </div>
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
                Bu alan yatırım tavsiyesi değildir; yalnızca model çıktısını,
                risk görünümünü ve belirsizliği sadeleştirir.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
) -> None:
    """AI teknik analiz özetini güvenli şekilde gösterir."""
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

    st.info(f"**AI Sentezi:** {ai_summary}")


def render_analysis_panel(
    data: pd.DataFrame,
    asset_name: str,
    current_price: float,
    currency_rate: float,
    forecast_data: Mapping[str, Any],
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
        st.plotly_chart(
            price_figure,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "responsive": True,
            },
        )

    _render_ai_summary(
        asset_name=asset_name,
        current_price=current_price,
        bull_target=float(forecast_data["boga"]),
        bear_target=float(forecast_data["ayi"]),
    )
