import os
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import streamlit as st
from google import genai  # Resmi yeni Google SDK

def gemini_baslat():
    api_key = None
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass
        
    if not api_key:
        api_key = "AIzaSyCZGqjtf3MbqIsRQud3oBzFc3vwGvJ7nTw"
        
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[Gemini Başlatma Hatası]: {e}")
        return None

def canli_rss_haber_cek(arama_kelimesi):
    haberler = []
    client = gemini_baslat()
    
    try:
        query = urllib.parse.quote(f"{arama_kelimesi} market finance")
        url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        for item in root.findall('./channel/item')[:4]:
            title_elem = item.find('title')
            link_elem = item.find('link')
            
            if title_elem is None or link_elem is None:
                continue
                
            title = title_elem.text
            link = link_elem.text
            
            pub_date_elem = item.find('pubDate')
            pub_date = pub_date_elem.text if pub_date_elem is not None else "Tarih Belirtilmemiş"
            if " GMT" in pub_date:
                pub_date = pub_date.replace(" GMT", "")[:-3]
                
            source_elem = item.find('source')
            media_name = source_elem.text if source_elem is not None else "Haber Kaynağı"
            
            if client:
                try:
                    prompt = f"Şu haber başlığını oku: '{title}'. Bu haber doğrudan ekonomi, finans veya piyasalarla mı ilgili? Sadece 'EVET' veya 'HAYIR' yaz, başka hiçbir kelime kullanma."
                    # DEĞİŞİKLİK: model ismi güncellendi ve ön ek kaldırıldı
                    ai_response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    ai_cevap = ai_response.text.strip().upper()
                    
                    if "EVET" in ai_cevap:
                        haberler.append({"title": title, "link": link, "media": media_name, "date": pub_date})
                except Exception as ai_err:
                    print(f"[Gemini Filtre Hatası]: {ai_err}")
                    haberler.append({"title": title, "link": link, "media": media_name, "date": pub_date})
            else:
                haberler.append({"title": title, "link": link, "media": media_name, "date": pub_date})
                
    except Exception as e:
        print(f"[Haber Motoru RSS Hatası]: {e}")
        
    return haberler

def ai_etki_analizi(haber_basligi, enstruman_ismi):
    try:
        client = gemini_baslat()
        if not client:
            return "NÖTR | 0.0 | AI motoru başlatılamadı."
            
        prompt = f"""Sen profesyonel bir kantitatif analistsin. Şu haberin: '{haber_basligi}' -> {enstruman_ismi} fiyatlarına olası etkisini analiz et.
        LÜTFEN SADECE AŞAĞIDAKİ FORMATTA YANIT VER (Başka hiçbir açıklama veya markdown ekleme):
        ETKİ YÖNÜ (POZİTİF, NEGATİF veya NÖTR) | ETKİ YÜZDESİ (Sadece rakam, örn: 2.5) | 1 CÜMLELİK ÖZET
        Örnek: POZİTİF | 1.5 | Şirketin yeni yatırımı büyüme beklentilerini artırdı."""
        
        # DEĞİŞİKLİK: model ismi güncellendi
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Etki Analiz Hatası]: {e}")
        return "NÖTR | 0.0 | Yapay zeka analiz motoruna şu an ulaşılamıyor."

def ai_teknik_analiz_yorumu(enstruman_ismi, anlik_fiyat, boga_fiyat, ayi_fiyat):
    try:
        client = gemini_baslat()
        if not client:
            return "🤖 AI Yorum Motoru Çevrimdışı"
            
        prompt = f"""Sen Wall Street seviyesinde profesyonel bir teknik analistsin. 
        {enstruman_ismi} şu an {anlik_fiyat} seviyenisinden işlem görüyor. 
        Yapay zeka ve kantitatif algoritmalarımız bu varlık için önümüzdeki dönemde iyimser (boğa) hedefi {boga_fiyat:.2f}, kötümser (ayı) destek seviyesini ise {ayi_fiyat:.2f} olarak belirledi.
        Lütfen yatırımcılara bu durumu özetleyen, 2-3 cümlelik çok profesyonel ve teknik bir piyasa yorumu yap. Sadece yorum metnini ver, başlık vs. kullanma."""
        
        # DEĞİŞİKLİK: model ismi güncellendi
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Teknik Analiz Hatası]: {e}")
        return "🤖 AI Yorum Motoru: Teknik indikatörler ve formasyon hedefleri doğrultusunda fiyat takibi sürdürülmelidir."

def ai_model_yorumu(model_adi, enstruman_ismi, anlik_fiyat, hedef_fiyat, vade):
    try:
        client = gemini_baslat()
        if not client:
            return "🤖 AI Model Yorumu Çevrimdışı"
            
        prompt = f"""Sen profesyonel bir kantitatif analistsin.
        {enstruman_ismi} şu an {anlik_fiyat:.2f} seviyesinde. Bizim '{model_adi}' isimli algoritmamız, {vade} sonra fiyatın {hedef_fiyat:.2f} olacağını öngörüyor.
        Lütfen bu {model_adi} modelinin bu varlık için yaptığı öngörüyü yatırımcıya yorumla. 
        SADECE 2 cümlelik, çok teknik ve profesyonel bir açıklama yaz. Başlık veya giriş kullanma."""
        
        # DEĞİŞİKLİK: model ismi güncellendi
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Model Yorum Hatası]: {e}")
        return "🤖 AI Yorumu: Model projeksiyonları piyasa hacmi ve momentum doğrultusunda izlenmelidir."
