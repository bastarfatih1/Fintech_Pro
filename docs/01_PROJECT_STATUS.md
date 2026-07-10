# PROJECT STATUS

Son güncelleme: 10 Temmuz 2026

## Aktif çalışma düzeni

PLAN -> IMPLEMENT -> TEST -> COMMIT -> DEPLOY/DEMO

## Tamamlanan sprintler

### Mimari ve arayüz

- Sprint 2.9 - Profesyonel fiyat grafiği
- Sprint 2.10 - RSI modülü
- Sprint 2.11 - Konsensüs grafiği
- Sprint 2.12 - Haber paneli
- Sprint 2.13 - Performans paneli
- Sprint 2.14 - Analiz paneli
- Sprint 2.15 - Konsensüs paneli
- Sprint 2.16 - Girdi paneli
- Sprint 2.17 - Oturum ve ilerleme yönetimi
- Sprint 2.18 - Ana giriş dosyasının sadeleştirilmesi
- Sprint 2.19 - Mimari doğrulama

### Tahmin ve backtest

- Sprint 3.1 - Tahmin yolu stabilizasyonu ve risk metrikleri
- Sprint 3.2 - Güvenli kur API yapılandırması
- Sprint 3.3 - Model hatalarının takip edilmesi
- Sprint 3.4 - Model durumlarının gösterimi
- Sprint 3.5 - Kronolojik backtest
- Sprint 3.6 - Backtest sonuç ekranı
- Sprint 3.7 - Dinamik model ağırlıkları
- Sprint 3.8 - Ağırlıkların arayüzde gösterimi
- Sprint 3.9 - ARIMA ve Monte Carlo backtesti
- Sprint 3.10 - Walk-forward stabilite skoru
- Sprint 3.11A - Naive referans model ve gerçekçilik koruması
- Sprint 3.11B - Kalibre senaryo güven bantları
- Sprint 3.11C - Senaryo bantlarının arayüzde gösterimi

## Mevcut teknik durum

Uygulama artık:

- Referans modeli geçemeyen modellere ağırlık vermiyor.
- Kötümser, baz ve iyimser senaryolar üretiyor.
- Backtest hatalarıyla kalibre güven bandı hesaplıyor.
- Görsel rotaları gerçek günlük tahminlerden ayırıyor.
- Hisse senedi vadelerinde işlem günü mantığı kullanıyor.
- Model stabilitesi, RMSE, yön doğruluğu ve ağırlıkları gösteriyor.

## Bilinen sınırlamalar

- Tüm varlık türleri aynı takvim mantığını kullanıyor.
- Kripto için 7/24 takvim desteği henüz yok.
- ABD, BIST ve Londra borsalarının resmi tatil takvimleri bağlı değil.
- Üretim veri kaynakları henüz lisanslı sağlayıcılarla değiştirilmedi.
- Ticari yayın durumu halen NO-GO.

## Sıradaki sprint

Sprint 3.12 - Varlık Türüne Göre Takvim ve Vade Standardı
