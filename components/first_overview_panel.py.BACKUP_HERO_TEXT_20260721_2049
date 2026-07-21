from __future__ import annotations

from html import escape
from typing import Any, Mapping, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def _num(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        n = float(value)
        if pd.isna(n) or np.isinf(n):
            return default
        return n
    except Exception:
        return default


def _money(value: Any, symbol: str = "₺", decimals: Optional[int] = None) -> str:
    n = _num(value)

    if n is None:
        return "Veri yok"

    if decimals is None:
        decimals = 4 if abs(n) < 100 else 2

    s = f"{n:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} {symbol}"


def _pct(value: Any) -> str:
    n = _num(value)

    if n is None:
        return "Veri yok"

    sign = "+" if n > 0 else "-" if n < 0 else ""
    return f"{sign}%{abs(n):.2f}".replace(".", ",")


def _delta(value: Any) -> Optional[str]:
    n = _num(value)

    if n is None:
        return None

    return f"{n:+.2f}%"


def _to_df(value: Any) -> pd.DataFrame:
    try:
        if isinstance(value, pd.DataFrame):
            return value.copy()
        if isinstance(value, (list, tuple)):
            return pd.DataFrame(value)
        if isinstance(value, dict):
            return pd.DataFrame(value)
    except Exception:
        pass

    return pd.DataFrame()


def _future_table(forecast_data: Mapping[str, Any]) -> pd.DataFrame:
    if not isinstance(forecast_data, Mapping):
        return pd.DataFrame()

    keys = [
        "gelecek_df",
        "gelecek_tablo",
        "gelecek_tablo_df",
        "future_table",
        "future_scenarios",
        "senaryo_tablosu",
    ]

    for key in keys:
        df = _to_df(forecast_data.get(key))
        if not df.empty and "Vade" in df.columns:
            return df

    for value in forecast_data.values():
        df = _to_df(value)
        if not df.empty and "Vade" in df.columns:
            return df

    return pd.DataFrame()


def _pick_future_row(
    forecast_data: Mapping[str, Any],
    selected_horizon: Optional[str],
) -> dict[str, Any]:
    df = _future_table(forecast_data)

    if df.empty:
        return {}

    candidates = []

    if selected_horizon:
        candidates.append(str(selected_horizon).strip())

    candidates += ["1 Yıl", "6 Ay", "3 Ay", "1 Ay", "1 Hafta", "1 İşlem Günü"]

    normalized = df["Vade"].astype(str).str.strip().str.casefold()

    for label in candidates:
        match = df[normalized == label.strip().casefold()]
        if not match.empty:
            return match.iloc[0].to_dict()

    return df.iloc[-1].to_dict()


def _horizon_days(label: Optional[str], fallback: Optional[int] = None) -> int:
    if fallback and fallback > 0:
        return int(fallback)

    text = str(label or "").casefold()

    if "hafta" in text:
        return 5
    if "1 ay" in text:
        return 21
    if "3 ay" in text:
        return 63
    if "6 ay" in text:
        return 126
    if "1 yıl" in text or "1 yil" in text:
        return 252
    if "2 yıl" in text or "2 yil" in text:
        return 504

    return 252


def _close_series(data: pd.DataFrame) -> pd.Series:
    if data is None or data.empty or "Close" not in data.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(data["Close"], errors="coerce").dropna()


def _past_stats(
    data: pd.DataFrame,
    current_price: float,
    investment_amount: float,
    currency_rate: float,
    horizon: str,
    forecast_days: Optional[int],
) -> dict[str, Any]:
    close = _close_series(data)
    current_native = _num(current_price)
    invested = _num(investment_amount, 0.0) or 0.0
    rate = _num(currency_rate, 1.0) or 1.0
    days = _horizon_days(horizon, forecast_days)

    out = {
        "past_price": None,
        "historical_return": None,
        "same_position_past_value": None,
        "past_investment_today_value": None,
    }

    if current_native is None or current_native <= 0 or len(close) <= days:
        return out

    past_native = _num(close.iloc[-(days + 1)])

    if past_native is None or past_native <= 0:
        return out

    out["past_price"] = past_native * rate
    out["historical_return"] = ((current_native / past_native) - 1.0) * 100.0

    if invested > 0:
        out["same_position_past_value"] = invested * past_native / current_native
        out["past_investment_today_value"] = invested * current_native / past_native

    return out






def _history_rows(
    data: pd.DataFrame,
    current_price: float,
    investment_amount: float,
    currency_rate: float,
    currency_symbol: str,
) -> list[dict[str, Any]]:
    close = _close_series(data)
    current_native = _num(current_price)
    invested = _num(investment_amount, 0.0) or 0.0
    rate = _num(currency_rate, 1.0) or 1.0

    if current_native is None or current_native <= 0 or close.empty:
        return []

    current_display = current_native * rate
    rows: list[dict[str, Any]] = []

    for label, days in [
        ("1 Hafta", 5),
        ("1 Ay", 21),
        ("3 Ay", 63),
        ("6 Ay", 126),
        ("1 Yıl", 252),
        ("3 Yıl", 756),
        ("5 Yıl", 1260),
    ]:
        if len(close) <= days:
            continue

        old_native = _num(close.iloc[-(days + 1)])

        if old_native is None or old_native <= 0:
            continue

        old_display = old_native * rate
        ret = ((current_native / old_native) - 1.0) * 100.0

        today_capital = invested * current_native / old_native if invested > 0 else None
        gain_loss = today_capital - invested if today_capital is not None else None

        direction = "▲" if ret >= 0 else "▼"

        rows.append(
            {
                "Tür": "Geçmiş",
                "Vade": label,
                "Referans Fiyat": _money(old_display, currency_symbol),
                "Baz/Güncel": _money(current_display, currency_symbol),
                "Getiri": f"{direction} {_pct(ret)}",
                "Sermaye": _money(today_capital, currency_symbol, 2),
                "Ek Senaryo / Kazanç": _money(gain_loss, currency_symbol, 2),
            }
        )

    return rows

def _inject_style() -> None:
    """Genel Bakış metin kontrastını güçlendirir."""
    st.markdown(
        """
        <style>
        .block-container h1,
        .block-container h2,
        .block-container h3,
        .block-container h4 {
            color: #f8fafc !important;
            font-weight: 950 !important;
            letter-spacing: -0.02em !important;
        }

        .block-container p,
        .block-container span,
        .block-container div,
        .block-container label {
            color: rgba(226, 232, 240, 0.96);
        }

        [data-testid="stCaptionContainer"] {
            color: rgba(203, 213, 225, 0.98) !important;
            font-weight: 650 !important;
        }

        [data-testid="stMetricLabel"] {
            color: rgba(203, 213, 225, 0.98) !important;
            font-weight: 850 !important;
        }

        [data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 950 !important;
            letter-spacing: -0.03em !important;
        }

        [data-testid="stMetricDelta"] {
            font-weight: 950 !important;
        }

        .stAlert {
            border-radius: 16px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(56, 189, 248, 0.30) !important;
            background:
                radial-gradient(circle at 0% 0%, rgba(56,189,248,0.10), transparent 34%),
                rgba(15, 23, 42, 0.58) !important;
        }

        /* Premium tablo daha net okunur olsun */
        .fp-premium-table,
        .fp-table,
        table {
            font-size: 0.88rem !important;
        }

        th {
            color: #dbeafe !important;
            font-weight: 950 !important;
        }

        td {
            color: #f8fafc !important;
            font-weight: 750 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _future_rows(
    forecast_data: Mapping[str, Any],
    investment_amount: float,
    current_display_price: float,
    currency_symbol: str,
) -> list[dict[str, Any]]:
    """Gelecek senaryo satırlarını birleşik tablo formatına çevirir."""
    df = _future_table(forecast_data)

    if df.empty:
        return []

    invested = _num(investment_amount, 0.0) or 0.0
    rows: list[dict[str, Any]] = []

    for _, item in df.iterrows():
        horizon = str(item.get("Vade", "-"))

        bad_capital = _num(item.get("Kötümser Sermaye"))
        base_capital = _num(item.get("Sermaye Karşılığı"))
        good_capital = _num(item.get("İyimser Sermaye"))

        base_return = _num(item.get("Nominal Getiri %"))
        bad_return = _num(item.get("Kötümser Getiri %"))
        good_return = _num(item.get("İyimser Getiri %"))

        base_price = _num(item.get("Baz Senaryo", item.get("Tahmin")))

        if base_capital is None and base_return is not None:
            base_capital = invested * (1 + base_return / 100.0)

        if bad_capital is None and bad_return is not None:
            bad_capital = invested * (1 + bad_return / 100.0)

        if good_capital is None and good_return is not None:
            good_capital = invested * (1 + good_return / 100.0)

        gain_loss = base_capital - invested if base_capital is not None else None
        direction = "▲" if (base_return or 0) >= 0 else "▼"

        rows.append(
            {
                "Tür": "Gelecek",
                "Vade": horizon,
                "Referans Fiyat": _money(current_display_price, currency_symbol),
                "Baz/Güncel": _money(base_price, currency_symbol),
                "Getiri": f"{direction} {_pct(base_return)}",
                "Sermaye": _money(base_capital, currency_symbol, 2),
                "Ek Senaryo / Kazanç": (
                    f"Kötümser: {_money(bad_capital, currency_symbol, 2)} | "
                    f"İyimser: {_money(good_capital, currency_symbol, 2)}"
                ),
            }
        )

    return rows



def _render_premium_history_table(
    history_rows: list[dict[str, Any]],
    future_rows: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Geçmiş ve gelecek satırlarını farklı renk tonlarıyla tek premium tabloda gösterir."""
    from html import escape as html_escape
    import streamlit.components.v1 as components

    future_rows = future_rows or []
    rows = history_rows + future_rows

    if not rows:
        st.info("Geçmiş ve gelecek yatırım özeti için yeterli veri bulunamadı.")
        return

    wanted_columns = [
        "Tür",
        "Vade",
        "Referans Fiyat",
        "Baz/Güncel",
        "Getiri",
        "Sermaye",
        "Ek Senaryo / Kazanç",
    ]

    def cell(value) -> str:
        return html_escape(str(value if value is not None else "-"))

    body = ""

    for row in rows:
        row_type = str(row.get("Tür", "")).strip().casefold()
        row_class = "future-row" if "gelecek" in row_type else "history-row"

        gain_text = str(row.get("Getiri", ""))
        gain_class = "gain-pos" if "+" in gain_text or "▲" in gain_text else "gain-neg" if "-" in gain_text or "▼" in gain_text else "gain-flat"

        tds = []
        for col in wanted_columns:
            value = cell(row.get(col, "-"))

            if col == "Tür":
                badge_class = "future-badge" if row_class == "future-row" else "history-badge"
                value = f'<span class="{badge_class}">{value}</span>'

            if col == "Getiri":
                value = f'<span class="gain-badge {gain_class}">{value}</span>'

            if col == "Sermaye":
                value = f'<strong>{value}</strong>'

            tds.append(f"<td>{value}</td>")

        body += f'<tr class="{row_class}">' + "".join(tds) + "</tr>"

    head = "".join(f"<th>{cell(col)}</th>" for col in wanted_columns)

    height = min(max(220 + len(rows) * 48, 420), 900)

    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: #f8fafc;
        }}

        .table-card {{
            width: 100%;
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(56, 189, 248, 0.34);
            background:
                radial-gradient(circle at 0% 0%, rgba(56,189,248,0.14), transparent 36%),
                linear-gradient(180deg, rgba(8,20,48,0.98), rgba(2,6,23,0.98));
            box-shadow: 0 18px 55px rgba(0,0,0,0.32);
        }}

        .table-title {{
            padding: 17px 18px 5px 18px;
            color: #ffffff;
            font-size: 18px;
            font-weight: 950;
            letter-spacing: -0.02em;
        }}

        .table-subtitle {{
            padding: 0 18px 15px 18px;
            color: #cbd5e1;
            font-size: 13px;
            font-weight: 650;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }}

        th {{
            padding: 13px 12px;
            text-align: left;
            background: rgba(14, 165, 233, 0.16);
            color: #dbeafe;
            font-size: 12px;
            font-weight: 950;
            border-top: 1px solid rgba(148,163,184,0.18);
            border-bottom: 1px solid rgba(148,163,184,0.22);
        }}

        td {{
            padding: 13px 12px;
            color: #f8fafc;
            font-size: 13px;
            font-weight: 760;
            border-bottom: 1px solid rgba(148,163,184,0.12);
            vertical-align: middle;
            word-break: break-word;
        }}

        tr.history-row {{
            background: linear-gradient(90deg, rgba(37,99,235,0.22), rgba(15,23,42,0.66));
        }}

        tr.future-row {{
            background: linear-gradient(90deg, rgba(20,184,166,0.22), rgba(15,23,42,0.70));
        }}

        tr.history-row:hover {{
            background: linear-gradient(90deg, rgba(37,99,235,0.34), rgba(30,41,59,0.78));
        }}

        tr.future-row:hover {{
            background: linear-gradient(90deg, rgba(20,184,166,0.34), rgba(30,41,59,0.78));
        }}

        .history-badge,
        .future-badge,
        .gain-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 950;
            white-space: nowrap;
        }}

        .history-badge {{
            color: #bfdbfe;
            background: rgba(37,99,235,0.24);
            border: 1px solid rgba(96,165,250,0.48);
        }}

        .future-badge {{
            color: #99f6e4;
            background: rgba(20,184,166,0.24);
            border: 1px solid rgba(45,212,191,0.48);
        }}

        .gain-pos {{
            color: #86efac;
            background: rgba(34,197,94,0.18);
            border: 1px solid rgba(34,197,94,0.42);
        }}

        .gain-neg {{
            color: #fecdd3;
            background: rgba(244,63,94,0.18);
            border: 1px solid rgba(244,63,94,0.42);
        }}

        .gain-flat {{
            color: #fde68a;
            background: rgba(234,179,8,0.16);
            border: 1px solid rgba(234,179,8,0.34);
        }}
      </style>
    </head>
    <body>
      <div class="table-card">
        <div class="table-title">Geçmiş ve gelecek yatırım özeti</div>
        <div class="table-subtitle">
          Mavi tonlar geçmiş performansı, yeşil tonlar gelecek senaryoları gösterir.
        </div>
        <table>
          <thead>
            <tr>{head}</tr>
          </thead>
          <tbody>
            {body}
          </tbody>
        </table>
      </div>
    </body>
    </html>
    """

    components.html(html, height=height, scrolling=False)

def _extract_route(
    forecast_data: Mapping[str, Any],
    current_display: float,
    base_price: float,
    forecast_days: int,
) -> np.ndarray:
    if isinstance(forecast_data, Mapping):
        for key in ["konsensus_rota", "consensus_path", "forecast_path", "base_path"]:
            value = forecast_data.get(key)

            if value is None:
                continue

            try:
                arr = np.asarray(value, dtype=float).flatten()
                arr = arr[np.isfinite(arr)]

                if arr.size >= 2:
                    return arr[:forecast_days]
            except Exception:
                pass

    return np.linspace(current_display, base_price, forecast_days)


def _consensus_chart(
    data: pd.DataFrame,
    current_price: float,
    currency_rate: float,
    currency_symbol: str,
    forecast_data: Mapping[str, Any],
    forecast_days: Optional[int],
    bad_price: float,
    base_price: float,
    good_price: float,
) -> go.Figure | None:
    close = _close_series(data)

    if close.empty:
        return None

    rate = _num(currency_rate, 1.0) or 1.0
    current_display = (_num(current_price) or float(close.iloc[-1])) * rate

    history = close.iloc[-252:] * rate
    history_x = list(pd.to_datetime(history.index))
    history_y = list(history.astype(float).values)

    days = max(int(forecast_days or 63), 5)
    last_date = pd.Timestamp(history_x[-1])
    future_x = list(pd.bdate_range(last_date, periods=days + 1)[1:])

    base_route = _extract_route(
        forecast_data=forecast_data,
        current_display=current_display,
        base_price=base_price,
        forecast_days=days,
    )

    if len(base_route) < days:
        base_route = np.linspace(current_display, base_price, days)

    base_route = np.asarray(base_route[:days], dtype=float)

    bad_route = np.linspace(current_display, bad_price, days)
    good_route = np.linspace(current_display, good_price, days)

    all_x = history_x + future_x
    all_base = np.asarray(history_y + list(base_route), dtype=float)

    above = np.where(all_base >= current_display, all_base, np.nan)
    below = np.where(all_base < current_display, all_base, np.nan)
    baseline = np.full_like(all_base, current_display)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=all_x,
            y=baseline,
            mode="lines",
            line=dict(color="rgba(226,232,240,0.55)", width=1, dash="dash"),
            name=f"Güncel Fiyat ({_money(current_display, currency_symbol)})",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=all_x,
            y=below,
            mode="lines",
            line=dict(color="#ef4444", width=2.15),
            fill="tonexty",
            fillcolor="rgba(239,68,68,0.18)",
            name="Konsensüs < Güncel Fiyat",
            connectgaps=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=all_x,
            y=above,
            mode="lines",
            line=dict(color="#22c55e", width=2.15),
            fill="tonexty",
            fillcolor="rgba(34,197,94,0.18)",
            name="Konsensüs > Güncel Fiyat",
            connectgaps=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=bad_route,
            mode="lines",
            line=dict(color="rgba(251,113,133,.75)", width=1.4, dash="dot"),
            name="Kötümser Tahmin Bandı",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=good_route,
            mode="lines",
            line=dict(color="rgba(34,197,94,.75)", width=1.4, dash="dot"),
            fill="tonexty",
            fillcolor="rgba(59,130,246,.10)",
            name="İyimser Tahmin Bandı",
        )
    )

    final_x = future_x[-1]

    fig.add_trace(
        go.Scatter(
            x=[final_x],
            y=[bad_price],
            mode="markers+text",
            marker=dict(size=9, color="#fb7185"),
            text=["Kötümser"],
            textposition="middle left",
            name="Kötümser Son Nokta",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[final_x],
            y=[base_price],
            mode="markers+text",
            marker=dict(size=10, color="#60a5fa"),
            text=["Baz"],
            textposition="top center",
            name="Baz Son Nokta",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[final_x],
            y=[good_price],
            mode="markers+text",
            marker=dict(size=9, color="#22c55e"),
            text=["İyimser"],
            textposition="middle right",
            name="İyimser Son Nokta",
        )
    )

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=22, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,6,23,0.78)",
        font=dict(color="#cbd5e1"),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            y=1.08,
            x=0.5,
            xanchor="center",
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.12)",
            zeroline=False,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1A", step="month", stepmode="backward"),
                    dict(count=3, label="3A", step="month", stepmode="backward"),
                    dict(count=6, label="6A", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=2, label="2Y", step="year", stepmode="backward"),
                    dict(step="all", label="Tümü"),
                ],
                bgcolor="rgba(15,23,42,0.88)",
                activecolor="#2563eb",
                font=dict(color="#e2e8f0", size=11),
            ),
        ),
        yaxis=dict(
            side="right",
            showgrid=True,
            gridcolor="rgba(148,163,184,0.12)",
            zeroline=False,
        ),
    )

    return fig


def render_first_overview_panel(
    data: pd.DataFrame,
    asset_name: str,
    market_symbol: str,
    current_price: float,
    investment_amount: float,
    currency_rate: float,
    currency_symbol: str,
    forecast_data: Mapping[str, Any],
    selected_horizon: Optional[str] = None,
    forecast_days: Optional[int] = None,
    **_: Any,
) -> None:
    _inject_style()

    row = _pick_future_row(forecast_data, selected_horizon)
    horizon = str(row.get("Vade") or selected_horizon or "Seçili vade")

    rate = _num(currency_rate, 1.0) or 1.0
    current_display = (_num(current_price, 0.0) or 0.0) * rate
    invested = _num(investment_amount, 0.0) or 0.0

    base_price = _num(row.get("Baz Senaryo", row.get("Tahmin")), current_display) or current_display
    bad_price = _num(row.get("Kötümser Senaryo"), base_price) or base_price
    good_price = _num(row.get("İyimser Senaryo"), base_price) or base_price

    base_return = _num(
        row.get("Nominal Getiri %"),
        ((base_price / current_display) - 1.0) * 100.0 if current_display > 0 else 0.0,
    ) or 0.0

    bad_return = _num(
        row.get("Kötümser Getiri %"),
        ((bad_price / current_display) - 1.0) * 100.0 if current_display > 0 else 0.0,
    ) or 0.0

    good_return = _num(
        row.get("İyimser Getiri %"),
        ((good_price / current_display) - 1.0) * 100.0 if current_display > 0 else 0.0,
    ) or 0.0

    bad_capital = _num(row.get("Kötümser Sermaye"), invested * (1 + bad_return / 100.0))
    base_capital = _num(row.get("Sermaye Karşılığı"), invested * (1 + base_return / 100.0))
    good_capital = _num(row.get("İyimser Sermaye"), invested * (1 + good_return / 100.0))

    past = _past_stats(
        data=data,
        current_price=current_price,
        investment_amount=investment_amount,
        currency_rate=currency_rate,
        horizon=horizon,
        forecast_days=forecast_days,
    )

    st.markdown("## Genel Bakış")
    st.caption(f"{asset_name} • {market_symbol} • Seçili vade: {horizon}")

    top1, top2, top3, top4 = st.columns(4)

    with top1:
        st.metric("Yatırılan Sermaye", _money(invested, currency_symbol, 2))

    with top2:
        st.metric("Güncel Varlık Fiyatı", _money(current_display, currency_symbol))

    with top3:
        st.metric(f"{horizon} Önceki Fiyat", _money(past.get("past_price"), currency_symbol))

    with top4:
        st.metric("Geçmiş Getiri", _pct(past.get("historical_return")), _delta(past.get("historical_return")))

    st.info(
        f"Bugünkü {_money(invested, currency_symbol, 2)} değerindeki aynı pozisyon, "
        f"{horizon} önce yaklaşık {_money(past.get('same_position_past_value'), currency_symbol, 2)} değerindeydi. "
        f"O tarihte {_money(invested, currency_symbol, 2)} yatırılsaydı bugünkü yaklaşık değeri "
        f"{_money(past.get('past_investment_today_value'), currency_symbol, 2)} olurdu."
    )

    st.markdown(f"### {horizon} gelecek yatırım tahmini")

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric("Kötümser Senaryo", _money(bad_capital, currency_symbol, 2), _delta(bad_return))

    with s2:
        st.metric("Baz Konsensüs Tahmini", _money(base_capital, currency_symbol, 2), _delta(base_return))

    with s3:
        st.metric("İyimser Senaryo", _money(good_capital, currency_symbol, 2), _delta(good_return))

    with st.container(border=True):
        st.caption(
            "Hedef fiyatlar · "
            f"Kötümser: {_money(bad_price, currency_symbol)} · "
            f"Baz: {_money(base_price, currency_symbol)} · "
            f"İyimser: {_money(good_price, currency_symbol)}"
        )

    st.markdown("### Geçmiş ve gelecek yatırım tablosu")

    history_rows = _history_rows(
        data=data,
        current_price=current_price,
        investment_amount=investment_amount,
        currency_rate=currency_rate,
        currency_symbol=currency_symbol,
    )

    future_rows = _future_rows(
        forecast_data=forecast_data,
        investment_amount=investment_amount,
        current_display_price=current_display,
        currency_symbol=currency_symbol,
    )

    _render_premium_history_table(history_rows, future_rows)

    st.markdown("### Konsensüs Grafiği")
    st.caption("Mevcut grafik tipi korunmuştur; kötümser / baz / iyimser tahmin noktaları eklendi.")

    fig = _consensus_chart(
        data=data,
        current_price=current_price,
        currency_rate=currency_rate,
        currency_symbol=currency_symbol,
        forecast_data=forecast_data,
        forecast_days=forecast_days,
        bad_price=bad_price,
        base_price=base_price,
        good_price=good_price,
    )

    if fig is None:
        st.info("Konsensüs grafiği için yeterli veri bulunamadı.")
    else:
        st.plotly_chart(fig, use_container_width=True)
