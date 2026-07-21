from __future__ import annotations

import traceback
from typing import Callable, Any

import streamlit as st


def render_soft_error_card(title: str, error: Exception | str) -> None:
    st.markdown(
        f"""
        <div style="
            padding: 18px 20px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(69, 26, 3, 0.88), rgba(30, 41, 59, 0.92));
            border: 1px solid rgba(251, 146, 60, 0.30);
            box-shadow: 0 14px 34px rgba(0,0,0,0.22);
            margin: 12px 0 18px 0;
        ">
            <div style="
                color: #fed7aa;
                font-weight: 900;
                font-size: 1.05rem;
                margin-bottom: 6px;
            ">{title} şu an üretilemedi</div>

            <div style="
                color: rgba(255, 237, 213, 0.88);
                font-size: 0.92rem;
                line-height: 1.5;
            ">
                Veri hattı yoğun, eksik veri var veya bu panel için gerekli hesaplama tamamlanamadı.
                Uygulamanın tamamı durdurulmadı; diğer sekmeleri kullanmaya devam edebilirsin.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Teknik hata detayı", expanded=False):
        st.code(str(error))
        st.code(traceback.format_exc())


def safe_render_panel(title: str, render_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    try:
        render_fn(*args, **kwargs)
    except Exception as exc:
        render_soft_error_card(title=title, error=exc)
