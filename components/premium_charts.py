from __future__ import annotations

from typing import Any

import streamlit as st


PREMIUM_PALETTE = [
    "#38bdf8",
    "#22c55e",
    "#f97316",
    "#a78bfa",
    "#f43f5e",
    "#eab308",
    "#14b8a6",
    "#94a3b8",
]


def inject_premium_chart_css() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stPlotlyChart"] {
            border-radius: 22px;
            border: 1px solid rgba(56, 189, 248, 0.18);
            background: linear-gradient(135deg, rgba(6, 14, 27, 0.96), rgba(13, 31, 54, 0.92));
            box-shadow: 0 18px 42px rgba(0,0,0,0.26);
            padding: 10px;
            margin: 8px 0 18px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _trace_name(trace: Any) -> str:
    try:
        return str(trace.name or "")
    except Exception:
        return ""


def _trace_type(trace: Any) -> str:
    try:
        return str(trace.type or "").lower()
    except Exception:
        return ""


def _is_candlestick(trace: Any) -> bool:
    return _trace_type(trace) == "candlestick"


def _is_bar(trace: Any) -> bool:
    return _trace_type(trace) == "bar"


def _is_line_like(trace: Any) -> bool:
    try:
        trace_type = _trace_type(trace)
        mode = str(getattr(trace, "mode", "") or "").lower()
        return trace_type == "scatter" and ("lines" in mode or mode == "")
    except Exception:
        return False


def _pick_trace_color(name: str, index: int) -> str:
    lower = name.lower()

    if any(key in lower for key in ["konsensüs", "consensus", "baz", "base"]):
        return "#38bdf8"

    if any(key in lower for key in ["iyimser", "optimistic", "upper", "yukarı"]):
        return "#22c55e"

    if any(key in lower for key in ["kötümser", "pessimistic", "lower", "aşağı"]):
        return "#f97316"

    if any(key in lower for key in ["geçmiş", "historical", "price", "fiyat"]):
        return "#94a3b8"

    return PREMIUM_PALETTE[index % len(PREMIUM_PALETTE)]


def apply_premium_plot_theme(fig: Any, height: int | None = None) -> Any:
    if fig is None:
        return fig

    try:
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(6,14,27,0.94)",
            font=dict(
                family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                color="#e2e8f0",
                size=13,
            ),
            margin=dict(l=44, r=26, t=58, b=46),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(15,23,42,0.96)",
                bordercolor="rgba(125,211,252,0.28)",
                font=dict(color="#f8fafc", size=12),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15,23,42,0.62)",
                bordercolor="rgba(125,211,252,0.18)",
                borderwidth=1,
                font=dict(color="#dbeafe", size=11),
            ),
        )

        if height:
            fig.update_layout(height=height)

        fig.update_xaxes(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.11)",
            zeroline=False,
            linecolor="rgba(125,211,252,0.22)",
            tickfont=dict(color="#cbd5e1", size=11),
            title_font=dict(color="#cbd5e1", size=12),
            showspikes=True,
            spikecolor="rgba(125,211,252,0.35)",
            spikethickness=1,
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.11)",
            zeroline=False,
            linecolor="rgba(125,211,252,0.22)",
            tickfont=dict(color="#cbd5e1", size=11),
            title_font=dict(color="#cbd5e1", size=12),
            showspikes=True,
            spikecolor="rgba(125,211,252,0.35)",
            spikethickness=1,
        )

        for index, trace in enumerate(fig.data):
            name = _trace_name(trace)
            color = _pick_trace_color(name, index)

            if _is_candlestick(trace):
                trace.update(
                    increasing=dict(
                        line=dict(color="#22c55e", width=1.2),
                        fillcolor="rgba(34,197,94,0.62)",
                    ),
                    decreasing=dict(
                        line=dict(color="#f97316", width=1.2),
                        fillcolor="rgba(249,115,22,0.62)",
                    ),
                )

            elif _is_bar(trace):
                trace.update(
                    marker=dict(
                        color=color,
                        line=dict(color="rgba(255,255,255,0.16)", width=1),
                    ),
                    opacity=0.86,
                )

            elif _is_line_like(trace):
                try:
                    current_line = trace.line.to_plotly_json()
                except Exception:
                    current_line = {}

                current_line.setdefault("color", color)
                current_line.setdefault("width", 2.6)

                trace.update(
                    line=current_line,
                    opacity=0.96,
                )

    except Exception:
        return fig

    return fig


def render_premium_plotly_chart(fig: Any, *args: Any, **kwargs: Any) -> None:
    inject_premium_chart_css()

    fig = apply_premium_plot_theme(fig)

    if "use_container_width" not in kwargs and "width" not in kwargs:
        kwargs["use_container_width"] = True

    st.plotly_chart(fig, *args, **kwargs)
