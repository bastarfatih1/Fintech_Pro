"""
Streamlit oturum yönetimi.

Bu modül analiz durumunu başlatır ve
analiz butonunun davranışını yönetir.
"""

import streamlit as st


ANALYSIS_STATE_KEY = "analiz_tamam"


def initialize_analysis_state() -> None:
    """Analiz oturum anahtarını güvenli şekilde başlatır."""
    if ANALYSIS_STATE_KEY not in st.session_state:
        st.session_state[ANALYSIS_STATE_KEY] = False


def render_analysis_button() -> bool:
    """
    Analiz başlatma butonunu gösterir.

    Returns:
        Analiz aktifse True döndürür.
    """
    clicked = st.button(
        "🚀 Kurumsal Gelişmiş AI Projeksiyonunu Başlat",
        use_container_width=True,
        type="primary",
    )

    if clicked:
        st.session_state[ANALYSIS_STATE_KEY] = True

    return bool(st.session_state[ANALYSIS_STATE_KEY])


def reset_analysis_state() -> None:
    """Analiz durumunu başlangıç değerine döndürür."""
    st.session_state[ANALYSIS_STATE_KEY] = False
