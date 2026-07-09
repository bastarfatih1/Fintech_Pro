"""
Alt işlem menüsü bileşenleri.

Bu modül uygulamanın alt kısmındaki sabit işlem çubuğunu gösterir.
"""

import streamlit as st


def render_action_footer() -> None:
    """Alt sabit işlem menüsünü ekranda gösterir."""
    footer_html = """
<div class="floating-action-bar">
<button style="background:transparent; border:none; color:white; font-size:16px;">🔄 Yenile</button>
<button style="background:transparent; border:none; color:white; font-size:16px;">⭐ İzleme Listesi</button>
<button style="background:transparent; border:none; color:white; font-size:16px;">📤 Rapor İndir</button>
<button style="background:transparent; border:none; color:#00bbff; font-weight:bold; font-size:16px;">🤖 AI Analiz Raporu</button>
</div>
"""

    st.markdown(
        footer_html,
        unsafe_allow_html=True,
    )