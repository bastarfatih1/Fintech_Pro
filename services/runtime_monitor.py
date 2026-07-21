from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import streamlit as st


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def mark_app_rerun() -> None:
    st.session_state["runtime_app_rerun_count"] = (
        int(st.session_state.get("runtime_app_rerun_count", 0)) + 1
    )
    st.session_state["runtime_last_rerun_at"] = _now_text()


def mark_analysis_start() -> None:
    st.session_state["runtime_analysis_run_count"] = (
        int(st.session_state.get("runtime_analysis_run_count", 0)) + 1
    )
    st.session_state["runtime_analysis_active"] = True
    st.session_state["runtime_last_analysis_started_at"] = _now_text()


def mark_analysis_end(success: bool = True, error: str | None = None) -> None:
    st.session_state["runtime_analysis_active"] = False
    st.session_state["runtime_last_analysis_finished_at"] = _now_text()
    st.session_state["runtime_last_analysis_success"] = bool(success)

    if error:
        st.session_state["runtime_last_analysis_error"] = str(error)
    elif success:
        st.session_state["runtime_last_analysis_error"] = ""


def mark_cache_event(name: str, hit: bool | None = None) -> None:
    key = f"runtime_cache_{name}"
    current = dict(st.session_state.get(key, {}))

    current["count"] = int(current.get("count", 0)) + 1
    current["last_at"] = _now_text()

    if hit is not None:
        current["last_hit"] = bool(hit)

    st.session_state[key] = current


def get_runtime_snapshot() -> Dict[str, Any]:
    cache_items = {}

    for key, value in st.session_state.items():
        if str(key).startswith("runtime_cache_"):
            cache_items[str(key).replace("runtime_cache_", "")] = value

    return {
        "app_rerun_count": int(st.session_state.get("runtime_app_rerun_count", 0)),
        "analysis_run_count": int(st.session_state.get("runtime_analysis_run_count", 0)),
        "analysis_active": bool(st.session_state.get("runtime_analysis_active", False)),
        "last_rerun_at": st.session_state.get("runtime_last_rerun_at", "-"),
        "last_analysis_started_at": st.session_state.get("runtime_last_analysis_started_at", "-"),
        "last_analysis_finished_at": st.session_state.get("runtime_last_analysis_finished_at", "-"),
        "last_analysis_success": st.session_state.get("runtime_last_analysis_success", "-"),
        "last_analysis_error": st.session_state.get("runtime_last_analysis_error", ""),
        "cache_items": cache_items,
    }
