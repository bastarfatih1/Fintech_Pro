"""
AI sağlayıcı katmanı.

Amaç:
- Lokal geliştirmede Ollama kullanmak
- Yayın / Streamlit Cloud ortamında Groq veya OpenAI uyumlu API kullanmak
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


DEFAULT_TIMEOUT = 150.0
LAST_AI_ERROR = ""


def _get_secret_value(key: str, default: str = "") -> str:
    """Önce Streamlit secrets, sonra environment üzerinden değer okur."""
    try:
        value = st.secrets.get(key, default)
    except Exception:
        value = default

    if value:
        return str(value)

    return str(os.getenv(key, default))




def _get_int_secret_value(key: str, default: int) -> int:
    """Secret/env içinden güvenli integer değer okur."""
    raw_value = _get_secret_value(key, str(default))
    try:
        value = int(str(raw_value).strip())
    except (TypeError, ValueError):
        return default

    return max(128, min(value, 4000))


def get_ai_provider_name() -> str:
    """
    Aktif AI sağlayıcısını döndürür.

    Öncelik:
    1. AI_PROVIDER secret/env
    2. GROQ_API_KEY varsa groq
    3. OPENAI_API_KEY varsa openai
    4. Yoksa ollama
    """
    configured = _get_secret_value("AI_PROVIDER", "").strip().lower()

    if configured:
        return configured

    if _get_secret_value("GROQ_API_KEY", ""):
        return "groq"

    if _get_secret_value("OPENAI_API_KEY", ""):
        return "openai"

    return "ollama"


def get_last_ai_error() -> str:
    """Son AI hatasını güvenli şekilde döndürür."""
    return LAST_AI_ERROR


def _call_ollama(prompt: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Lokal Ollama API çağrısı yapar."""
    global LAST_AI_ERROR
    LAST_AI_ERROR = ""

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
            "num_predict": _get_int_secret_value("OLLAMA_NUM_PREDICT", 1200),
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        content = str(response.json().get("response", "")).strip()
        if not content:
            LAST_AI_ERROR = "Ollama yanıtı boş geldi."
            return None
        return content
    except Exception as exc:
        LAST_AI_ERROR = f"Ollama bağlantı/yanıt hatası: {type(exc).__name__}: {exc}"
        return None


