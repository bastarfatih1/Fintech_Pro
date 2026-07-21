"""
Uygulamanın üst bölümünü oluşturan bileşenler.

Bu modül canlı piyasa bandını ekrana getirir.
"""

from __future__ import annotations

import html
from typing import Mapping

import streamlit as st

from config.constants import TICKER_TEXT


# Not:
# ExchangeRate-API verisi USD bazlı gelir.
# Örnek:
#   USD = 1.0
#   TRY = 46.97
#   EUR = 0.875
# Bu şu demektir:
#   1 USD = 46.97 TRY
#   1 USD = 0.875 EUR
# Kullanıcı için daha anlaşılır olması adına bantta TRY karşılıkları gösterilir:
#   USD/TRY, EUR/TRY, CNY/TRY vb.

CURRENCY_LABELS = {
    "USD": "ABD Doları",
    "EUR": "Euro",
    "CNY": "Çin Yuanı",
    "RUB": "Rus Rublesi",
    "JPY": "Japon Yeni",
    "SAR": "Suudi Riyali",
    "KWD": "Kuveyt Dinarı",
}

REFERENCE_TRY_CROSSES = {
    "USD": 34.20,
    "EUR": 37.17,
    "CNY": 4.72,
    "RUB": 0.39,
    "JPY": 0.22,
    "SAR": 9.12,
    "KWD": 110.32,
}


def _safe_rate(currencies: Mapping[str, float], code: str, default: float) -> float:
    """Kur değerini güvenli float olarak okur."""
    try:
        return float(currencies.get(code, default))
    except (TypeError, ValueError):
        return default


def _format_try_cross(code: str, value: float) -> str:
    """TRY karşılığını okunur biçimde gösterir."""
    if code in {"RUB", "JPY"}:
        return f"{value:.4f}"
    if value >= 100:
        return f"{value:,.2f}"
    return f"{value:,.3f}"


def _build_try_cross_items(currencies: Mapping[str, float]) -> str:
    """
    USD bazlı kur sözlüğünü kullanıcı dostu TRY paritelerine çevirir.

    API mantığı:
        TRY = 46.97  -> 1 USD kaç TL?
        EUR = 0.875  -> 1 USD kaç Euro?

    Gösterim mantığı:
        USD/TRY = TRY
        EUR/TRY = TRY / EUR
        CNY/TRY = TRY / CNY
    """
    usd_try = _safe_rate(currencies, "TRY", 1.0)

    items = [
        "<span class='fp-market-ticker-item'>"
        "<span class='fp-market-ticker-code'>TRY</span>"
        "<span class='fp-market-ticker-name'>Türk Lirası</span>"
        "<span class='fp-market-rate-neutral'>Baz ₺1.000</span>"
        "</span>"
    ]

    for code, label in CURRENCY_LABELS.items():
        rate_vs_usd = _safe_rate(currencies, code, 1.0)

        if code == "USD":
            try_cross = usd_try
        elif rate_vs_usd > 0:
            try_cross = usd_try / rate_vs_usd
        else:
            try_cross = 0.0

        reference = REFERENCE_TRY_CROSSES.get(code, try_cross)
        is_up = try_cross >= reference
        tone_class = "fp-market-rate-up" if is_up else "fp-market-rate-down"
        arrow = "▲" if is_up else "▼"

        items.append(
            "<span class='fp-market-ticker-item'>"
            f"<span class='fp-market-ticker-code'>{html.escape(code)}/TRY</span>"
            f"<span class='fp-market-ticker-name'>{html.escape(label)}</span>"
            f"<span class='{tone_class}'>{arrow} ₺{html.escape(_format_try_cross(code, try_cross))}</span>"
            "</span>"
        )

    return "".join(items)




