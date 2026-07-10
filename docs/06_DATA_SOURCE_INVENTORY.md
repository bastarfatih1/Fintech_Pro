# DATA SOURCE INVENTORY

Son güncelleme: 10 Temmuz 2026

## Amaç

Bu belge, Fintech_Pro2 uygulamasında kullanılan mevcut veri kaynaklarını, cache sürelerini, lisans durumunu ve üretim öncesi yapılması gereken kontrolleri takip etmek için oluşturulmuştur.

Bu belge teknik envanterdir. Ticari yayın için hukuki/lisans incelemesinin yerine geçmez.

## Özet durum

| Veri alanı | Mevcut kaynak | Dosya / Fonksiyon | Cache | Üretim durumu |
|---|---|---|---:|---|
| Piyasa fiyat geçmişi | yfinance / Yahoo Finance | `services/cache_service.py` -> `services/data_provider.py` / `get_cached_asset_history()` | 1 saat | Prototip |
| S&P 500 beta verisi | yfinance / Yahoo Finance | `finans_motoru.py` -> `services/data_provider.py` / `get_sp500_data()` | Yok | Prototip |
| Döviz kurları | ExchangeRate-API | `finans_motoru.py` / `get_kurlar()` | 15 dk | API key ile |
| Haberler | Google News RSS | `haber_motoru.py` / `canli_rss_haber_cek()` | 10 dk + fonksiyon içi 1 saat | Prototip |
| AI teknik yorum | Local Ollama | `haber_motoru.py` / `ollama_ai_cagir()` | 1 saat | Yerel servis |
| AI haber etki analizi | Local Ollama | `haber_motoru.py` / `ai_etki_analizi()` | 1 saat | Yerel servis |

## Mevcut veri akışı

```text
app.py
  ├─ get_cached_asset_history()
  │    └─ services.data_provider.get_market_history()
  │         └─ YahooFinancePrototypeProvider
  │              └─ yfinance / Yahoo Finance geçmiş OHLCV verisi
  │
  ├─ get_cached_asset_history_with_metadata()
  │    └─ veri + kaynak/lisans metadata bilgisi
  │
  ├─ get_cached_currencies()
  │    └─ finans_motoru.get_kurlar()
  │         └─ ExchangeRate-API veya fallback kur tablosu
  │
  └─ get_cached_news()
       └─ haber_motoru.canli_rss_haber_cek()
            └─ Google News RSS
```

Beta hesabı için ayrıca:

```text
finans_motoru.py
  └─ get_sp500_data()
       └─ services.data_provider.get_market_history()
            └─ YahooFinancePrototypeProvider
                 └─ yfinance ^GSPC kapanış verisi
```

AI yorumları için ayrıca:

```text
haber_motoru.py
  └─ ollama_ai_cagir()
       └─ http://localhost:11434/api/generate
```

## Kaynak bazlı notlar

### 1. Piyasa fiyat geçmişi

Mevcut kaynak:

```text
yfinance / Yahoo Finance
```

Kullanıldığı yer:

```text
services/cache_service.py
get_cached_asset_history(symbol, period="10y")

services/data_provider.py
get_market_history(symbol, period, asset_type)
YahooFinancePrototypeProvider
```

Mevcut görev:

- Seçilen varlığın geçmiş OHLCV verisini indirir.
- Streamlit cache ile 1 saat saklanır.
- Model eğitimleri, grafikler, performans ve risk metrikleri bu veriye dayanır.
- Veri kaynağı metadata bilgisi artık provider katmanında üretilir.

Risk:

- Prototip için uygundur.
- Ticari kullanım için veri lisansı net değildir.
- Üretim öncesi lisanslı veri sağlayıcı veya açıkça izinli veri kaynağı gerekir.

Karar:

```text
Üretim için NO-GO.
Demo / geliştirme için kontrollü kullanılabilir.
Provider katmanına bağlandı.
```

### 2. S&P 500 beta verisi

Mevcut kaynak:

```text
yfinance ^GSPC
```

Kullanıldığı yer:

```text
finans_motoru.py
get_sp500_data(start_date, end_date)

services/data_provider.py
get_market_history(symbol="^GSPC", asset_type="index", start_date, end_date)
YahooFinancePrototypeProvider
```

Mevcut görev:

- Beta hesabı için S&P 500 kapanış verisi getirir.
- Veri çağrısı artık doğrudan `finans_motoru.py` içinden yapılmaz.
- S&P 500 verisi provider katmanı üzerinden alınır.
- İleride lisanslı endeks sağlayıcısına geçiş tek provider katmanından yapılabilir.

Risk:

- Ana fiyat verisiyle aynı lisans ve süreklilik risklerini taşır.
- Provider katmanına taşındı ancak kullanılan kaynak hâlâ prototip yfinance kaynağıdır.
- Ticari yayın için lisans kontrolü hâlâ gereklidir.

Karar:

