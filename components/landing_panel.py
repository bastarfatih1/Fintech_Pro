"""
İlk karşılama / kazanç özeti paneli.

Bu panel analiz çalışınca kullanıcının ilk ekranda görmesi gereken iki soruyu
cevaplar:
1. Gelecekte ne kadar kazandırabilir?
2. Geçmişte ne kadar kazandırmış?
"""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import streamlit as st


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Sayısal değeri güvenli float'a çevirir."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default

    if pd.isna(numeric):
        return default

    return numeric


def _format_money(value: float, symbol: str = "") -> str:
    """Parayı Türkçe okunur biçimde gösterir."""
    formatted = f"{float(value):,.2f}"
    formatted = (
        formatted
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )

    if symbol:
        return f"{formatted} {symbol}"

    return formatted


def _format_percent(value: float) -> str:
    """Yüzdeyi Türkçe biçimde gösterir."""
    formatted = f"{float(value):+.2f}".replace(".", ",")
    return f"%{formatted}"


def _get_primary_future_row(forecast_data: Mapping[str, Any]) -> Mapping[str, Any]:
    """İlk ekranda gösterilecek ana gelecek senaryo satırını seçer."""
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


def _extract_future_table(
    forecast_data: Mapping[str, Any],
    currency_symbol: str,
) -> pd.DataFrame:
    """
    Gelecek senaryolarını okunur tabloya çevirir.

    Eski tabloda sadece "Sermaye Karşılığı" yazdığı için bunun hangi
    senaryoya ait olduğu belirsizdi. Bu tabloda artık üç ayrı sermaye
    karşılığı net gösterilir:
    - Kötümser Sermaye
    - Baz Sermaye
    - İyimser Sermaye
    """
    future_table = forecast_data.get("gelecek_df")

    if not isinstance(future_table, pd.DataFrame) or future_table.empty:
        return pd.DataFrame()

    renamed = pd.DataFrame()
    renamed["Vade"] = future_table.get("Vade", "")

    column_map = {
        "Kötümser Senaryo": "Kötümser Fiyat",
        "Baz Senaryo": "Baz Fiyat",
        "İyimser Senaryo": "İyimser Fiyat",
        "Kötümser Getiri %": "Kötümser Getiri",
        "Nominal Getiri %": "Baz Getiri",
        "İyimser Getiri %": "İyimser Getiri",
        "Kötümser Sermaye": "Kötümser Sermaye",
        "Sermaye Karşılığı": "Baz Sermaye",
        "İyimser Sermaye": "İyimser Sermaye",
    }

    for source_column, display_column in column_map.items():
        if source_column in future_table.columns:
            renamed[display_column] = future_table[source_column]

    money_columns = (
        "Kötümser Fiyat",
        "Baz Fiyat",
        "İyimser Fiyat",
        "Kötümser Sermaye",
        "Baz Sermaye",
        "İyimser Sermaye",
    )
    percent_columns = (
        "Kötümser Getiri",
        "Baz Getiri",
        "İyimser Getiri",
    )

    for column in money_columns:
        if column in renamed.columns:
            renamed[column] = renamed[column].apply(
                lambda value: _format_money(
                    _safe_float(value),
                    currency_symbol,
                )
            )

    for column in percent_columns:
        if column in renamed.columns:
            renamed[column] = renamed[column].apply(
                lambda value: _format_percent(_safe_float(value))
            )

    return renamed


def _build_past_return_table(
    data: pd.DataFrame,
    investment_amount: float,
    currency_rate: float,
    currency_symbol: str,
) -> pd.DataFrame:
    """Geçmiş getirileri sade tabloya dönüştürür."""
    if data is None or data.empty or "Close" not in data.columns:
        return pd.DataFrame()

    close_prices = pd.to_numeric(data["Close"], errors="coerce").dropna()

    if close_prices.empty:
        return pd.DataFrame()

    current_price = float(close_prices.iloc[-1])
    rows = []

    periods = [
        ("1 Hafta", 5),
        ("1 Ay", 21),
        ("3 Ay", 63),
        ("6 Ay", 126),
        ("1 Yıl", 252),
        ("3 Yıl", 756),
        ("5 Yıl", 1260),
    ]

    for label, days in periods:
        if len(close_prices) <= days:
            continue

        old_price = float(close_prices.iloc[-days])
        if old_price <= 0:
            continue

        return_percent = ((current_price - old_price) / old_price) * 100.0
        old_display = old_price * currency_rate
        current_display = current_price * currency_rate

        if investment_amount > 0:
            capital_now = investment_amount * (current_price / old_price)
            gain_amount = capital_now - investment_amount
            capital_text = _format_money(capital_now, currency_symbol)
            gain_text = _format_money(gain_amount, currency_symbol)
        else:
            capital_text = "Tutar girilmedi"
            gain_text = "Tutar girilmedi"

        rows.append(
            {
                "Dönem": label,
                "Başlangıç Fiyatı": _format_money(old_display, currency_symbol),
                "Bugünkü Fiyat": _format_money(current_display, currency_symbol),
                "Geçmiş Getiri": _format_percent(return_percent),
                "Bugünkü Sermaye": capital_text,
                "Geçmiş Kazanç/Kayıp": gain_text,
            }
        )

    return pd.DataFrame(rows)


