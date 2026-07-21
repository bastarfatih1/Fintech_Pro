from __future__ import annotations

import time
import streamlit as st


def render_analysis_countdown(total_seconds: int = 12) -> None:
    """Analiz başlamadan önce premium geri sayım paneli gösterir.

    Streamlit tek akışlı çalıştığı için bu sayaç, analiz sonucunun ekrana kontrollü
    ve anlaşılır şekilde gelmesini sağlar.
    """
    total_seconds = max(int(total_seconds), 3)

    box = st.empty()
    bar = st.progress(0)

    stages = [
        "Piyasa verileri hazırlanıyor",
        "Fiyat geçmişi ve teknik göstergeler kontrol ediliyor",
        "Model tahminleri hesaplamaya hazırlanıyor",
        "Konsensüs ve senaryo çıktısı oluşturuluyor",
    ]

    for elapsed in range(total_seconds + 1):
        remaining = total_seconds - elapsed
        pct = int((elapsed / total_seconds) * 100)

        stage_index = min(
            int((elapsed / max(total_seconds, 1)) * len(stages)),
            len(stages) - 1,
        )
        stage = stages[stage_index]

        with box.container(border=True):
            c1, c2, c3 = st.columns([1.1, 1.4, 1])

            with c1:
                st.metric("Analiz geri sayımı", f"{remaining} sn")

            with c2:
                st.markdown("### Analiz hazırlanıyor")
                st.caption(stage)

            with c3:
                st.metric("İlerleme", f"%{pct}")

        bar.progress(min(max(pct, 0), 100))
        time.sleep(1)

    box.empty()
    bar.empty()
