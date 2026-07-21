import urllib.parse
import xml.etree.ElementTree as ET
import json
import re

import requests
import streamlit as st

from services.ai_provider import ai_single_prompt_analysis, ai_text_call


def render_premium_ai_loading():
    """AI sentezi sırasında HTML kullanmadan native Streamlit panel gösterir."""
    import streamlit as st

    with st.container(border=True):
        st.markdown("### AI analiz ediliyor")
        st.caption("Haber akışı, teknik senaryo ve risk notu tek merkezde sentezleniyor.")
        st.progress(88)

def ai_teknik_analiz_yorumu(enstruman, anlik, boga, ayi):
    """
    Teknik analiz yorumunu aktif AI sağlayıcısından alır.

    Bu fonksiyon eski arayüzle uyumlu kalır.
    """
    bundle = ai_single_prompt_analysis(
        asset_name=enstruman,
        current_price=float(anlik),
        bull_target=float(boga),
        bear_target=float(ayi),
        news_items=[],
    )

    summary = str(bundle.get("technical_summary", "")).strip()

    if summary:
        return summary

    return (
        f"{enstruman} için teknik göstergeler izleniyor; boğa senaryosu "
        f"{boga:.2f}, ayı senaryosu {ayi:.2f} seviyesinde."
    )


@st.cache_data(ttl=300, show_spinner=False)
def ai_etki_analizi(baslik, varlik):
    """
    Tek haber için eski formatta AI analizi döndürür.

    Not:
    Yayın modunda haber panelinde mümkün olduğunca toplu analiz kullanılmalı.
    Bu fonksiyon eski kodun bozulmaması için korunmuştur.
    """
    bundle = ai_single_prompt_analysis(
        asset_name=varlik,
        current_price=0.0,
        bull_target=0.0,
        bear_target=0.0,
        news_items=[{"title": baslik, "media": ""}],
    )

    analyses = bundle.get("news_analysis", [])

    if analyses and isinstance(analyses[0], dict):
        item = analyses[0]
        direction = str(item.get("direction", "NÖTR")).upper()
        impact = str(item.get("impact", 0))
        confidence = str(item.get("confidence", 50))
        summary = str(item.get("summary", "Haber etkisi nötr kabul edildi."))
        return f"{direction}|{impact}|{confidence}|{summary}"

    return (
        "NÖTR|0|50|Sistem otomatik yanıtı: Haber metni teknik etki "
        "yaratmayacak düzeyde nötr kabul edildi."
    )


@st.cache_data(ttl=300, show_spinner=False)
def ai_haberleri_toplu_analiz_et(
    varlik,
    haberler,
    anlik=0.0,
    boga=0.0,
    ayi=0.0,
):
    """
    Haberlerin tamamını tek AI isteğiyle analiz eder.

    Kullanım amacı:
    Streamlit Cloud / GitHub yayın modunda çok sayıda AI isteği atmayı engellemek.
    """
    return ai_single_prompt_analysis(
        asset_name=varlik,
        current_price=float(anlik or 0.0),
        bull_target=float(boga or 0.0),
        bear_target=float(ayi or 0.0),
        news_items=list(haberler or [])[:6],
    )


@st.cache_data(ttl=300, show_spinner=False)
def ai_toplu_model_yorumlari(enstruman, anlik, vade, modeller_verisi):
    modeller_metni = "\n".join(
        [f"- {m}: {hedef:.2f}" for m, hedef in modeller_verisi.items()]
    )
    prompt = f"""Sen profesyonel bir kantitatif analistsin.
{enstruman} şu an {anlik:.2f} seviyesinde.
Vade: {vade}

Modeller:
{modeller_metni}

Her model için yatırım tavsiyesi vermeyen, tek cümlelik teknik yorum üret.
Sadece geçerli JSON döndür.
"""

    sonuclar = {
        m: "Standart projeksiyon: Algoritmik trend izleniyor."
        for m in modeller_verisi.keys()
    }

    cevap = ai_text_call(prompt, timeout=12.0)

    if cevap:
        try:
            match = re.search(r"\{.*\}", cevap, re.DOTALL)
            if match:
                ai_cevaplari = json.loads(match.group(0))
                for m in modeller_verisi.keys():
                    for ai_key, ai_yorum in ai_cevaplari.items():
                        if (
                            m.lower() in ai_key.lower()
                            or m.replace("_", "").lower()
                            in ai_key.replace("_", "").lower()
                        ):
                            sonuclar[m] = ai_yorum
                            break
        except Exception:
            pass

    return sonuclar


def canli_rss_haber_cek(arama_kelimesi):
    try:
        query = urllib.parse.quote(f"{arama_kelimesi} finance")
        url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR"
        response = requests.get(url, timeout=5)
        root = ET.fromstring(response.content)
        haberler = []
        for item in root.findall("./channel/item")[:6]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            source = item.find("source")
            if title is None or link is None:
                continue
            haberler.append(
                {
                    "title": title.text,
                    "link": link.text,
                    "media": (
                        source.text if source is not None else "Haber Kaynağı"
                    ),
                    "date": (
                        pub_date.text if pub_date is not None else "Tarih Yok"
                    ),
                }
            )
        return haberler
    except Exception:
        return []
