"""
Uygulama sekmeleri bileşeni.

Bu modül ana analiz ekranındaki sekmeleri oluşturur.
"""

from typing import Sequence

import streamlit as st


TAB_LABELS: Sequence[str] = (
    "Genel Görünüm",
    "Senaryo Analizi",
    "Piyasa Haberleri",
    "Geçmiş Performans",
)


def _inject_premium_tab_style() -> None:
    """Sekmeleri daha büyük ve premium görünümlü yapar."""
    st.markdown(
        """
        <style>
        div[data-testid="stTabs"] div[role="tablist"] {
            gap: 10px;
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.78), rgba(2, 6, 23, 0.72));
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 20px;
            padding: 8px;
            margin-bottom: 18px;
            box-shadow: 0 14px 32px rgba(2, 6, 23, 0.20);
        }
        div[data-testid="stTabs"] button[role="tab"] {
            border-radius: 15px;
            padding: 13px 18px;
            min-height: 52px;
            color: #cbd5e1;
            font-size: 1.02rem;
            font-weight: 880;
            letter-spacing: -0.01em;
            border: 1px solid rgba(148, 163, 184, 0.14);
            background: rgba(15, 23, 42, 0.42);
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #f8fafc;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.24), transparent 35%),
                linear-gradient(135deg, rgba(14, 165, 233, 0.22), rgba(15, 23, 42, 0.82));
            border: 1px solid rgba(56, 189, 248, 0.42);
            box-shadow: 0 10px 28px rgba(14, 165, 233, 0.16);
        }
        div[data-testid="stTabs"] button[role="tab"] p {
            font-size: 1.02rem;
            font-weight: 880;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_main_tabs():
    """Ana analiz sekmelerini oluşturur ve döndürür."""
    _inject_premium_tab_style()
    return st.tabs(TAB_LABELS)
