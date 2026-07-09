"""
Uygulamanın başlangıç ayarları.

Bu modül Streamlit sayfa yapılandırmasını ve genel CSS dosyasını yükler.
"""

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STYLE_FILE = PROJECT_ROOT / "assets" / "css" / "style.css"


def configure_page() -> None:
    """Streamlit sayfasının temel ayarlarını uygular."""
    st.set_page_config(
        page_title="Fintech Alpha Pro | Kurumsal Risk Terminali",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def load_global_styles() -> None:
    """Global CSS dosyasını okuyup uygulamaya yükler."""
    if not STYLE_FILE.exists():
        raise FileNotFoundError(
            f"CSS dosyası bulunamadı: {STYLE_FILE}"
        )

    css_content = STYLE_FILE.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{css_content}</style>",
        unsafe_allow_html=True,
    )


def initialize_application() -> None:
    """Uygulamanın başlangıç işlemlerini sırasıyla çalıştırır."""
    configure_page()
    load_global_styles()