def render_app_intro() -> None:
    """Uygulama giriş başlığını premium şekilde gösterir."""
    st.markdown(
        """
        <style>
        .fp-app-intro {
            border: 1px solid rgba(56, 189, 248, 0.34);
            border-radius: 26px;
            padding: 24px 26px;
            margin: 4px 0 16px 0;
            background:
                radial-gradient(circle at 10% 0%, rgba(56, 189, 248, 0.24), transparent 34%),
                radial-gradient(circle at 90% 10%, rgba(134, 239, 172, 0.12), transparent 30%),
                linear-gradient(135deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.94));
            box-shadow: 0 22px 56px rgba(2, 6, 23, 0.34);
        }
        .fp-app-intro-kicker {
            color: #93c5fd;
            font-size: 0.78rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .fp-app-intro-title {
            color: #f8fafc;
            font-size: clamp(2.15rem, 4vw, 4.10rem);
            line-height: 1.00;
            font-weight: 980;
            letter-spacing: -0.055em;
            margin-bottom: 12px;
        }
        .fp-app-intro-subtitle {
            color: #dbeafe;
            font-size: clamp(1.02rem, 1.6vw, 1.26rem);
            line-height: 1.62;
            max-width: 980px;
            font-weight: 560;
        }
        .fp-app-intro-note {
            margin-top: 12px;
            color: #94a3b8;
            font-size: 0.90rem;
            line-height: 1.50;
        }
        .fp-app-intro-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
            margin-top: 16px;
        }
        .fp-app-intro-pill {
            border: 1px solid rgba(226, 232, 240, 0.16);
            border-radius: 999px;
            padding: 7px 11px;
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.54);
            font-size: 0.83rem;
            font-weight: 820;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="fp-app-intro">
            <div class="fp-app-intro-kicker">AI destekli finansal senaryo terminali</div>
            <div class="fp-app-intro-title">Fintech Pro</div>
            <div class="fp-app-intro-subtitle">
                Yatırımlarınızın geçmişte ne kadar getiri sağladığını ölçün;
                gelecekte oluşabilecek değer aralıklarını ekonometri, istatistik,
                matematiksel modelleme ve yapay zekâ destekli senaryo analiziyle hesaplayın.
            </div>
            <div class="fp-app-intro-note">
                Sonuçlar kesin fiyat tahmini veya yatırım tavsiyesi değildir.
                Uygulama, veriyi daha anlaşılır hale getiren analitik bir karar destek ekranıdır.
            </div>
            <div class="fp-app-intro-pill-row">
                <div class="fp-app-intro-pill">Geçmiş performans</div>
                <div class="fp-app-intro-pill">Risk metrikleri</div>
                <div class="fp-app-intro-pill">Model konsensüsü</div>
                <div class="fp-app-intro-pill">AI haber sentezi</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_market_ticker(currencies: Mapping[str, float] | None = None) -> None:
    """Canlı piyasa özet bandını ekranda gösterir."""
    if currencies:
        ticker_html = _build_try_cross_items(currencies)
    else:
        ticker_html = html.escape(TICKER_TEXT)

    st.markdown(
        """
        <style>
        .fp-market-ticker-shell {
            border: 1px solid rgba(56, 189, 248, 0.36);
            border-radius: 22px;
            padding: 12px 0;
            margin: 6px 0 16px 0;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.20), transparent 34%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.94));
            box-shadow: 0 18px 40px rgba(2, 6, 23, 0.30);
            overflow: hidden;
        }
        .fp-market-ticker-item {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            margin-right: 40px;
            color: #e2e8f0;
            font-size: 1.02rem;
            font-weight: 850;
            letter-spacing: -0.01em;
            white-space: nowrap;
        }
        .fp-market-ticker-code {
            color: #f8fafc;
            border: 1px solid rgba(226, 232, 240, 0.20);
            border-radius: 999px;
            padding: 5px 9px;
            background: rgba(15, 23, 42, 0.72);
            font-size: 0.84rem;
            font-weight: 950;
        }
        .fp-market-ticker-name {
            color: #cbd5e1;
            font-size: 0.92rem;
            font-weight: 760;
        }
        .fp-market-rate-up {
            color: #86efac;
            font-weight: 960;
            text-shadow: 0 0 18px rgba(134, 239, 172, 0.16);
        }
        .fp-market-rate-down {
            color: #fca5a5;
            font-weight: 960;
            text-shadow: 0 0 18px rgba(252, 165, 165, 0.16);
        }
        .fp-market-rate-neutral {
            color: #fde68a;
            font-weight: 960;
            text-shadow: 0 0 18px rgba(253, 230, 138, 0.16);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="fp-market-ticker-shell">
            <marquee scrollamount="5">
                {ticker_html}
            </marquee>
        </div>
        """,
        unsafe_allow_html=True,
    )
