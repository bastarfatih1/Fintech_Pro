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
- Sprint 3.12A - Varlık türüne göre merkezi takvim standardı
- Sprint 3.12B - Vade seçim ekranının takvim standardına bağlanması

## Mevcut teknik durum

Uygulama artık:

- Referans modeli geçemeyen modellere ağırlık vermiyor.
- Kötümser, baz ve iyimser senaryolar üretiyor.
- Backtest hatalarıyla kalibre güven bandı hesaplıyor.
- Görsel rotaları gerçek günlük tahminlerden ayırıyor.
- Model stabilitesi, RMSE, yön doğruluğu ve ağırlıkları gösteriyor.
- Varlık türünü sembolden otomatik belirliyor.
- Kripto için takvim günü standardı kullanıyor.
- Hisse senedi ve döviz için hafta sonu hariç işlem günü standardı kullanıyor.
- Tahmin motoru, konsensüs grafiği ve vade seçim paneli aynı merkezi takvim modülünü kullanıyor.
- Vade seçim ekranında kaç işlem günü veya takvim günü kullanılacağı açıkça gösteriliyor.

## Merkezi takvim standardı

Dosya:

```text
core/market_calendar.py
```

Mevcut davranış:

- Kripto: 7/24 takvim günü
- Hisse senedi / endeks: hafta sonu hariç işlem günü
- Döviz: hafta sonu hariç işlem günü
- Diğer varlıklar: güvenli varsayılan olarak hafta sonu hariç işlem günü

Örnekler:

- BTC-USD -> crypto -> 1 ay = 30 takvim günü
- USDTRY=X -> fx -> 1 ay = 21 işlem günü
- THYAO.IS -> stock -> 1 ay = 21 işlem günü

## Bilinen sınırlamalar

- BIST, ABD ve Londra resmî borsa tatilleri henüz takvime bağlı değil.
- Döviz için ülke ve banka tatilleri henüz takvime bağlı değil.
- Piyasa saatleri ve zaman dilimi bazlı açık/kapalı bilgisi henüz yok.
- Üretim veri kaynakları henüz lisanslı sağlayıcılarla değiştirilmedi.
- Ticari yayın durumu halen NO-GO.

## Sıradaki sprint

Sprint 3.13 - Veri Kaynağı Katmanı ve Üretim Hazırlığı
