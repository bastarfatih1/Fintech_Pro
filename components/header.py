"""
Uygulamanın üst bölümünü oluşturan bileşenler.

Bu modül canlı piyasa bandını ekrana getirir.
"""

import html

import streamlit as st

from config.constants import TICKER_TEXT


def render_market_ticker() -> None:
    """Canlı piyasa özet bandını ekranda gösterir."""
    safe_ticker_text = html.escape(TICKER_TEXT)

    st.markdown(
        f"""
        <div class="ticker-bar">
            <marquee scrollamount="5">
                {safe_ticker_text}
            </marquee>
        </div>
        """,
        unsafe_allow_html=True,
    )
