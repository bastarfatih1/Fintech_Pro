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
from haber_motoru import ai_teknik_analiz_yorumu


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
    """Analiz sonucunu kısa ve kullanıcı dostu özet kartlarıyla gösterir."""
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

    st.markdown("#### 📌 Profesyonel Analiz Özeti")

    col_price, col_base, col_range = st.columns(3)

    col_price.metric(
        "Güncel Fiyat",
        f"{current_display:,.2f}",
    )
    col_base.metric(
        f"Baz Senaryo ({horizon})",
        f"{base_target:,.2f}",
        delta=f"{nominal_return:+.2f}%",
    )
    col_range.metric(
        "Senaryo Aralığı",
        f"{lower_target:,.2f} - {upper_target:,.2f}",
    )

    col_risk, col_confidence = st.columns(2)

    col_risk.metric(
        "Risk Seviyesi",
        risk_level,
    )
    col_confidence.metric(
        "Model Güveni",
        f"%{confidence:.1f}",
    )

    st.caption(
        "Genel durum: "
        + general_status
        + " Bu özet yatırım tavsiyesi değildir; yalnızca model çıktısını sadeleştirir."
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
        st.warning(f"⚠️ {rsi_result.message}")
    elif rsi_result.status == "oversold":
        st.success(f"✅ {rsi_result.message}")
    else:
        st.info(f"ℹ️ {rsi_result.message}")


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

    st.info(f"**🤖 AI Sentezi:** {ai_summary}")


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

    st.markdown(f"### 📡 {asset_name} - Merkezi Terminal")

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