def _call_openai(prompt: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """
    OpenAI Chat Completions API çağrısı yapar.

    Harici openai paketi gerektirmez; requests ile çalışır.
    """
    global LAST_AI_ERROR
    LAST_AI_ERROR = ""

    api_key = _get_secret_value("OPENAI_API_KEY", "")
    if not api_key:
        LAST_AI_ERROR = "OPENAI_API_KEY bulunamadı. Streamlit Secrets kontrol edilmeli."
        st.error("OpenAI API key bulunamadı.")
        st.caption("Streamlit Cloud → Manage app → Settings → Secrets bölümünü kontrol et.")
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

        if response.status_code != 200:
            LAST_AI_ERROR = (
                f"OpenAI HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            st.error(f"OpenAI hata kodu: {response.status_code}")
            st.code(response.text[:1000])
            return None

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:
            LAST_AI_ERROR = "OpenAI yanıtı boş geldi."
            st.error("OpenAI yanıtı boş geldi.")
            return None

        return content

    except Exception as exc:
        LAST_AI_ERROR = f"OpenAI bağlantı hatası: {type(exc).__name__}: {exc}"
        st.error("OpenAI bağlantı hatası")
        st.code(str(exc))
        return None


def _call_groq(prompt: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """
    Groq OpenAI uyumlu Chat Completions API çağrısı yapar.

    Harici groq paketi gerektirmez; requests ile çalışır.
    """
    global LAST_AI_ERROR
    LAST_AI_ERROR = ""

    api_key = _get_secret_value("GROQ_API_KEY", "")
    if not api_key:
        LAST_AI_ERROR = "GROQ_API_KEY bulunamadı. Streamlit Secrets kontrol edilmeli."
        st.error("Groq API key bulunamadı.")
        st.caption("Streamlit Cloud → Manage app → Settings → Secrets bölümünü kontrol et.")
        return None

    model = _get_secret_value("GROQ_MODEL", "llama-3.1-8b-instant")
    base_url = _get_secret_value(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1",
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
                    "ifadeleri kullanma. Sadece ham JSON objesi döndür. "
                    "JSON dışında açıklama, markdown veya kod bloğu yazma. "
                    "Cevap doğrudan { karakteri ile başlamalı ve } karakteri ile bitmeli. "
                    "news_analysis dizisi, verilen haber sayısı kadar öğe içermeli."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.1,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
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

        if response.status_code != 200:
            LAST_AI_ERROR = (
                f"Groq HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            st.error(f"Groq hata kodu: {response.status_code}")
            st.code(response.text[:1000])
            return None

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:
            LAST_AI_ERROR = "Groq yanıtı boş geldi."
            st.error("Groq yanıtı boş geldi.")
            return None

        return content

    except Exception as exc:
        LAST_AI_ERROR = f"Groq bağlantı hatası: {type(exc).__name__}: {exc}"
        st.error("Groq bağlantı hatası")
        st.code(str(exc))
        return None

def ai_text_call(prompt: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Aktif sağlayıcıya göre tek metin çağrısı yapar."""
    global LAST_AI_ERROR
    provider = get_ai_provider_name()

    if provider == "groq":
        return _call_groq(prompt, timeout=timeout)

    if provider == "openai":
        return _call_openai(prompt, timeout=timeout)

    if provider == "ollama":
        return _call_ollama(prompt, timeout=timeout)

    LAST_AI_ERROR = f"Bilinmeyen AI_PROVIDER: {provider}"
    st.error(LAST_AI_ERROR)
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


def _classify_news_locally(title: str) -> dict[str, Any]:
    """AI erişilemediğinde haber başlığını basit anahtar kelimelerle yorumlar."""
    lowered = str(title or "").lower()

    positive_words = (
        "yükseldi",
        "arttı",
        "artış",
        "rekor",
        "güçlendi",
        "pozitif",
        "talep",
        "destek",
        "alıcılı",
        "toparlan",
        "kazanç",
    )
    negative_words = (
        "düştü",
        "düşüş",
        "geriledi",
        "satış",
        "kayıp",
        "zayıf",
        "baskı",
        "risk",
        "kriz",
        "belirsiz",
        "faiz",
        "sert",
    )

    positive_score = sum(1 for word in positive_words if word in lowered)
    negative_score = sum(1 for word in negative_words if word in lowered)

    if positive_score > negative_score:
        return {
            "direction": "POZİTİF",
            "impact": 20,
            "confidence": 55,
            "summary": (
                "AI sağlayıcısı yanıt vermediği için yerel haber okuması kullanıldı. "
                "Başlıktaki olumlu ifadeler kısa vadeli algıyı destekleyebilir."
            ),
        }

    if negative_score > positive_score:
        return {
            "direction": "NEGATİF",
            "impact": -20,
            "confidence": 55,
            "summary": (
                "AI sağlayıcısı yanıt vermediği için yerel haber okuması kullanıldı. "
                "Başlıktaki olumsuz ifadeler risk veya baskı ihtimalini artırabilir."
            ),
        }

    return {
        "direction": "NÖTR",
        "impact": 0,
        "confidence": 50,
        "summary": (
            "AI sağlayıcısı yanıt vermediği için yerel haber okuması kullanıldı. "
            "Başlık tek başına güçlü pozitif veya negatif etki göstermiyor."
        ),
    }


def build_fallback_ai_bundle(
    asset_name: str,
    current_price: float,
    bull_target: float,
    bear_target: float,
    news_items: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """AI çalışmadığında uygulamanın bozulmaması için yerel yorum üretir."""
    news_items = list(news_items or [])

    news_analysis = []
    direction_counts = {"POZİTİF": 0, "NEGATİF": 0, "NÖTR": 0}

    for item in news_items[:6]:
        headline = str(item.get("title", "Başlıksız Haber"))
        local_result = _classify_news_locally(headline)
        direction_counts[local_result["direction"]] += 1
        news_analysis.append(
            {
                "headline": headline,
                **local_result,
            }
        )

    if direction_counts["POZİTİF"] > direction_counts["NEGATİF"]:
        overall_effect = "POZİTİF"
        effect_summary = (
            "AI sağlayıcısı yanıt vermedi; yerel haber okumasında olumlu başlıklar "
            "biraz daha baskın görünüyor."
        )
    elif direction_counts["NEGATİF"] > direction_counts["POZİTİF"]:
        overall_effect = "NEGATİF"
        effect_summary = (
            "AI sağlayıcısı yanıt vermedi; yerel haber okumasında risk veya baskı "
            "içeren başlıklar biraz daha baskın görünüyor."
        )
    else:
        overall_effect = "NÖTR"
        effect_summary = (
            "AI sağlayıcısı yanıt vermedi; yerel haber okuması güçlü bir haber yönü "
            "göstermiyor."
        )

    return {
        "technical_summary": (
            f"{asset_name} için teknik seviyeler izleniyor. Boğa senaryosu "
            f"{bull_target:.2f}, ayı senaryosu {bear_target:.2f} seviyesinde."
        ),
        "market_synthesis": (
            "AI sağlayıcısı yanıt vermediği için bu bölüm yerel otomatik haber "
            "okuması ve model çıktılarıyla dolduruldu."
        ),
        "risk_note": (
            "Bu çıktı yatırım tavsiyesi değildir; yalnızca veri analizi ve "
            "senaryo değerlendirmesi amacı taşır."
        ),
        "overall_news_effect": overall_effect,
        "news_effect_summary": effect_summary,
        "news_analysis": news_analysis,
        "provider": "local_fallback",
        "provider_error": get_last_ai_error(),
    }


@st.cache_data(ttl=300, show_spinner=False)
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
Sadece geçerli JSON döndür. Markdown, açıklama veya kod bloğu yazma.

Varlık: {asset_name}
Güncel fiyat: {current_price:.4f}
Olumlu senaryo: {bull_target:.4f}
Olumsuz senaryo: {bear_target:.4f}

Haberler:
{news_text}

Kurallar:
- Türkçe yaz.
- Yatırım tavsiyesi verme.
- Al / sat / tut deme.
- Her haber için tam 1 kısa yorum yaz.
- direction sadece POZİTİF, NEGATİF veya NÖTR olsun.
- impact -100 ile 100 arasında sayı olsun.
- confidence 0 ile 100 arasında sayı olsun.

JSON:
{{
  "technical_summary": "1 cümle teknik özet",
  "market_synthesis": "1 cümle genel sentez",
  "risk_note": "1 cümle risk notu",
  "overall_news_effect": "POZİTİF",
  "news_effect_summary": "1 cümle haber etkisi özeti",
  "news_analysis": [
    {{
      "headline": "haber başlığı",
      "direction": "POZİTİF",
      "impact": 20,
      "confidence": 60,
      "summary": "1 cümle haber yorumu"
    }}
  ]
}}
"""

    raw_response = ai_text_call(prompt, timeout=DEFAULT_TIMEOUT)
    parsed = _extract_json_object(raw_response)

    if not parsed:
        compact_prompt = f"""
Sadece geçerli JSON döndür. Markdown yazma.

Varlık: {asset_name}
Fiyat: {current_price:.4f}
Olumlu senaryo: {bull_target:.4f}
Olumsuz senaryo: {bear_target:.4f}

Haberler:
{news_text}

JSON şeması:
{{
  "technical_summary": "kısa teknik özet",
  "market_synthesis": "kısa piyasa sentezi",
  "risk_note": "kısa risk notu",
  "overall_news_effect": "POZİTİF veya NEGATİF veya NÖTR",
  "news_effect_summary": "kısa haber özeti",
  "news_analysis": [
    {{
      "headline": "haber başlığı",
      "direction": "POZİTİF veya NEGATİF veya NÖTR",
      "impact": 0,
      "confidence": 50,
      "summary": "kısa yorum"
    }}
  ]
}}
"""
        raw_response = ai_text_call(compact_prompt, timeout=DEFAULT_TIMEOUT)
        parsed = _extract_json_object(raw_response)

    if not parsed:
        global LAST_AI_ERROR
        if raw_response and not LAST_AI_ERROR:
            LAST_AI_ERROR = (
                "AI yanıtı geldi ama JSON formatına çevrilemedi. "
                f"İlk karakterler: {raw_response[:300]}"
            )

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

    normalized_analysis = []
    for index, item in enumerate(news_items):
        if index < len(parsed["news_analysis"]) and isinstance(
            parsed["news_analysis"][index],
            Mapping,
        ):
            normalized_analysis.append(dict(parsed["news_analysis"][index]))
        else:
            headline = str(item.get("title", "Başlıksız Haber"))
            local_result = _classify_news_locally(headline)
            normalized_analysis.append(
                {
                    "headline": headline,
                    **local_result,
                }
            )

    parsed["news_analysis"] = normalized_analysis[: len(news_items)]

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
        "ollama_num_predict": str(_get_int_secret_value("OLLAMA_NUM_PREDICT", 1200)),
        "openai_model": _get_secret_value("OPENAI_MODEL", "gpt-4o-mini"),
        "groq_model": _get_secret_value("GROQ_MODEL", "llama-3.1-8b-instant"),
        "has_openai_key": "yes" if bool(_get_secret_value("OPENAI_API_KEY", "")) else "no",
        "has_groq_key": "yes" if bool(_get_secret_value("GROQ_API_KEY", "")) else "no",
        "last_error": get_last_ai_error(),
    }
    return diagnostic
