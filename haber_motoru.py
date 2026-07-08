import requests
import urllib.parse
import xml.etree.ElementTree as ET
from ollama import Client

def canli_rss_haber_cek(arama_kelimesi):
    haberler = []
    try:
        # Arama sorgusunu daha güvenli URL formatına çeviriyoruz
        query = urllib.parse.quote(f"{arama_kelimesi} market finance")
        url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
        
        # Timeout süresini 10 saniyeye çıkardık (Sunucu yavaş yanıt verebilir)
        response = requests.get(url, timeout=10)
        response.raise_for_status() # HTTP 200 harici bir kod dönerse hata fırlatır
        
        root = ET.fromstring(response.content)
        client = Client(host='http://localhost:11434')
        
        for item in root.findall('./channel/item')[:4]:
            title_elem = item.find('title')
            link_elem = item.find('link')
            
            # Başlık veya link yoksa bu haberi atla
            if title_elem is None or link_elem is None:
                continue
                
            title = title_elem.text
            link = link_elem.text
            
            # Tarih parçasının güvenli manipülasyonu
            pub_date_elem = item.find('pubDate')
            pub_date = pub_date_elem.text if pub_date_elem is not None else "Tarih Belirtilmemiş"
            if " GMT" in pub_date:
                pub_date = pub_date.replace(" GMT", "")[:-3]
                
            # Yapay Zeka Süzgeci
            try:
                # Promptu yapay zekanın boş yapmasını engelleyecek şekilde kısıtladık
                prompt = f"Şu haber başlığını oku: '{title}'. Bu haber doğrudan ekonomi, finans veya piyasalarla mı ilgili? Sadece 'EVET' veya 'HAYIR' yaz, başka hiçbir kelime kullanma."
                ai_response = client.generate(model='gemma2:2b', prompt=prompt)
                
                # Cevabı temizleyip her ihtimale karşı büyük harfe çeviriyoruz
                ai_cevap = ai_response.get('response', 'HAYIR').strip().upper()
                
                if "EVET" in ai_cevap:
                    source_elem = item.find('source')
                    haberler.append({
                        "title": title, 
                        "link": link, 
                        "media": source_elem.text if source_elem is not None else "Haber Kaynağı",
                        "date": pub_date
                    })
            except Exception as ai_err:
                print(f"[Ollama Hatası] Filtreleme yapılamadı: {ai_err}")
                # AI çökerse döngü bozulmasın, diğer habere geçsin
                continue
                
    except requests.exceptions.RequestException as req_err:
        print(f"[Haber Motoru] İnternet veya bağlantı sorunu: {req_err}")
    except ET.ParseError as parse_err:
        print(f"[Haber Motoru] RSS veri formatı bozuk: {parse_err}")
    except Exception as e:
        print(f"[Haber Motoru] Beklenmeyen Hata: {e}")
        
    return haberler

def ai_etki_analizi(haber_basligi, enstruman_ismi):
    try:
        from ollama import Client
        client = Client(host='http://localhost:11434')
        
        # Yapay zekayı spesifik bir formata zorluyoruz
        prompt = f"""Sen profesyonel bir kantitatif analistsin. Şu haberin: '{haber_basligi}' -> {enstruman_ismi} fiyatlarına olası etkisini analiz et.
        LÜTFEN SADECE AŞAĞIDAKİ FORMATTA YANIT VER (Başka hiçbir açıklama ekleme):
        ETKİ YÖNÜ (POZİTİF, NEGATİF veya NÖTR) | ETKİ YÜZDESİ (Sadece rakam, örn: 2.5) | 1 CÜMLELİK ÖZET
        Örnek: POZİTİF | 1.5 | Şirketin yeni yatırımı büyüme beklentilerini artırdı."""
        
        response = client.generate(model='gemma2:2b', prompt=prompt)
        return response.get('response', 'NÖTR | 0.0 | Analiz tamamlanamadı.').strip()
    except Exception as e:
        print(f"[AI Hatası]: {e}")
        return "NÖTR | 0.0 | AI motoruna ulaşılamadı."
def ai_teknik_analiz_yorumu(enstruman_ismi, anlik_fiyat, boga_fiyat, ayi_fiyat):
    try:
        from ollama import Client
        client = Client(host='http://localhost:11434')
        
        prompt = f"""Sen Wall Street seviyesinde profesyonel bir teknik analistsin. 
        {enstruman_ismi} şu an {anlik_fiyat} seviyesinden işlem görüyor. 
        Yapay zeka ve kantitatif algoritmalarımız bu varlık için önümüzdeki dönemde iyimser (boğa) hedefi {boga_fiyat:.2f}, kötümser (ayı) destek seviyesini ise {ayi_fiyat:.2f} olarak belirledi.
        Lütfen yatırımcılara bu durumu özetleyen, 2-3 cümlelik çok profesyonel ve teknik bir piyasa yorumu yap. Sadece yorum metnini ver, başlık vs. kullanma."""
        
        response = client.generate(model='gemma2:2b', prompt=prompt)
        return response.get('response', 'Teknik analiz şu an gerçekleştirilemiyor.').strip()
    except Exception as e:
        print(f"[AI Teknik Hata]: {e}")
        return "🤖 AI Yorum Motoru Çevrimdışı: Teknik analiz bağlantısı kurulamadı."
def ai_model_yorumu(model_adi, enstruman_ismi, anlik_fiyat, hedef_fiyat, vade):
    try:
        from ollama import Client
        client = Client(host='http://localhost:11434')
        
        prompt = f"""Sen profesyonel bir kantitatif analistsin.
        {enstruman_ismi} şu an {anlik_fiyat:.2f} seviyesinde. Bizim '{model_adi}' isimli algoritmamız, {vade} sonra fiyatın {hedef_fiyat:.2f} olacağını öngörüyor.
        Lütfen bu {model_adi} modelinin bu varlık için yaptığı öngörüyü yatırımcıya yorumla. 
        SADECE 2 cümlelik, çok teknik ve profesyonel bir açıklama yaz. Başlık veya giriş kullanma."""
        
        response = client.generate(model='gemma2:2b', prompt=prompt)
        return response.get('response', 'Analiz yapılamadı.').strip()
    except Exception as e:
        return "🤖 AI Yorum Motoru Çevrimdışı: Bağlantı kurulamadı."    
