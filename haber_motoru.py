import os
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import streamlit as st

def ollama_ai_cagir(prompt, timeout=2.0):
    """
    Sistemi Ollama üzerinden (Localhost) çalıştırır. 
    Maksimum 2 saniye içinde yanıt gelmezse Exception fırlatarak Fallback mekanizmasını tetikler.
    """
    model = st.session_state.get("USER_GEMINI_MODEL", "llama3")
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        return None
    except Exception as e:
        # Fallback senaryosuna düşürmek için None dönüyoruz
        return None

@st.cache_data(ttl=3600)
def ai_teknik_analiz_yorumu(enstruman, anlik, boga, ayi):
    prompt = f"Sen profesyonel bir borsa analistisin. {enstruman} şuan {anlik:.2f}. Boğa hedefi {boga:.2f}, Ayı hedefi {ayi:.2f}. Sadece tek bir cümle ile kısa ve teknik bir yorum yap."
    cevap = ollama_ai_cagir(prompt, timeout=2.0)
    return cevap if cevap else f"{enstruman} için teknik göstergeler izleniyor; boğa senaryosu {boga:.2f}, ayı senaryosu {ayi:.2f} seviyesinde."

@st.cache_data(ttl=3600)
def ai_etki_analizi(baslik, varlik):
    prompt = f"Haber: '{baslik}'. Bu haber {varlik} varlığını nasıl etkiler? SADECE ŞU FORMATTA YANIT VER: YÖN (POZİTİF/NEGATİF/NÖTR)|ETKİ YÜZDESİ (sadece rakam)|GÜVEN SKORU (0-100)|Kısa özet cümle."
    cevap = ollama_ai_cagir(prompt, timeout=2.0)
    if cevap:
        return cevap
    return "NÖTR|0|50|Sistem otomatik yanıtı: Haber metni teknik etki yaratmayacak düzeyde nötr kabul edildi."

@st.cache_data(ttl=3600)
def ai_toplu_model_yorumlari(enstruman, anlik, vade, modeller_verisi):
    modeller_metni = "\n".join([f"- {m}: {hedef:.2f}" for m, hedef in modeller_verisi.items()])
    prompt = f"""Sen profesyonel bir kantitatif analistsin. {enstruman} şu an {anlik:.2f} seviyesinde. Vade: {vade}. Modeller:
    {modeller_metni}

    Lütfen HER BİR modelin hedefini tek (1) cümlelik teknik bir dille yorumla.
    YANITINI SADECE VE SADECE AŞAĞIDAKİ GİBİ GEÇERLİ BİR JSON FORMATINDA VER:
    {{
        "random_forest": "Yorum...",
        "svr": "Yorum...",
        "linear_regression": "Yorum...",
        "arima": "Yorum...",
        "xgboost": "Yorum...",
        "monte_carlo": "Yorum..."
    }}
    """
    
    sonuclar = {m: "🤖 Standart Projeksiyon: Algoritmik trend izleniyor." for m in modeller_verisi.keys()}
    cevap = ollama_ai_cagir(prompt, timeout=2.0) # 2 Saniye Fallback sınırı
    
    if cevap:
        try:
            # JSON yanıtını güvenli şekilde parse et (Metin içinden ayıkla)
            match = re.search(r'\{.*\}', cevap, re.DOTALL)
            if match:
                ai_cevaplari = json.loads(match.group(0))
                for m in modeller_verisi.keys():
                    for ai_key, ai_yorum in ai_cevaplari.items():
                        if m.lower() in ai_key.lower() or m.replace("_", "").lower() in ai_key.lower():
                            sonuclar[m] = ai_yorum
                            break
        except Exception:
            pass # Parse hatası durumunda varsayılan (fallback) değerler kalır
            
    return sonuclar

def canli_rss_haber_cek(arama_kelimesi):
    try:
        query = urllib.parse.quote(f"{arama_kelimesi} finance")
        url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR"
        response = requests.get(url, timeout=5)
        root = ET.fromstring(response.content)
        haberler = []
        for item in root.findall('./channel/item')[:6]:
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            source = item.find('source')
            if title is None or link is None: continue
            haberler.append({
                "title": title.text, "link": link.text, 
                "media": source.text if source is not None else "Haber Kaynağı",
                "date": pub_date.text if pub_date is not None else "Tarih Yok"
            })
        return haberler
    except:
        return []