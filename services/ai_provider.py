"""
AI sağlayıcı katmanı.

Amaç:
- Lokal geliştirmede Ollama kullanmak
- Yayın / Streamlit Cloud ortamında OpenAI uyumlu API kullanmak
- AI erişilemezse uygulamayı bozmadan güvenli fallback üretmek

Not:
API anahtarları asla GitHub'a yazılmaz. Streamlit Cloud'da secrets alanına,
lokalde ise .streamlit/secrets.toml dosyasına eklenir.
"""

from __future__ import annotations

import json
import os
from typing import Any, Mapping, Sequence

import requests
import streamlit as st


DEFAULT_TIMEOUT = 90.0


def _get_secret_value(key: str, default: str = "") -> str:
    """Önce Streamlit secrets, sonra environment üzerinden değer okur."""
    try:
        value = st.secrets.get(key, default)
    except Exception:
        value = default

    if value:
        return str(value)

    return str(os.getenv(key, default))


def get_ai_provider_name() -> str:
    """
    Aktif AI sağlayıcısını döndürür.

    Öncelik:
    1. AI_PROVIDER secret/env
    2. OPENAI_API_KEY varsa openai
    3. Yoksa ollama
    """
    configured = _get_secret_value("AI_PROVIDER", "").strip().lower()

    if configured:
        return configured

    if _get_secret_value("OPENAI_API_KEY", ""):
        return "openai"

    return "ollama"


