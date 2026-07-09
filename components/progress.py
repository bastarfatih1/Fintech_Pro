"""
Analiz ilerleme ve hata yönetimi.

Bu bileşen ilerleme çubuğunun yaşam döngüsünü ve
kullanıcıya gösterilen genel hata mesajlarını yönetir.
"""

import time
from typing import Optional

import streamlit as st


class AnalysisProgress:
    """Streamlit ilerleme çubuğunu güvenli şekilde yönetir."""

    def __init__(self) -> None:
        self._bar = st.progress(
            0,
            text="Veriler işleniyor, kantitatif modeller çalıştırılıyor...",
        )
        self._closed = False

    def update(self, value: int, text: str) -> None:
        """İlerleme değerini ve açıklamasını günceller."""
        if self._closed:
            return

        safe_value = max(0, min(100, int(value)))
        self._bar.progress(safe_value, text=text)

    def complete(self, delay_seconds: float = 0.5) -> None:
        """İlerlemeyi tamamlar ve çubuğu kaldırır."""
        if self._closed:
            return

        self._bar.progress(100, text="Tamamlandı.")

        if delay_seconds > 0:
            time.sleep(delay_seconds)

        self.close()

    def close(self) -> None:
        """İlerleme çubuğunu ekrandan kaldırır."""
        if self._closed:
            return

        self._bar.empty()
        self._closed = True


def render_analysis_error(
    error: Exception,
    user_message: Optional[str] = None,
) -> None:
    """Analiz hatasını kullanıcıya anlaşılır biçimde gösterir."""
    message = user_message or (
        "Veri çekilirken veya analiz yapılırken bir sorun oluştu."
    )

    st.error(f"Sistem Hatası: {message} Detay: {error}")
    st.info(
        "İnternet bağlantısını, seçilen varlığı ve giriş değerlerini kontrol edin."
    )