def _inject_landing_style() -> None:
    """İlk ekran için premium ve mobil uyumlu stil."""
    st.markdown(
        """
        <style>
        .fp-landing-hero {
            border: 1px solid rgba(56, 189, 248, 0.34);
            border-radius: 24px;
            padding: 20px 22px;
            margin: 8px 0 18px 0;
            background:
                radial-gradient(circle at 8% 0%, rgba(56, 189, 248, 0.22), transparent 34%),
                radial-gradient(circle at 92% 8%, rgba(134, 239, 172, 0.14), transparent 30%),
                linear-gradient(135deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.94));
            box-shadow: 0 20px 52px rgba(2, 6, 23, 0.30);
        }
        .fp-landing-kicker {
            color: #93c5fd;
            font-size: 0.76rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .fp-landing-title {
            color: #f8fafc;
            font-size: clamp(1.55rem, 3vw, 2.28rem);
            font-weight: 950;
            letter-spacing: -0.04em;
            line-height: 1.08;
            margin-bottom: 8px;
        }
        .fp-landing-subtitle {
            color: #cbd5e1;
            font-size: 0.98rem;
            line-height: 1.62;
            max-width: 980px;
        }
        .fp-landing-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 13px;
            margin: 12px 0 18px 0;
        }
        .fp-landing-card {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 18px;
            padding: 15px 16px;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.060), rgba(255,255,255,0.025));
            box-shadow: 0 12px 28px rgba(2, 6, 23, 0.18);
            min-height: 126px;
        }
        .fp-landing-label {
            color: #94a3b8;
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .fp-landing-value {
            color: #f8fafc;
            font-size: clamp(1.18rem, 2vw, 1.52rem);
            font-weight: 950;
            line-height: 1.18;
            margin-bottom: 8px;
        }
        .fp-landing-note {
            color: #cbd5e1;
            font-size: 0.86rem;
            line-height: 1.46;
        }
        .fp-landing-positive {
            color: #86efac;
        }
        .fp-landing-negative {
            color: #fca5a5;
        }
        .fp-landing-neutral {
            color: #fde68a;
        }
        .fp-section-title {
            color: #f8fafc;
            font-size: 1.20rem;
            font-weight: 930;
            margin: 18px 0 8px 0;
        }
        .fp-mobile-note {
            color: #94a3b8;
            font-size: 0.84rem;
            line-height: 1.45;
            margin: 8px 0 14px 0;
        }
        @media (max-width: 860px) {
            .fp-landing-grid {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            .fp-landing-hero {
                padding: 18px 16px;
            }
            .fp-landing-card {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_landing_panel(
    data: pd.DataFrame,
    asset_name: str,
    current_price: float,
    investment_amount: float,
    currency_rate: float,
    currency_symbol: str,
    forecast_data: Mapping[str, Any],
) -> None:
    """İlk sekmede gelecek ve geçmiş kazanç özetini gösterir."""
    _inject_landing_style()

    current_display = current_price * currency_rate
    future_row = _get_primary_future_row(forecast_data)

    horizon = str(future_row.get("Vade", "Seçili vade"))
    base_target = _safe_float(
        future_row.get("Baz Senaryo", future_row.get("Tahmin")),
        default=current_display,
    )
    lower_target = _safe_float(
        future_row.get("Kötümser Senaryo"),
        default=base_target,
    )
    upper_target = _safe_float(
        future_row.get("İyimser Senaryo"),
        default=base_target,
    )
    expected_return = _safe_float(
        future_row.get("Nominal Getiri %"),
        default=(
            ((base_target - current_display) / current_display) * 100.0
            if current_display > 0
            else 0.0
        ),
    )

    if investment_amount > 0 and current_display > 0:
        projected_capital = investment_amount * (base_target / current_display)
        projected_gain = projected_capital - investment_amount
        capital_text = _format_money(projected_capital, currency_symbol)
        gain_text = _format_money(projected_gain, currency_symbol)
    else:
        capital_text = "Tutar girilmedi"
        gain_text = "Tutar girilmedi"

    tone = (
        "fp-landing-positive"
        if expected_return > 0
        else "fp-landing-negative"
        if expected_return < 0
        else "fp-landing-neutral"
    )

    st.markdown(
        f"""
        <div class="fp-landing-hero">
            <div class="fp-landing-kicker">İlk Bakış Kazanç Özeti</div>
            <div class="fp-landing-title">{asset_name} için gelecek ve geçmiş görünüm</div>
            <div class="fp-landing-subtitle">
                Bu ekran ilk bakışta iki şeyi gösterir: Seçili tutar ve vadeye göre
                gelecekte oluşabilecek baz senaryo değeri; geçmişte aynı varlığın farklı
                dönemlerde ne kadar getiri sağladığı.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="fp-landing-grid">
            <div class="fp-landing-card">
                <div class="fp-landing-label">Güncel Fiyat</div>
                <div class="fp-landing-value">{_format_money(current_display, currency_symbol)}</div>
                <div class="fp-landing-note">Seçili para birimiyle bugünkü fiyat.</div>
            </div>
            <div class="fp-landing-card">
                <div class="fp-landing-label">Gelecek Baz Senaryo · {horizon}</div>
                <div class="fp-landing-value {tone}">{_format_money(base_target, currency_symbol)}</div>
                <div class="fp-landing-note">Beklenen fark: {_format_percent(expected_return)}</div>
            </div>
            <div class="fp-landing-card">
                <div class="fp-landing-label">Baz Senaryoya Göre Sermaye</div>
                <div class="fp-landing-value">{capital_text}</div>
                <div class="fp-landing-note">Seçili yatırım tutarına göre baz senaryo kazanç/kayıp: {gain_text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="fp-landing-card">
            <div class="fp-landing-label">Senaryo Aralığı</div>
            <div class="fp-landing-value">
                {_format_money(lower_target, currency_symbol)} - {_format_money(upper_target, currency_symbol)}
            </div>
            <div class="fp-landing-note">
                Bu aralık kötümser ve iyimser senaryoyu gösterir. Tek bir kesin fiyat
                değil, model belirsizliğini anlatan olası aralıktır.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Gram Altın (TRY) gibi TRY bazlı varlıklarda fiyat tekrar USD/TRY ile "
        "çarpılmaz; seçilen para birimine tek doğru dönüşüm uygulanır."
    )

    future_table = _extract_future_table(forecast_data, currency_symbol)

    st.markdown("<div class='fp-section-title'>Gelecek senaryo özeti</div>", unsafe_allow_html=True)
    st.caption(
        "Fiyat sütunları varlığın beklenen fiyatını gösterir. Sermaye sütunları ise "
        "girdiğin yatırım tutarının o senaryoda yaklaşık kaç TL/para birimi olacağını gösterir."
    )
    if future_table.empty:
        st.info("Gelecek senaryo tablosu bulunamadı.")
    else:
        st.dataframe(future_table, hide_index=True, use_container_width=True)

    past_table = _build_past_return_table(
        data=data,
        investment_amount=investment_amount,
        currency_rate=currency_rate,
        currency_symbol=currency_symbol,
    )

    st.markdown("<div class='fp-section-title'>Geçmiş getiri özeti</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='fp-mobile-note'>Mobilde tabloyu sağa-sola kaydırarak tüm sütunları görebilirsin.</div>",
        unsafe_allow_html=True,
    )

    if past_table.empty:
        st.info("Geçmiş getiri hesaplamak için yeterli veri bulunamadı.")
    else:
        st.dataframe(past_table, hide_index=True, use_container_width=True)

    st.caption(
        "Bu ekran yatırım tavsiyesi vermez. Geçmiş performans geleceği garanti etmez; "
        "gelecek değerler model senaryosudur."
    )