def _call_ollama(prompt: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Lokal Ollama API çağrısı yapar."""
    model = _get_secret_value("OLLAMA_MODEL", "")
    if not model:
        model = st.session_state.get("USER_GEMINI_MODEL", "llama3")

    url = _get_secret_value(
        "OLLAMA_URL",
        "http://localhost:11434/api/generate",
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 700,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return str(response.json().get("response", "")).strip() or None
    except Exception:
        return None


def _call_openai(prompt: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """
    OpenAI Chat Completions API çağrısı yapar.

    Harici openai paketi gerektirmez; requests ile çalışır.
    """
    api_key = _get_secret_value("OPENAI_API_KEY", "")
    if not api_key:
        return None

    model = _get_secret_value("OPENAI_MODEL", "gpt-4o-mini")
    base_url = _get_secret_value(
        "OPENAI_BASE_URL",
        "https://api.openai.com/v1",
    ).rstrip("/")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Sen finansal veri analizi arayüzü için kısa, dikkatli "
                    "ve yatırım tavsiyesi vermeyen Türkçe açıklamalar üreten "
                    "bir analiz asistanısın. Al, sat, tut gibi yönlendirme "
                    "ifadeleri kullanma."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
            or None
        )
    except Exception:
        return None


def ai_text_call(prompt: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Aktif sağlayıcıya göre tek metin çağrısı yapar."""
    provider = get_ai_provider_name()

    if provider == "openai":
        return _call_openai(prompt, timeout=timeout)

    if provider == "ollama":
        return _call_ollama(prompt, timeout=timeout)

    return None


def _extract_json_object(raw_text: str | None) -> dict[str, Any] | None:
    """AI çıktısından JSON objesi ayıklar."""
    if not raw_text:
        return None

    text = raw_text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(text[start : end + 1])
    except Exception:
        return None

    if isinstance(parsed, dict):
        return parsed

    return None


def build_fallback_ai_bundle(
    asset_name: str,
    current_price: float,
    bull_target: float,
    bear_target: float,
    news_items: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """AI çalışmadığında uygulamanın bozulmaması için güvenli varsayılan üretir."""
    news_items = list(news_items or [])

    news_analysis = []
    for item in news_items[:6]:
        news_analysis.append(
            {
                "headline": str(item.get("title", "Başlıksız Haber")),
                "direction": "NÖTR",
                "impact": 0,
                "confidence": 50,
                "summary": (
                    "AI sağlayıcısı kullanılamadığı için haber etkisi nötr "
                    "varsayıldı."
                ),
            }
        )

    return {
        "technical_summary": (
            f"{asset_name} için teknik seviyeler izleniyor. Boğa senaryosu "
            f"{bull_target:.2f}, ayı senaryosu {bear_target:.2f} seviyesinde."
        ),
        "market_synthesis": (
            "AI sağlayıcısı geçici olarak kullanılamıyor. Sonuçlar model "
            "çıktıları ve tarihsel metrikler üzerinden okunmalıdır."
        ),
        "risk_note": (
            "Bu çıktı yatırım tavsiyesi değildir; yalnızca veri analizi ve "
            "senaryo değerlendirmesi amacı taşır."
        ),
        "overall_news_effect": "NÖTR",
        "news_effect_summary": (
            "AI sağlayıcısı kullanılamadığı için haber etkisi genel analizde "
            "nötr kabul edildi."
        ),
        "news_analysis": news_analysis,
        "provider": "fallback",
    }


@st.cache_data(ttl=1800)
def ai_single_prompt_analysis(
    asset_name: str,
    current_price: float,
    bull_target: float,
    bear_target: float,
    news_items: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Teknik özet ve haber duyarlılığını tek AI isteğinde üretir.

    Böylece 6 haber için 6 ayrı istek yerine tek istek gönderilir.
    """
    news_items = list(news_items or [])[:6]
    news_lines = []

    for index, item in enumerate(news_items, start=1):
        news_lines.append(
            f"{index}. {item.get('title', 'Başlıksız Haber')} "
            f"Kaynak: {item.get('media', 'Bilinmeyen Kaynak')}"
        )

    news_text = "\n".join(news_lines) if news_lines else "Haber bulunamadı."

    prompt = f"""
Varlık: {asset_name}
Güncel fiyat: {current_price:.4f}
Boğa senaryosu: {bull_target:.4f}
Ayı senaryosu: {bear_target:.4f}

Haberler:
{news_text}

Görev:
Teknik özet, piyasa sentezi, risk notu ve haber bazlı duyarlılık analizi üret.

Kurallar:
- Türkçe yaz.
- Yatırım tavsiyesi verme.
- Al / sat / tut ifadeleri kullanma.
- Kesinlik veya garanti dili kullanma.
- Sadece geçerli JSON döndür.

JSON şeması:
{{
  "technical_summary": "Tek cümlelik teknik özet",
  "market_synthesis": "Kısa genel sentez",
  "risk_note": "Kısa risk ve sorumluluk notu",
  "overall_news_effect": "POZİTİF veya NEGATİF veya NÖTR",
  "news_effect_summary": "Haberlerin genel analize etkisini açıklayan kısa cümle",
  "news_analysis": [
    {{
      "headline": "Haber başlığı",
      "direction": "POZİTİF veya NEGATİF veya NÖTR",
      "impact": 0,
      "confidence": 50,
      "summary": "Kısa haber etkisi"
    }}
  ]
}}
"""

    raw_response = ai_text_call(prompt, timeout=DEFAULT_TIMEOUT)
    parsed = _extract_json_object(raw_response)

    if not parsed:
        return build_fallback_ai_bundle(
            asset_name=asset_name,
            current_price=current_price,
            bull_target=bull_target,
            bear_target=bear_target,
            news_items=news_items,
        )

    parsed.setdefault("technical_summary", "")
    parsed.setdefault("market_synthesis", "")
    parsed.setdefault("risk_note", "")
    parsed.setdefault("overall_news_effect", "NÖTR")
    parsed.setdefault("news_effect_summary", "")
    parsed.setdefault("news_analysis", [])
    parsed["provider"] = get_ai_provider_name()

    if not isinstance(parsed["news_analysis"], list):
        parsed["news_analysis"] = []

    return parsed



def get_ai_diagnostic() -> dict[str, str]:
    """AI bağlantısı için kullanıcıya gösterilebilir kısa durum bilgisi döndürür."""
    provider = get_ai_provider_name()
    diagnostic = {
        "provider": provider,
        "ollama_model": _get_secret_value("OLLAMA_MODEL", ""),
        "ollama_url": _get_secret_value(
            "OLLAMA_URL",
            "http://localhost:11434/api/generate",
        ),
        "openai_model": _get_secret_value("OPENAI_MODEL", "gpt-4o-mini"),
        "has_openai_key": "yes" if bool(_get_secret_value("OPENAI_API_KEY", "")) else "no",
    }
    return diagnostic
