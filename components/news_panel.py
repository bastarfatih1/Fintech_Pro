"""
Haber ve AI duyarlılık paneli.

Bu bileşen haber kartlarını, kaynak bilgilerini ve
AI etki analizini Streamlit arayüzünde gösterir.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Optional, Tuple

import streamlit as st

from haber_motoru import ai_haberleri_toplu_analiz_et
from components.ui_icons import icon_html


def _inject_news_premium_style() -> None:
    """Haber paneli için premium görünüm stillerini ekler."""
    st.markdown(
        """
        <style>
        .fp-news-hero {
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 20px;
            padding: 20px 22px;
            margin: 8px 0 18px 0;
            background:
                radial-gradient(circle at top left, rgba(34, 197, 94, 0.18), transparent 34%),
                radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.16), transparent 30%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.90));
            box-shadow: 0 16px 40px rgba(2, 6, 23, 0.22);
        }
        .fp-news-eyebrow {
            color: #86efac;
            font-size: 0.76rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 7px;
        }
        .fp-news-title {
            color: #f8fafc;
            font-size: 1.36rem;
            font-weight: 850;
            margin-bottom: 6px;
        }
        .fp-news-subtitle {
            color: #cbd5e1;
            font-size: 0.94rem;
            line-height: 1.55;
            max-width: 900px;
        }
        .fp-news-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }
        .fp-news-pill {
            border: 1px solid rgba(226, 232, 240, 0.16);
            border-radius: 999px;
            padding: 6px 10px;
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.45);
            font-size: 0.78rem;
        }
        .news-card {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 16px;
            padding: 14px 16px;
            margin: 10px 0 8px 0;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.050), rgba(255,255,255,0.020));
        }
        .fp-ai-note {
            border-left: 4px solid rgba(56, 189, 248, 0.90);
            border-radius: 14px;
            padding: 10px 12px;
            background: rgba(14, 165, 233, 0.08);
            margin: 8px 0 14px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_news_hero(
    news_items: Optional[Iterable[Mapping[str, Any]]],
    asset_name: str,
) -> None:
    """Haber paneli için premium giriş alanı gösterir."""
    items = list(news_items or [])
    news_count = len(items)

    _inject_news_premium_style()

    st.markdown(
        f"""
        <div class="fp-news-hero">
            <div class="fp-news-eyebrow">Market Narrative Radar</div>
            <div class="fp-news-title"><span class="fp-title-with-icon">{icon_html("news_radar")}</span>Haber Akışı & AI Duyarlılık Radarı</div>
            <div class="fp-news-subtitle">
                {asset_name} için haber başlıkları taranır, AI etki analiziyle
                pozitif / negatif / nötr sinyaller kısa ve okunabilir biçimde sunulur.
            </div>
            <div class="fp-news-pill-row">
                <div class="fp-news-pill"><span class="fp-pill-with-icon">{icon_html("news_radar", "fp-icon-small")}</span>Haber sayısı: {news_count}</div>
                <div class="fp-news-pill"><span class="fp-pill-with-icon">{icon_html("ai_core", "fp-icon-small")}</span>AI etki analizi</div>
                <div class="fp-news-pill"><span class="fp-pill-with-icon">{icon_html("signal_node", "fp-icon-small")}</span>Hızlı duyarlılık okuması</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return items



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
            f"Kaynak: {media} | Tarih: {date}"
            "</p></div>"
        ),
        unsafe_allow_html=True,
    )


def _render_ai_analysis_result(
    analysis_item: Optional[Mapping[str, Any]],
) -> None:
    """Toplu AI analizinden gelen tek haber sonucunu gösterir."""
    if not analysis_item:
        st.markdown(
            "**AI Analiz Sonucu:** Haber için ek AI yorumu üretilemedi."
        )
        return

    direction = str(analysis_item.get("direction", "NÖTR"))
    impact = str(analysis_item.get("impact", 0))
    confidence = str(analysis_item.get("confidence", 50))
    summary = str(
        analysis_item.get(
            "summary",
            "Haber etkisi nötr kabul edildi.",
        )
    )
    color = _get_direction_color(direction)

    st.markdown(
        (
            "<div class='fp-ai-note'>"
            f"**Yön:** <span style='color:{color};'>"
            f"{_escape_html(direction)}</span> | "
            f"**Etki:** %{_escape_html(impact)} | "
            f"**AI Güven Skoru:** {_escape_html(confidence)}/100"
            f"<br>*Özet:* {_escape_html(summary)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_news_panel(
    news_items: Optional[Iterable[Mapping[str, Any]]],
    asset_name: str,
    ai_bundle: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Haber sekmesinin tamamını oluşturur.

    Args:
        news_items: Haber sözlüklerinden oluşan liste.
        asset_name: Analiz edilen varlığın kullanıcıya gösterilen adı.
    """
    news_items = _render_news_hero(
        news_items=news_items,
        asset_name=asset_name,
    )

    if not news_items:
        st.info("Kritik haber akışı bulunamadı.")
        return

    if ai_bundle is None:
        ai_bundle = ai_haberleri_toplu_analiz_et(
            varlik=asset_name,
            haberler=news_items,
        )

    ai_results = ai_bundle.get("news_analysis", [])

    if ai_bundle.get("market_synthesis"):
        st.info(f"**Piyasa Sentezi:** {ai_bundle.get('market_synthesis')}")

    if ai_bundle.get("news_effect_summary"):
        st.caption(
            f"Haber etkisi: {ai_bundle.get('overall_news_effect', 'NÖTR')} · "
            f"{ai_bundle.get('news_effect_summary')}"
        )

    for index, news_item in enumerate(news_items):
        with st.container():
            _render_news_card(news_item)

            analysis_item = (
                ai_results[index]
                if index < len(ai_results)
                and isinstance(ai_results[index], Mapping)
                else None
            )

            _render_ai_analysis_result(analysis_item)

            st.divider()
