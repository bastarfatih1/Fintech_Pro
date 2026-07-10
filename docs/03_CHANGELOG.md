# CHANGELOG

## 10 Temmuz 2026

### Tamamlananlar

- Streamlit Plotly parametre uyarısı düzeltildi.
- Dinamik model ağırlıkları arayüzde gösterildi.
- ARIMA ve Monte Carlo backtest sistemine alındı.
- Walk-forward stabilite skoru eklendi.
- Naive Last Price referans modeli eklendi.
- Referans modeli geçemeyen modellerin ağırlığı sıfırlandı.
- Backtest hatalarına göre kötümser, baz ve iyimser senaryolar üretildi.
- Senaryo bantları konsensüs grafiğine bağlandı.
- Görsel rotalar gerçek model tahminlerinden ayrıldı.
- Merkezi takvim standardı eklendi.
- Varlık türü sembolden otomatik belirlenir hâle getirildi.
- Kripto için 7/24 takvim günü standardı eklendi.
- Hisse ve döviz için hafta sonu hariç işlem günü standardı eklendi.
- Konsensüs grafiği merkezi takvim modülüne bağlandı.
- Tahmin motoru merkezi vade standardına bağlandı.
- Vade seçim ekranı varlık türüne göre açıklayıcı hâle getirildi.
- Boş placeholder dosyalar temizlendi.

### Son durum

Sprint 3.12 tamamlandı.

Uygulamada:

- BTC-USD gibi kripto sembolleri takvim günü kullanır.
- USDTRY=X gibi döviz sembolleri işlem günü kullanır.
- THYAO.IS gibi hisse sembolleri işlem günü kullanır.
- Vade seçiminde kaç gün kullanılacağı kullanıcıya gösterilir.

### Bilinen sınırlamalar

- Resmî borsa tatilleri henüz yok.
- Ülke/banka tatilleri henüz yok.
- Piyasa saatleri henüz yok.
- Lisanslı veri sağlayıcı entegrasyonu henüz yok.

### Sıradaki iş

Sprint 3.13 - Veri Kaynağı Katmanı ve Üretim Hazırlığı
