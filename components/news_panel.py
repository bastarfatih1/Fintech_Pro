"""
Haber ve AI duyarlılık paneli.

Bu bileşen haber kartlarını, kaynak bilgilerini ve
AI etki analizini Streamlit arayüzünde gösterir.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Optional, Tuple

import streamlit as st

from haber_motoru import ai_etki_analizi


SENTIMENT_COLORS = {
    "POZİTİF": "#00ff88",
    "NEGATİF": "#ff4d4d",
    "NÖTR": "#a0a0a0",
}


def _escape_html(value: Any) -> str:
    """Basit HTML karakter kaçışı uygular."""
    text = str(value)

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _parse_ai_analysis(
    analysis_result: Any,
) -> Optional[Tuple[str, str, str, str]]:
    """
    AI analiz sonucunu dört alana ayırır.

    Beklenen biçim:
        YÖN | ETKİ | GÜVEN | ÖZET
    """
    if not isinstance(analysis_result, str):
        return None

    parts = [part.strip() for part in analysis_result.split("|", 3)]

    if len(parts) != 4:
        return None

    direction, impact, confidence, summary = parts

    if not all(parts):
        return None

    return direction, impact, confidence, summary


def _get_direction_color(direction: str) -> str:
    """Duyarlılık yönüne uygun renk döndürür."""
    upper_direction = direction.upper()

    for key, color in SENTIMENT_COLORS.items():
        if key in upper_direction:
            return color

    return SENTIMENT_COLORS["NÖTR"]


def _render_news_card(news_item: Mapping[str, Any]) -> None:
    """Tek bir haber kartını güvenli şekilde gösterir."""
    title = _escape_html(news_item.get("title", "Başlıksız Haber"))
    media = _escape_html(news_item.get("media", "Bilinmeyen Kaynak"))
    date = _escape_html(news_item.get("date", "Tarih Yok"))
    link = str(news_item.get("link", "#")).strip()

    if not link.startswith(("http://", "https://")):
        link = "#"

    safe_link = _escape_html(link)

    st.markdown(
        (
            "<div class='news-card'>"
            f"<h4><a href='{safe_link}' target='_blank' "
            "rel='noopener noreferrer' "
            "style='color:#00bbff; text-decoration:none;'>"
            f"{title}</a></h4>"
            "<p style='color:#a0a0a0; font-size:12px;'>"
            f"📰 Kaynak: {media} | 📅 Tarih: {date}"
            "</p></div>"
        ),
        unsafe_allow_html=True,
    )


def _render_ai_analysis(
    headline: str,
    asset_name: str,
) -> None:
    """Bir haber başlığı için AI etki analizini gösterir."""
    try:
        analysis_result = ai_etki_analizi(
            headline,
            asset_name,
        )
    except Exception as exc:
        st.warning(
            "AI haber analizi şu anda tamamlanamadı. "
            f"Detay: {exc}"
        )
        return

    parsed_result = _parse_ai_analysis(analysis_result)

    if parsed_result is None:
        st.markdown(
            f"🤖 **Analiz Sonucu:** {_escape_html(analysis_result)}"
        )
        return

    direction, impact, confidence, summary = parsed_result
    color = _get_direction_color(direction)

    st.markdown(
        (
            f"**Yön:** <span style='color:{color};'>"
            f"{_escape_html(direction)}</span> | "
            f"**Etki:** %{_escape_html(impact)} | "
            f"**AI Güven Skoru:** {_escape_html(confidence)}/100"
            f"<br>📝 *Özet:* {_escape_html(summary)}"
        ),
        unsafe_allow_html=True,
    )


def render_news_panel(
    news_items: Optional[Iterable[Mapping[str, Any]]],
    asset_name: str,
) -> None:
    """
    Haber sekmesinin tamamını oluşturur.

    Args:
        news_items: Haber sözlüklerinden oluşan liste.
        asset_name: Analiz edilen varlığın kullanıcıya gösterilen adı.
    """
    st.markdown(
        "### 📰 Gerçek Zamanlı AI Duyarlılık (Sentiment) Analizi"
    )

    if not news_items:
        st.info("Kritik haber akışı bulunamadı.")
        return

    for news_item in news_items:
        with st.container():
            _render_news_card(news_item)

            headline = str(
                news_item.get(
                    "title",
                    "Başlıksız Haber",
                )
            )

            _render_ai_analysis(
                headline=headline,
                asset_name=asset_name,
            )

            st.divider()