```text
Provider katmanına taşındı.
Üretim için NO-GO.
Demo / geliştirme için kontrollü kullanılabilir.
```

### 3. Döviz kurları

Mevcut kaynak:

```text
ExchangeRate-API
```

Kullanıldığı yer:

```text
finans_motoru.py
get_kurlar()
```

Mevcut görev:

- USD bazlı güncel döviz kurlarını alır.
- API anahtarı yoksa fallback sabit kur tablosu kullanır.
- Cache süresi `services/cache_service.py` içinde 15 dakikadır.

Risk:

- Fallback kur değerleri güncel piyasa verisi değildir.
- Kullanıcıya fallback kullanıldığı açıkça gösterilmiyor.
- Ticari sürümde sağlayıcı planı, limitler ve lisans kontrolü gerekir.

Karar:

```text
Fallback kullanımı arayüzde kaynak etiketiyle gösterilmeli.
```

### 4. Haber verisi

Mevcut kaynak:

```text
Google News RSS
```

Kullanıldığı yer:

```text
haber_motoru.py
canli_rss_haber_cek(arama_kelimesi)
```

Mevcut görev:

- Varlık adı + finance kelimesiyle RSS araması yapar.
- İlk 6 haberi listeler.

Risk:

- RSS sonuçlarının sürekliliği garanti değildir.
- Ticari kullanım ve gösterim koşulları ayrıca incelenmelidir.
- Haber kaynağı güvenilirlik ve tekrar kontrolü yoktur.

Karar:

```text
Prototip için kullanılabilir.
Üretimde haber sağlayıcı/lisans kontrolü gerekir.
```

### 5. Local Ollama AI yorumları

Mevcut kaynak:

```text
http://localhost:11434/api/generate
```

Kullanıldığı yer:

```text
haber_motoru.py
ollama_ai_cagir()
ai_teknik_analiz_yorumu()
ai_etki_analizi()
ai_toplu_model_yorumlari()
```

Mevcut görev:

- Teknik yorum üretir.
- Haber etki analizi üretir.
- Model yorumları üretir.
- Yanıt gelmezse fallback metinleri kullanır.

Risk:

- Kullanıcının bilgisayarında Ollama çalışmıyorsa fallback devreye girer.
- Model adı `st.session_state` içinden okunur.
- Üretim ortamında local servis mimarisi doğrudan çalışmayabilir.

Karar:

```text
Demo için uygun.
Üretimde AI servis mimarisi ayrıca tasarlanmalı.
```

## Merkezi veri sağlayıcı hedef mimarisi

Hedef yapı:

```text
app.py
  ↓
services/cache_service.py
  ↓
services/data_provider.py
  ↓
providers/
  ├─ yahoo_provider.py
  ├─ licensed_bist_provider.py
  ├─ global_equity_provider.py
  ├─ crypto_provider.py
  └─ fx_provider.py
```

Her veri sonucu şu metadataları taşımalıdır:

```text
source_name
provider_type
asset_type
symbol
retrieved_at
data_delay
license_status
is_production_allowed
fallback_used
```

## Üretim öncesi veri kapıları

Ticari yayın öncesi şu kapılar kapanmadan üretime çıkılmamalıdır:

1. Piyasa verisi lisans kontrolü
2. Haber verisi kullanım koşulları kontrolü
3. Döviz verisi sağlayıcı plan ve limit kontrolü
4. AI servis sağlayıcı ve veri işleme kontrolü
5. Kaynak ve gecikme etiketlerinin arayüzde gösterimi
6. Veri hatalarında kullanıcı dostu hata mesajları
7. Demo/prototip modu ile üretim modu ayrımı

## Sprint 3.13 tamamlanan alt adımlar

### Sprint 3.13B

Veri sağlayıcı arayüzü taslağı eklendi:

```text
MarketDataResult
MarketDataProvider
DataSourceMetadata
YahooFinancePrototypeProvider
```

### Sprint 3.13C

`get_cached_asset_history()` fonksiyonu provider katmanına bağlandı.

### Sprint 3.13D

Arayüzde veri kaynağı, lisans durumu, prototip etiketi ve üretime uygunluk bilgisi gösterildi.

### Sprint 3.13E

S&P 500 beta verisi provider katmanına taşındı.

## Sprint 3.13 sonraki adımlar

### Sprint 3.13G

Döviz kuru sonucuna metadata ekleme.

### Sprint 3.13H

Haber verisi sonucuna kaynak ve lisans etiketi ekleme.

### Sprint 3.13I

Demo modu / üretim modu ayrımını konfigürasyona bağlama.

## Genel karar

Mevcut veri kaynakları geliştirme ve demo için kullanılabilir.

Ancak ticari sürüm için durum:

```text
NO-GO
```

Ticari yayına çıkmadan önce lisanslı veya açıkça izinli veri kaynaklarıyla provider katmanı tamamlanmalıdır.