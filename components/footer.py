"""
Alt işlem menüsü bileşenleri.

Bu modül uygulamanın alt kısmındaki sabit işlem çubuğunu gösterir.
"""

import streamlit as st

from components.ui_icons import icon_html


def render_action_footer() -> None:
    """Alt sabit işlem menüsünü ekranda gösterir."""
    footer_html = f"""
<div class="floating-action-bar">
<button class="fp-action-btn">
    <span class="fp-action-content">{icon_html("refresh_cycle", "fp-icon-small")}Yenile</span>
</button>
<button class="fp-action-btn">
    <span class="fp-action-content">{icon_html("watchlist_star", "fp-icon-small")}İzleme Listesi</span>
</button>
<button class="fp-action-btn">
    <span class="fp-action-content">{icon_html("document_report", "fp-icon-small")}Rapor İndir</span>
</button>
<button class="fp-action-btn fp-action-btn-primary">
    <span class="fp-action-content">{icon_html("ai_core", "fp-icon-small")}AI Analiz Raporu</span>
</button>
</div>
"""

    st.markdown(
        footer_html,
        unsafe_allow_html=True,
    )
