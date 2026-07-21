"""
Uygulama sekmeleri bileşeni.

Bu modül ana analiz ekranındaki sekmeleri oluşturur.
"""

from typing import Sequence

import streamlit as st


TAB_LABELS: Sequence[str] = (
    "Kazanç Özeti",
    "Grafikler & Modeller",
    "AI Haberler",
    "Geçmiş Detay",
)


def _inject_premium_tab_style() -> None:
    """Sekmeleri daha büyük, butonlu ve mobil uyumlu yapar."""
    st.markdown(
        """
        <style>
        div[data-testid="stTabs"] div[role="tablist"] {
            gap: 10px;
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.82), rgba(2, 6, 23, 0.76));
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 22px;
            padding: 9px;
            margin-bottom: 18px;
            box-shadow: 0 16px 36px rgba(2, 6, 23, 0.24);
            overflow-x: auto;
        }
        div[data-testid="stTabs"] button[role="tab"] {
            border-radius: 16px;
            padding: 14px 20px;
            min-height: 56px;
            color: #cbd5e1;
            font-size: 1.04rem;
            font-weight: 900;
            letter-spacing: -0.01em;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.052), rgba(255,255,255,0.020));
            white-space: nowrap;
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #f8fafc;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.28), transparent 35%),
                linear-gradient(135deg, rgba(14, 165, 233, 0.28), rgba(15, 23, 42, 0.86));
            border: 1px solid rgba(56, 189, 248, 0.50);
            box-shadow: 0 12px 30px rgba(14, 165, 233, 0.18);
        }
        div[data-testid="stTabs"] button[role="tab"] p {
            font-size: 1.04rem;
            font-weight: 900;
        }
        @media (max-width: 700px) {
            div[data-testid="stTabs"] div[role="tablist"] {
                gap: 8px;
                padding: 7px;
            }
            div[data-testid="stTabs"] button[role="tab"] {
                min-height: 48px;
                padding: 10px 13px;
            }
            div[data-testid="stTabs"] button[role="tab"] p {
                font-size: 0.92rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_main_tabs():
    """Ana analiz sekmelerini oluşturur ve döndürür."""
    _inject_premium_tab_style()
    return st.tabs(TAB_LABELS)
