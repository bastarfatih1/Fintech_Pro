from __future__ import annotations

import html
from typing import Any, Optional

import pandas as pd
import streamlit as st


def inject_premium_ui_theme() -> None:
    st.markdown(
        """
        <style>
        .fp-premium-table-wrap {
            width: 100%;
            overflow-x: auto;
            border-radius: 18px;
            border: 1px solid rgba(56, 189, 248, 0.24);
            background: linear-gradient(135deg, rgba(6, 14, 27, 0.98), rgba(13, 31, 54, 0.96));
            box-shadow: 0 18px 42px rgba(0,0,0,0.30);
            margin: 12px 0 20px 0;
            max-height: 540px;
        }

        table.fp-premium-table {
            width: 100%;
            border-collapse: collapse;
            color: #eaf6ff;
            font-size: 0.86rem;
            background: transparent;
        }

        table.fp-premium-table thead th {
            background: linear-gradient(135deg, rgba(11, 39, 70, 0.98), rgba(18, 28, 52, 0.98));
            color: #bfe9ff;
            font-weight: 850;
            text-align: left;
            padding: 12px 12px;
            border-bottom: 1px solid rgba(125, 211, 252, 0.28);
            white-space: nowrap;
        }

        table.fp-premium-table tbody td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            color: rgba(236, 246, 255, 0.92);
            white-space: nowrap;
        }

        table.fp-premium-table tbody tr:nth-child(even) {
            background: rgba(255,255,255,0.026);
        }

        table.fp-premium-table tbody tr:hover {
            background: rgba(56, 189, 248, 0.10);
        }

        .fp-premium-table-title {
            margin: 18px 0 4px 0;
            color: #f8fbff;
            font-size: 1.05rem;
            font-weight: 900;
        }

        .fp-premium-table-subtitle {
            margin: 0 0 8px 0;
            color: rgba(226, 232, 240, 0.72);
            font-size: 0.88rem;
            line-height: 1.45;
        }

        .fp-plain-guide {
            padding: 14px 16px;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(8, 25, 45, 0.96), rgba(16, 42, 70, 0.86));
            border: 1px solid rgba(56, 189, 248, 0.20);
            margin: 10px 0 16px 0;
            color: rgba(238, 248, 255, 0.90);
            line-height: 1.55;
        }

        .fp-plain-guide strong {
            color: #eaf7ff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _to_dataframe(value: Any) -> Optional[pd.DataFrame]:
    if value is None:
        return None

    if isinstance(value, pd.DataFrame):
        return value.copy()

    try:
        return pd.DataFrame(value)
    except Exception:
        return None


def render_premium_table(
    df: Any = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    max_rows: Optional[int] = None,
    **kwargs: Any,
) -> None:
    inject_premium_ui_theme()

    if df is None and "data" in kwargs:
        df = kwargs.get("data")

    table = _to_dataframe(df)

    if table is None or table.empty:
        st.info("Gösterilecek tablo verisi bulunamadı.")
        return

    if max_rows is not None:
        table = table.head(max_rows)

    table = table.copy().fillna("—")

    for col in table.columns:
        table[col] = table[col].map(
            lambda value: "—"
            if str(value).strip().lower() in {"none", "nan", "nat", ""}
            else value
        )

    if title:
        st.markdown(
            f'<div class="fp-premium-table-title">{html.escape(str(title))}</div>',
            unsafe_allow_html=True,
        )

    if subtitle:
        st.markdown(
            f'<div class="fp-premium-table-subtitle">{html.escape(str(subtitle))}</div>',
            unsafe_allow_html=True,
        )

    html_table = table.to_html(
        index=False,
        escape=True,
        border=0,
        classes="fp-premium-table",
    )

    st.markdown(
        f'<div class="fp-premium-table-wrap">{html_table}</div>',
        unsafe_allow_html=True,
    )


def render_plain_guide(title: str, text: str) -> None:
    inject_premium_ui_theme()

    st.markdown(
        f"""
        <div class="fp-plain-guide">
            <strong>{html.escape(str(title))}</strong><br>
            {html.escape(str(text))}
        </div>
        """,
        unsafe_allow_html=True,
    )
