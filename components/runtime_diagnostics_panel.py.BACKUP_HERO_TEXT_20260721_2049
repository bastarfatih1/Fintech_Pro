from __future__ import annotations

import pandas as pd
import streamlit as st

from services.runtime_monitor import get_runtime_snapshot
from components.premium_ui import render_premium_table


def render_runtime_diagnostics_panel() -> None:
    snapshot = get_runtime_snapshot()

    st.markdown("### Çalışma ve Performans Takibi")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Sayfa Yeniden Çalışma", snapshot["app_rerun_count"])

    with col2:
        st.metric("Analiz Motoru Çalışma", snapshot["analysis_run_count"])

    with col3:
        active_text = "Evet" if snapshot["analysis_active"] else "Hayır"
        st.metric("Analiz Şu An Çalışıyor", active_text)

    runtime_rows = [
        {
            "Ölçüm": "Son sayfa rerun zamanı",
            "Değer": snapshot["last_rerun_at"],
        },
        {
            "Ölçüm": "Son analiz başlama zamanı",
            "Değer": snapshot["last_analysis_started_at"],
        },
        {
            "Ölçüm": "Son analiz bitiş zamanı",
            "Değer": snapshot["last_analysis_finished_at"],
        },
        {
            "Ölçüm": "Son analiz başarılı mı?",
            "Değer": snapshot["last_analysis_success"],
        },
        {
            "Ölçüm": "Son analiz hatası",
            "Değer": snapshot["last_analysis_error"] or "-",
        },
    ]

    render_premium_table(
        pd.DataFrame(runtime_rows),
        title="Runtime Durumu",
        subtitle=(
            "Bu tablo sekme değiştirme, buton kullanımı ve analiz motoru tetiklenmesini "
            "ayırmak için kullanılır. Amaç ağır modellerin gereksiz tekrar çalışmasını yakalamaktır."
        ),
    )

    cache_items = snapshot.get("cache_items", {})

    if cache_items:
        cache_rows = []

        for name, info in cache_items.items():
            cache_rows.append(
                {
                    "Cache Alanı": name,
                    "Çağrı Sayısı": info.get("count", 0),
                    "Son Kullanım": info.get("last_at", "-"),
                    "Son Hit": info.get("last_hit", "-"),
                }
            )

        render_premium_table(
            pd.DataFrame(cache_rows),
            title="Cache Gözlemi",
            subtitle="Veri ve kaynak katmanlarının kaç kez kullanıldığını gösterir.",
        )
    else:
        st.info("Henüz izlenen cache olayı yok.")
