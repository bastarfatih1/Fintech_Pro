"""
Custom inline SVG icon system.

Bu modül uygulamadaki emoji tabanlı görsel dili azaltmak için
ürüne özel, kurumsal ve premium inline SVG ikonları sağlar.

Kullanım:
    from components.ui_icons import icon_html

    st.markdown(
        f"<div>{icon_html('market_pulse')} Market Pulse</div>",
        unsafe_allow_html=True,
    )
"""

from __future__ import annotations

import html
from typing import Final


_BASE_ATTRS: Final[str] = (
    "viewBox='0 0 24 24' fill='none' "
    "xmlns='http://www.w3.org/2000/svg' aria-hidden='true'"
)

ICONS: Final[dict[str, str]] = {
    "market_pulse": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M3 13.5H7.2L9.1 8.5L12.2 17L15 6L17.1 13.5H21' "
        "stroke='currentColor' stroke-width='1.8' stroke-linecap='round' "
        "stroke-linejoin='round'/>"
        "<path d='M4 19H20' stroke='currentColor' stroke-width='1.2' "
        "stroke-linecap='round' opacity='.45'/>"
        "</svg>"
    ),
    "signal_node": (
        f"<svg {_BASE_ATTRS}>"
        "<circle cx='6' cy='12' r='2.4' stroke='currentColor' stroke-width='1.7'/>"
        "<circle cx='18' cy='6' r='2.4' stroke='currentColor' stroke-width='1.7'/>"
        "<circle cx='18' cy='18' r='2.4' stroke='currentColor' stroke-width='1.7'/>"
        "<path d='M8.2 11L15.8 7.1M8.2 13L15.8 16.9' "
        "stroke='currentColor' stroke-width='1.6' stroke-linecap='round'/>"
        "</svg>"
    ),
    "risk_shield": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M12 3.2L19 6V11.4C19 15.8 16.2 19.6 12 21"
        "C7.8 19.6 5 15.8 5 11.4V6L12 3.2Z' "
        "stroke='currentColor' stroke-width='1.7' stroke-linejoin='round'/>"
        "<path d='M8.4 12.3H10.6L11.6 9.7L13.5 14.7L14.7 12.3H15.8' "
        "stroke='currentColor' stroke-width='1.5' stroke-linecap='round' "
        "stroke-linejoin='round'/>"
        "</svg>"
    ),
    "scenario_path": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M4 12H9C12 12 12 6 15 6H20' stroke='currentColor' "
        "stroke-width='1.7' stroke-linecap='round'/>"
        "<path d='M9 12C12 12 12 18 15 18H20' stroke='currentColor' "
        "stroke-width='1.7' stroke-linecap='round'/>"
        "<circle cx='4' cy='12' r='1.8' fill='currentColor'/>"
        "<circle cx='20' cy='6' r='1.8' fill='currentColor' opacity='.75'/>"
        "<circle cx='20' cy='18' r='1.8' fill='currentColor' opacity='.75'/>"
        "</svg>"
    ),
    "capital_stack": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M5 8.5C5 6.6 8.1 5 12 5C15.9 5 19 6.6 19 8.5"
        "C19 10.4 15.9 12 12 12C8.1 12 5 10.4 5 8.5Z' "
        "stroke='currentColor' stroke-width='1.6'/>"
        "<path d='M5 8.5V12.5C5 14.4 8.1 16 12 16C15.9 16 19 14.4 19 12.5V8.5' "
        "stroke='currentColor' stroke-width='1.6'/>"
        "<path d='M5 12.5V15.5C5 17.4 8.1 19 12 19C15.9 19 19 17.4 19 15.5V12.5' "
        "stroke='currentColor' stroke-width='1.6'/>"
        "</svg>"
    ),
    "insight_lens": (
        f"<svg {_BASE_ATTRS}>"
        "<circle cx='10.5' cy='10.5' r='5.5' stroke='currentColor' stroke-width='1.8'/>"
        "<path d='M15 15L20 20' stroke='currentColor' stroke-width='1.8' "
        "stroke-linecap='round'/>"
        "<path d='M8.2 10.7H9.7L10.5 8.7L12 12.4L12.8 10.7H13.6' "
        "stroke='currentColor' stroke-width='1.4' stroke-linecap='round' "
        "stroke-linejoin='round'/>"
        "</svg>"
    ),
    "news_radar": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M5 5.5H14.5C17 5.5 19 7.5 19 10V18.5H7.5C6.1 18.5 5 17.4 5 16V5.5Z' "
        "stroke='currentColor' stroke-width='1.7' stroke-linejoin='round'/>"
        "<path d='M8 9H15M8 12H16M8 15H12' stroke='currentColor' "
        "stroke-width='1.45' stroke-linecap='round'/>"
        "<path d='M17.5 4C19.2 4.5 20.5 5.8 21 7.5' stroke='currentColor' "
        "stroke-width='1.4' stroke-linecap='round' opacity='.7'/>"
        "</svg>"
    ),
    "performance_curve": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M4 18H20' stroke='currentColor' stroke-width='1.4' "
        "stroke-linecap='round' opacity='.45'/>"
        "<path d='M5 16C8 15.5 9 11 11.8 11.5C14.5 12 15.2 7 19 6' "
        "stroke='currentColor' stroke-width='1.9' stroke-linecap='round' "
        "stroke-linejoin='round'/>"
        "<path d='M16.2 5.2L19 6L17.7 8.6' stroke='currentColor' "
        "stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'/>"
        "</svg>"
    ),
    "consensus_mesh": (
        f"<svg {_BASE_ATTRS}>"
        "<circle cx='12' cy='5' r='2' stroke='currentColor' stroke-width='1.6'/>"
        "<circle cx='6' cy='16' r='2' stroke='currentColor' stroke-width='1.6'/>"
        "<circle cx='18' cy='16' r='2' stroke='currentColor' stroke-width='1.6'/>"
        "<circle cx='12' cy='13' r='2.4' stroke='currentColor' stroke-width='1.7'/>"
        "<path d='M12 7V10.5M8 15L9.8 14M16 15L14.2 14M8 16H16' "
        "stroke='currentColor' stroke-width='1.4' stroke-linecap='round'/>"
        "</svg>"
    ),
    "document_report": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M7 3.8H14L18 7.8V20.2H7V3.8Z' stroke='currentColor' "
        "stroke-width='1.7' stroke-linejoin='round'/>"
        "<path d='M14 4V8H18' stroke='currentColor' stroke-width='1.5' "
        "stroke-linejoin='round'/>"
        "<path d='M9.5 12H15.5M9.5 15H15.5M9.5 18H13' "
        "stroke='currentColor' stroke-width='1.4' stroke-linecap='round'/>"
        "</svg>"
    ),
    "refresh_cycle": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M18.5 9.2C17.5 6.8 15.1 5.2 12.4 5.2C9.3 5.2 6.7 7.3 6 10.1' "
        "stroke='currentColor' stroke-width='1.7' stroke-linecap='round'/>"
        "<path d='M16.3 9.4H18.8V6.9' stroke='currentColor' stroke-width='1.7' "
        "stroke-linecap='round' stroke-linejoin='round'/>"
        "<path d='M5.5 14.8C6.5 17.2 8.9 18.8 11.6 18.8C14.7 18.8 17.3 16.7 18 13.9' "
        "stroke='currentColor' stroke-width='1.7' stroke-linecap='round'/>"
        "<path d='M7.7 14.6H5.2V17.1' stroke='currentColor' stroke-width='1.7' "
        "stroke-linecap='round' stroke-linejoin='round'/>"
        "</svg>"
    ),
    "watchlist_star": (
        f"<svg {_BASE_ATTRS}>"
        "<path d='M12 4.2L14.3 8.9L19.5 9.6L15.8 13.2L16.7 18.4"
        "L12 15.9L7.3 18.4L8.2 13.2L4.5 9.6L9.7 8.9L12 4.2Z' "
        "stroke='currentColor' stroke-width='1.7' stroke-linejoin='round'/>"
        "</svg>"
    ),
    "ai_core": (
        f"<svg {_BASE_ATTRS}>"
        "<rect x='6' y='6' width='12' height='12' rx='3' stroke='currentColor' "
        "stroke-width='1.7'/>"
        "<path d='M9.5 9.5H14.5V14.5H9.5V9.5Z' stroke='currentColor' "
        "stroke-width='1.35'/>"
        "<path d='M9 3.8V6M12 3.8V6M15 3.8V6M9 18V20.2M12 18V20.2M15 18V20.2"
        "M3.8 9H6M3.8 12H6M3.8 15H6M18 9H20.2M18 12H20.2M18 15H20.2' "
        "stroke='currentColor' stroke-width='1.35' stroke-linecap='round'/>"
        "</svg>"
    ),
}


def icon_svg(name: str) -> str:
    """İkonun ham SVG metnini döndürür."""
    return ICONS.get(name, ICONS["insight_lens"])


def icon_html(name: str, class_name: str = "fp-icon", label: str = "") -> str:
    """CSS sınıfıyla sarılmış güvenli ikon HTML'i döndürür."""
    safe_class = html.escape(class_name, quote=True)
    safe_label = html.escape(label, quote=True)

    aria_label = f" aria-label='{safe_label}'" if safe_label else ""

    return (
        f"<span class='{safe_class}'{aria_label}>"
        f"{icon_svg(name)}"
        "</span>"
    )
