import os
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import streamlit as st

def anahtarsiz_ai_cagir(prompt):
    """
    Hugging Face Serverless API kullanarak tamamen ücretsiz, 
    kurulumsuz ve anahtarsız yapay zeka çağırma motoru.
    """
    API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
    
    payload = {
        "inputs": f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.3, 
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, list) and len(res_json) > 0:
                return res_json[0].get("generated_text", "").strip()
            elif isinstance(res_json, dict):
                return res_json.get("generated_text", "").strip()
        return None
    except Exception as e:
        print(f"Anahtarsız AI Motoru Hatası: {e}")
        return None

@st.cache_data(ttl=3600)
def ai_teknik_analiz_yorumu(enstruman, anlik, boga, ayi):
    prompt = f"Sen profesyonel bir borsa analistisin. {enstruman} şu an {anlik:.2f}. Boğa hedefi {boga:.2f}, Ayı hedefi {ayi:.2f}. Kısa, net, maksimum 2 cümlelik teknik bir yorum yap."
    cevap = anahtarsiz_ai_cagir(prompt)
    return cevap if cevap else "Teknik analiz yorumu şu an üretilemiyor."

def ai_etki_analizi(baslik, varlik):
    prompt = f"Haber: '{baslik}'. Bu haber {varlik} varlığını nasıl etkiler? SADECE şu formatta cevap ver, başka hiçbir kelime ekleme: YÖN (POZİTİF/NEGATİF/NÖTR)|ETKİ YÜZDESİ|Kısa özet."
    cevap = anahtarsiz_ai_cagir(prompt)
    return cevap if cevap else "NÖTR|0|Haber analiz edilemedi."

@st.cache_data(ttl=3600)
def ai_toplu_model_yorumlari(enstruman, anlik, vade, modeller_verisi):
    modeller_metni = "\n".join([f"- {m}: {vade} hedefi {hedef:.2f}" for m, hedef in modeller_verisi.items()])
    
    prompt = f"""Sen bir kantitatif analistsin. {enstruman} şu an {anlik:.2f} seviyesinde. 
    Modellerin hedefleri şunlardır:
    {modeller_metni}

    Her modelin hedefini tek (1) kısa cümleyle yorumla.
    SADECE AŞAĞIDAKİ JSON FORMATINDA CEVAP VER, BAŞKA HİÇBİR ŞEY YAZMA:
    {{
        "random_forest": "Yorum",
        "svm": "Yorum",
        "lin_reg": "Yorum",
        "arima": "Yorum",
        "monte_carlo": "Yorum",
        "xgboost": "Yorum"
    }}
    """
    
    sonuclar = {m: "🤖 Analiz izleniyor." for m in modeller_verisi.keys()}
    cevap = anahtarsiz_ai_cagir(prompt)
    
    if cevap:
        try:
            match = re.search(r'\{.*\}', cevap, re.DOTALL)
            if match:
                ai_cevaplari = json.loads(match.group(0))
                for m in modeller_verisi.keys():
                    for ai_key, ai_yorum in ai_cevaplari.items():
                        if m.lower() in ai_key.lower() or m.replace("_", "").lower() in ai_key.lower():
                            sonuclar[m] = ai_yorum
                            break
        except Exception as e:
            print(f"JSON Çözümleme Hatası: {e}")
            
    return sonuclar

def canli_rss_haber_cek(arama_kelimesi):
    try:
        query = urllib.parse.quote(f"{arama_kelimesi} finance")
        url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        haberler = []
        for item in root.findall('./channel/item')[:4]:
            title_elem = item.find('title')
            link_elem = item.find('link')
            if title_elem is None or link_elem is None: continue
            
            pub_date_elem = item.find('pubDate')
            source_elem = item.find('source')
            haberler.append({
                "title": title_elem.text, 
                "link": link_elem.text, 
                "media": source_elem.text if source_elem is not None else "Haber Kaynağı",
                "date": pub_date_elem.text if pub_date_elem is not None else "Tarih Yok"
            })
        return haberler
    except Exception as e:
        print(f"Haber Hatası: {e}")
        return []
