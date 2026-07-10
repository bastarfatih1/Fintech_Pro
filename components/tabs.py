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


def create_main_tabs():
    """Ana analiz sekmelerini oluşturur ve döndürür."""
    return st.tabs(TAB_LABELS)
