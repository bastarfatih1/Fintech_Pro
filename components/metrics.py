"""
Risk metrikleri bileşenleri.

Bu modül hesaplanan risk değerlerini güvenli ve premium görünümlü
risk kartları halinde gösterir.
"""

from typing import Mapping

import streamlit as st


def _safe_float(value: float, default: float = 0.0) -> float:
    """Sayısal değeri güvenli şekilde float'a çevirir."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _risk_tone_from_drawdown(max_drawdown: float) -> tuple[str, str]:
    """Max Drawdown değerinden risk tonu üretir."""
    value = abs(max_drawdown)

    if value >= 0.35:
        return "Yüksek", "negative"
    if value >= 0.20:
        return "Orta", "neutral"
    return "Düşük", "positive"


def _risk_tone_from_var(var_value: float) -> tuple[str, str]:
    """VaR değerinden risk tonu üretir."""
    value = abs(var_value)

    if value >= 0.04:
        return "Yüksek", "negative"
    if value >= 0.02:
        return "Orta", "neutral"
    return "Düşük", "positive"


def _risk_tone_from_ratio(ratio_value: float) -> tuple[str, str]:
    """Sharpe / Sortino gibi oranlardan kalite tonu üretir."""
    if ratio_value >= 1.0:
        return "Güçlü", "positive"
    if ratio_value >= 0.0:
        return "Sınırlı", "neutral"
    return "Zayıf", "negative"


def _risk_tone_from_beta(beta_value: float) -> tuple[str, str]:
    """Beta değerinden piyasa duyarlılığı tonu üretir."""
    value = abs(beta_value)

    if value >= 1.4:
        return "Yüksek Duyarlılık", "negative"
    if value >= 0.8:
        return "Piyasa Uyumlu", "neutral"
    return "Düşük Duyarlılık", "positive"


def _inject_risk_card_style() -> None:
    """Risk kartları için güvenli premium stil ekler."""
    st.markdown(
        """
        <style>
        .fp-risk-card {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 16px;
            padding: 13px 13px;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.050), rgba(255,255,255,0.020));
            min-height: 126px;
            box-shadow: 0 10px 26px rgba(2, 6, 23, 0.16);
        }
        .fp-risk-label {
            color: #94a3b8;
            font-size: 0.74rem;
            font-weight: 780;
            margin-bottom: 7px;
        }
        .fp-risk-value {
            color: #f8fafc;
            font-size: 1.16rem;
            font-weight: 880;
            line-height: 1.1;
            margin-bottom: 9px;
        }
        .fp-risk-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 0.72rem;
            font-weight: 850;
            border: 1px solid rgba(226, 232, 240, 0.14);
            background: rgba(15, 23, 42, 0.48);
            margin-bottom: 8px;
        }
        .fp-risk-positive {
            color: #86efac;
        }
        .fp-risk-neutral {
            color: #fde68a;
        }
        .fp-risk-negative {
            color: #fca5a5;
        }
        .fp-risk-note {
            color: #94a3b8;
            font-size: 0.72rem;
            line-height: 1.35;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_single_risk_card(
    label: str,
    value: str,
    badge: str,
    tone: str,
    note: str,
) -> None:
    """Tek risk kartını kapalı HTML bloğu olarak gösterir."""
    st.markdown(
        f"""
        <div class="fp-risk-card">
            <div class="fp-risk-label">{label}</div>
            <div class="fp-risk-value">{value}</div>
            <div class="fp-risk-badge fp-risk-{tone}">{badge}</div>
            <div class="fp-risk-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_metrics(stats: Mapping[str, float]) -> None:
    """
    Temel risk metriklerini premium risk kartları halinde gösterir.

    Args:
        stats: VaR, Sharpe, Sortino, MaxDD ve Beta değerlerini
            içeren sözlük benzeri veri.
    """
    required_keys = {"MaxDD", "VaR", "Sharpe", "Sortino", "Beta"}
    missing_keys = required_keys.difference(stats.keys())

    if missing_keys:
        st.error(
            "Risk metrikleri eksik: "
            + ", ".join(sorted(missing_keys))
        )
        return

    max_drawdown = _safe_float(stats["MaxDD"])
    var_value = _safe_float(stats["VaR"])
    sharpe = _safe_float(stats["Sharpe"])
    sortino = _safe_float(stats["Sortino"])
    beta = _safe_float(stats["Beta"])

    drawdown_badge, drawdown_tone = _risk_tone_from_drawdown(max_drawdown)
    var_badge, var_tone = _risk_tone_from_var(var_value)
    sharpe_badge, sharpe_tone = _risk_tone_from_ratio(sharpe)
    sortino_badge, sortino_tone = _risk_tone_from_ratio(sortino)
    beta_badge, beta_tone = _risk_tone_from_beta(beta)

    _inject_risk_card_style()

    left, right = st.columns([0.45, 0.55])

    with left:
        st.markdown("#### Risk Pulse")
        st.markdown("### Risk / Getiri Şeridi")

    with right:
        st.caption(
            "Bu metrikler tarihsel veri üzerinden hesaplanan bilgilendirici "
            "göstergelerdir. Gelecekteki sonucu garanti etmez ve yatırım "
            "tavsiyesi niteliği taşımaz."
        )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        _render_single_risk_card(
            label="Max Drawdown",
            value=f"%{max_drawdown * 100:.2f}",
            badge=drawdown_badge,
            tone=drawdown_tone,
            note="Zirveden görülen en büyük tarihsel düşüş.",
        )

    with col2:
        _render_single_risk_card(
            label="95% VaR",
            value=f"%{var_value * 100:.2f}",
            badge=var_badge,
            tone=var_tone,
            note="Normal koşullarda günlük kayıp eşiği.",
        )

    with col3:
        _render_single_risk_card(
            label="Sharpe",
            value=f"{sharpe:.2f}",
            badge=sharpe_badge,
            tone=sharpe_tone,
            note="Toplam riske karşı getiri verimliliği.",
        )

    with col4:
        _render_single_risk_card(
            label="Sortino",
            value=f"{sortino:.2f}",
            badge=sortino_badge,
            tone=sortino_tone,
            note="Aşağı yönlü riske göre getiri verimliliği.",
        )

    with col5:
        _render_single_risk_card(
            label="Beta",
            value=f"{beta:.2f}",
            badge=beta_badge,
            tone=beta_tone,
            note="Piyasa hareketlerine duyarlılık göstergesi.",
        )
