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
    with st.container(border=True):
        st.markdown("##### Analiz süresi")
        st.caption(
            "Bu analiz; piyasa verisi, geçmiş fiyat davranışı, model konsensüsü, "
            "risk metrikleri ve AI haber sentezi gibi ağır matematiksel hesaplamalar içerir. "
            "Ortalama 1–3 dk sürebilir."
        )

    clicked = st.button(
        "Analizi Başlat",
        width="stretch",
        type="primary",
    )

    if clicked:
        st.session_state[ANALYSIS_STATE_KEY] = True

    return bool(st.session_state[ANALYSIS_STATE_KEY])


def reset_analysis_state() -> None:
    """Analiz durumunu başlangıç değerine döndürür."""
    st.session_state[ANALYSIS_STATE_KEY] = False
