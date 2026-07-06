import requests
import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import requests
import pandas as pd
import streamlit as st
import yfinance as yf
from finans_motoru import hesapla_gecmis_performans, gelecek_senaryolari_hesapla
from haber_motoru import canli_rss_haber_cek, ai_etki_analizi

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Fintech Alpha Pro Final", layout="wide")
st.markdown("""
    <style>
    .metric-up { color: #00ff88; font-weight: bold; }
    .metric-down { color: #ff4d4d; font-weight: bold; }
    .kur-box { 
        background-color: #1c2541; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #3a506b;
        color: #ffffff !important; 
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ FinTech Alpha: Kurumsal Risk & Gelişmiş Kantitatif Projeksiyon")
st.markdown("---")

# --- 2. BÖLÜM: Global Parametreler ve Kur Çevirici ---
@st.cache_data(ttl=900)
def kurlari_getir_cache():
    # KÖKTEN ÇÖZÜM: Limit sınırı olmayan ve API Key istemeyen açık servis doğrudan app.py önbelleğine alındı.
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        response = requests.get(url, timeout=5).json()
        rates = response['rates']
        return {
            "USD": 1.0, 
            "TRY": float(rates.get('TRY', 34.20)), 
            "EUR": float(rates.get('EUR', 0.92)), 
            "CNY": float(rates.get('CNY', 7.25)),
            "RUB": float(rates.get('RUB', 88.0)), 
            "SAR": float(rates.get('SAR', 3.75)),
            "KWD": float(rates.get('KWD', 0.31)), 
            "JPY": float(rates.get('JPY', 155.0))
        }
    except:
        return {"USD": 1.0, "TRY": 34.20, "EUR": 0.92, "CNY": 7.25, "RUB": 88.0, "SAR": 3.75, "KWD": 0.31, "JPY": 155.0}

kurlar = kurlari_getir_cache()

col_g1, col_g2, col_g3 = st.columns([2, 1, 1])
ana_para = col_g1.number_input("Stratejik Yatırım Tutarı:", value=0.0, step=10000.0)
secilen_kur = col_g2.selectbox("Baz Para Birimi:", ["TRY", "USD", "EUR", "CNY", "RUB", "JPY", "SAR", "KWD"])

# BIST 100 (XU100.IS) Sisteme Eklendi!
enstrumanlar = {
    "BIST 100": "XU100.IS", 
    "Bitcoin (BTC)": "BTC-USD", 
    "Altın (Ons)": "GC=F", 
    "Gümüş (Ons)": "SI=F", 
    "S&P 500": "^GSPC"
}
secilen_varlik = col_g3.selectbox("Analiz Edilecek Varlık:", list(enstrumanlar.keys()))

sembol_sozluk = {"TRY": "₺", "USD": "$", "EUR": "€", "CNY": "¥", "RUB": "₽", "JPY": "¥", "SAR": "﷼", "KWD": "د.ك"}
s = sembol_sozluk[secilen_kur]
kur_val = kurlar.get(secilen_kur, 1.0)

usd_baz = ana_para / kurlar[secilen_kur] if ana_para > 0 else 0.0

st.write("💵 **Mevduatın Anlık Karşılığı:**")
k1, k2, k3, k4 = st.columns(4)
k5, k6, k7, k8 = st.columns(4)

def hesapla_ve_goster(col, bayrak, hedef_kod, birim):
    if hedef_kod in kurlar and secilen_kur in kurlar:
        tutar = (ana_para / kurlar[secilen_kur]) * kurlar[hedef_kod]
        col.markdown(f"<div class='kur-box'>{bayrak} {tutar:,.2f} {birim}</div>", unsafe_allow_html=True)
    else:
        col.markdown(f"<div class='kur-box'>{bayrak} N/A {birim}</div>", unsafe_allow_html=True)

hesapla_ve_goster(k1, "🇹🇷", "TRY", "TL")
hesapla_ve_goster(k2, "🇺🇸", "USD", "USD")
hesapla_ve_goster(k3, "🇪🇺", "EUR", "EUR")
hesapla_ve_goster(k4, "🇨🇳", "CNY", "CNY")
hesapla_ve_goster(k5, "🇷🇺", "RUB", "RUB")
hesapla_ve_goster(k6, "🇯🇵", "JPY", "JPY")
hesapla_ve_goster(k7, "🇸🇦", "SAR", "SAR")
hesapla_ve_goster(k8, "🇰🇼", "KWD", "KWD")

st.divider()

# --- 3. BÖLÜM: PİYASA KARTLARI (Gelişmiş & Hatasız) ---
def show_card(col, label, kur_key, yf_symbol=""):
    try:
        # HATA DÜZELTİLDİ: Canlı fonksiyon yerine yukarıdaki önbelleğe alınmış güvenli kurlar çağrılıyor.
        kurlar_kart = kurlari_getir_cache()
        usd_try = kurlar_kart.get("TRY", 34.20)
        
        if kur_key == "USD":
            val = usd_try
        else:
            hedef_usd_parite = kurlar_kart.get(kur_key, 1.0)
            # USD bazlı API verisi kusursuz çapraz kura çevriliyor (Örn: USD_TRY / EUR_USD)
            val = usd_try / hedef_usd_parite if hedef_usd_parite > 0 else 0.0
            
        # 2. YÜZDE KISMI
        pct_text = "▲ 0.00%"
        pct_color = "#00ff88"
        
        if yf_symbol:
            try:
                import yfinance as yf
                
                if yf_symbol in ["CNYTRY=X", "RUBTRY=X", "SARTRY=X", "KWDTRY=X"]:
                    hedef_kod = yf_symbol[:3]
                    
                    usd_try_data = yf.Ticker("USDTRY=X").history(period="5d")
                    usd_hedef_data = yf.Ticker(f"{hedef_kod}=X").history(period="5d")
                    
                    if len(usd_try_data) >= 2 and len(usd_hedef_data) >= 2:
                        prev_cross = usd_try_data['Close'].iloc[-2] / usd_hedef_data['Close'].iloc[-2]
                        curr_cross = usd_try_data['Close'].iloc[-1] / usd_hedef_data['Close'].iloc[-1]
                        
                        pct = ((curr_cross - prev_cross) / prev_cross) * 100
                        pct_color = "#00ff88" if pct >= 0 else "#ff4d4d"
                        pct_text = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.2f}%"
                        
                else:
                    data = yf.Ticker(yf_symbol).history(period="5d")
                    if len(data) >= 2:
                        prev = data['Close'].iloc[-2]
                        curr = data['Close'].iloc[-1]
                        
                        pct = ((curr - prev) / prev) * 100
                        pct_color = "#00ff88" if pct >= 0 else "#ff4d4d"
                        pct_text = f"{'▲' if pct >= 0 else '▼'} {abs(pct):.2f}%"
            except Exception:
                pass
                
        # 3. KARTI EKRANA BAS
        with col:
            with st.container(border=True):
                st.write(f"**{label}**")
                st.markdown(f"### {val:,.2f}")
                st.markdown(f"<span style='color: {pct_color}'>{pct_text}</span>", unsafe_allow_html=True)
                
    except Exception:
        pass

st.subheader("📊 Canlı Piyasa Göstergeleri")

r1_1, r1_2, r1_3 = st.columns(3)
show_card(r1_1, "USD/TRY", "USD", "") 
show_card(r1_2, "EUR/TRY", "EUR", "EURTRY=X")
show_card(r1_3, "Yuan (CNY)", "CNY", "CNYTRY=X")

r2_1, r2_2, r2_3 = st.columns(3)
show_card(r2_1, "Ruble (RUB)", "RUB", "RUBTRY=X")
show_card(r2_2, "Riyal (SAR)", "SAR", "SARTRY=X")
show_card(r2_3, "Dinar (KWD)", "KWD", "KWDTRY=X")

st.divider()

# --- 4. BÖLÜM: SEÇİLİ VARLIK ANALİZ ODASI ---
@st.cache_data(ttl=600)
def haberleri_getir_cache(kelime):
    return canli_rss_haber_cek(kelime)

sembol = enstrumanlar[secilen_varlik]
st.markdown(f"## 🎯 {secilen_varlik} Analiz Odası")

if st.button("🚀 Gelişmiş AI & Gelecek Projeksiyonunu Başlat", use_container_width=True, type="primary"):
    
    with st.spinner(f'{secilen_varlik} verileri ve yapay zeka modelleri senkronize ediliyor...'):
        ticker = yf.Ticker(sembol)
        data = ticker.history(period="10y")
        
        if data is not None and not data.empty:
            curr = float(data['Close'].iloc[-1])
            haberler = haberleri_getir_cache(secilen_varlik.split("(")[0])
            
            gelecek = gelecek_senaryolari_hesapla(data, curr, ana_para, kur_val, s, periyot_gun=1095)
            
            # ================= EKSTRA AI DOKUNUŞU: SENTIMENT INDIKATÖRÜ =================
            st.divider()
            st.subheader("🔮 Yapay Zeka Konsensüs Sinyali Odası")

            try:
                ham_getiri = gelecek["gelecek_df"].iloc[2]["Beklenen Getiri"]
                aylik_getiri_yuzde = float(str(ham_getiri).replace('%', '').strip())
            except (ValueError, KeyError, IndexError):
                aylik_getiri_yuzde = 0.0

            c1, c2 = st.columns([1, 3])
            with c1:
                if aylik_getiri_yuzde > 1.5:
                    st.success("🟢 AGRESİF BOĞA (YÜKSELİŞ)")
                elif aylik_getiri_yuzde < -1.5:
                    st.error("🔴 AYI SİNYALİ (DÜŞÜŞ)")
                else:
                    st.warning("🟡 YATAY / KARARSIZ PİYASA")
                    
            with c2:
                beklenen_getiri_str = gelecek['gelecek_df'].iloc[2]['Beklenen Getiri'] if 'gelecek_df' in gelecek else "%0.0"
                st.caption(
                    f"**AI Strateji Notu:** Modellerin ağırlıklı bileşkesi, varlığın önümüzdeki 30 gün içinde "
                    f"{beklenen_getiri_str} yönünde bir eğilim sergileyeceğini öngörüyor. "
                    f"Risk iştahınızı Monte Carlo alt-üst sınırlarına göre optimize etmeniz önerilir."
                )

            # ================= MİKRO GRAFİKLER VE AI YORUMLARI =================
            st.divider()
            st.markdown("### 🤖 Model Odası & Bağımsız Yapay Zeka Analizleri")
            st.caption("Aşağıda, konsensüsü oluşturan 6 temel algoritmanın **3 yıllık (1095 günlük)** bağımsız tahmin rotaları ve finansal çalışma prensipleri yer almaktadır.")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### ⚡ XGBoost Regressor (%25)")
                st.line_chart(gelecek["rotalar"]["xgboost"], height=120)
                st.info("**AI Yorumu:** Karar ağaçlarını gradyan artırma yöntemiyle eğiten bu model, piyasadaki doğrusal olmayan ani kırılmaları ve trend değişimlerini yakalamada en yüksek hassasiyete sahiptir.")

                st.markdown("#### 📈 ARIMA Modeli (%20)")
                st.line_chart(gelecek["rotalar"]["arima"], height=120)
                st.info("**AI Yorumu:** Saf istatistiksel zaman serisi algoritmasıdır. Geçmiş fiyat hareketlerindeki otokorelasyon ve trend durağanlığını inceleyerek momentumun korunduğu kararlı rotalar çizer.")

            with col2:
                st.markdown("#### 🎲 Monte Carlo Eğrisi (%15)")
                st.line_chart(gelecek["rotalar"]["monte_carlo"], height=120)
                st.info("**AI Yorumu:** Piyasaya 500 farklı paralel evrende rastgele yürüyüş (Random Walk) yaptırır. Varlık fiyatının matematiksel olarak yönelebileceği en olası ağırlıklı ortalama patikayı temsil eder.")

                st.markdown("#### 🌳 Random Forest (%15)")
                st.line_chart(gelecek["rotalar"]["random_forest"], height=120)
                st.info("**AI Yorumu:** Onlarca bağımsız karar ağacının ortak kararıyla tahmin üretir. Finansal verilerdeki gürültüleri (aşırı oynaklıkları) filtreleyerek daha dengeli ve tutarlı tahminler üretir.")

            with col3:
                st.markdown("#### 🧮 Linear Regression (%15)")
                st.line_chart(gelecek["rotalar"]["lin_reg"], height=120)
                st.info("**AI Yorumu:** Veri setinin genel yönüne kusursuz bir doğrusal çizgi oturtur. Piyasadaki spekülatif hareketlerden etkilenmeden, varlığın ana makro yönelimini (temel desteğini) hesaplar.")

                st.markdown("#### 🎯 Support Vector Machine (%10)")
                st.line_chart(gelecek["rotalar"]["svm"], height=120)
                st.info("**AI Yorumu:** Fiyat verilerini yüksek boyutlu bir düzleme taşıyarak marjinal sınır çizgileri oluşturur. Piyasanın aşırı alım ve aşırı satım noktalarındaki direnç eğilimlerini tespit eder.")

            # ================= BİLİMSEL DİPNOT AÇIKLAMASI =================
            st.divider()
            st.markdown(
                f"<div style='text-align: center; color: #888888; font-size: 13px; font-style: italic; padding: 10px; border-radius: 5px; background-color: #f9f9f9; border: 1px solid #eeeeee;'>"
                f"⚠️ Bu raporda yer alan veriler; <b>XGBoost, ARIMA, Monte Carlo, Random Forest, Linear Regression ve SVM</b> olmak üzere "
                f"<b>6 farklı ileri düzey yapay zeka ve ekonometrik modelin</b>, ilgili varlığa ait <b>2 yıllık (500 günlük)</b> derin finansal geçmiş verileriyle "
                f"bilimsel ve matematiksel olarak hesaplanmış ortak konsensüs projeksiyon tahminleridir. Kesinlikle yatırım tavsiyesi niteliği taşımaz."
                f"</div>", 
                unsafe_allow_html=True
            )
            
            st.divider()

            # ================= 3 ANA SEKME =================
            tab_gecmis, tab_gelecek, tab_haber = st.tabs(["📅 Geçmiş Performans", "🔮 Gelecek Projeksiyonu (AI)", "📰 Kurumsal Haber Akışı"])
            
            with tab_gecmis:
                col_tablo, col_grafik = st.columns([1, 2])
                with col_tablo:
                    st.markdown("### 📊 Gerçekleşen Getiriler")
                    df_tablo = hesapla_gecmis_performans(data, curr, ana_para, kur_val, s)
                    st.table(df_tablo)
                with col_grafik:
                    periyot_secimi = st.selectbox("📈 Grafik Görünümü:", ["1 Hafta", "1 Ay", "3 Ay", "6 Ay", "1 Yıl", "3 Yıl", "5 Yıl", "10 Yıl"], index=4)
                    gun_karsiligi = {"1 Hafta": 7, "1 Ay": 30, "3 Ay": 90, "6 Ay": 180, "1 Yıl": 365, "3 Yıl": 1095, "5 Yıl": 1825, "10 Yıl": 3650}
                    st.line_chart(data['Close'].tail(gun_karsiligi[periyot_secimi])) 

            with tab_gelecek:
                st.markdown("### 📊 Ana Projeksiyon ve Matris Merkezi")
                st.table(gelecek["gelecek_df"])
                
                st.markdown("### 📈 3 Yıllık Konsensüs Yol Haritası Grafiği")
                chart_data = pd.DataFrame({"Kolektif AI Rotaları": gelecek["konsensus_rota"]})
                st.line_chart(chart_data)
                
                st.markdown("### 🎲 3 Yıllık Uzun Vadeli Risk Senaryoları")
                g1, g2, g3 = st.columns(3)
                g1.metric("Boğa Senaryosu (+)", f"{gelecek['boga']:,.2f}", "İyimser (Monte Carlo)")
                g2.metric("Baz Senaryo (Nötr)", f"{gelecek['baz']:,.2f}", "Yatay İhtimal")
                g3.metric("Ayı Senaryosu (-)", f"{gelecek['ayi']:,.2f}", "Kötümser Risk")
                st.caption("Not: Uzun vadeli tahminler Yapay Zeka algoritmaları ile, riskler Monte Carlo (500 İhtimal) ile hesaplanmıştır.")

            with tab_haber:
                for h in haberler:
                    with st.container(border=True):
                        st.markdown(f"**{h['title']}**")
                        st.markdown(f"🗞️ {h['media']} | 🕒 {h['date']}")
                        st.link_button("🔗 Haberi Sayfasında Oku", h['link'])
                        with st.expander("🤖 AI Etki Analizi"):
                            ai_sonuc = ai_etki_analizi(h['title'], secilen_varlik)
                            st.success(ai_sonuc)
        else:
            st.error(f"⚠️ {secilen_varlik} için veri çekilemedi. Lütfen daha sonra tekrar deneyin.")