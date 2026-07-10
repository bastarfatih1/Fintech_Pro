# NEXT TASK

## Sprint 3.13 - Veri Kaynağı Katmanı ve Üretim Hazırlığı

### Amaç

Mevcut uygulamadaki veri akışını daha profesyonel, değiştirilebilir ve üretime hazırlanabilir hâle getirmek.

Bu sprintte amaç hemen ücretli veri sağlayıcıya geçmek değildir. Ama sistem, ileride lisanslı sağlayıcı eklenebilecek şekilde hazırlanacaktır.

### Neden gerekli?

Şu anda uygulama çalışıyor ancak veri kaynağı tarafı hâlâ prototip seviyesinde.

Üretime yaklaşmak için:

1. Veri sağlayıcı mantığı tek yerde toplanmalı.
2. Yahoo/yfinance kullanım alanı açıkça prototip olarak etiketlenmeli.
3. İleride BIST, global hisse, kripto ve döviz sağlayıcıları kolay değiştirilebilir olmalı.
4. Her veri sonucunda kaynak ve gecikme bilgisi taşınmalı.
5. Ticari sürüm öncesi lisans kontrol kapısı korunmalı.

### İlk küçük adım

Sprint 3.13A - Veri kaynağı durum envanteri

1. Mevcut veri çağrılarının nerede yapıldığını bul.
2. yfinance kullanılan dosyaları listele.
3. Döviz API çağrısının nerede olduğunu listele.
4. Haber verisi akışını listele.
5. Cache katmanının hangi verileri sakladığını çıkar.
6. Veri kaynağı notlarını belgeye ekle.

### Sonraki alt adımlar

- Veri sağlayıcı arayüzü taslağı
- Piyasa türüne göre provider seçimi
- Kaynak / gecikme / lisans etiketi
- Demo ve üretim veri modu ayrımı
- Lisanslı sağlayıcı entegrasyon kapısı
- Veri kaynağı hata mesajlarının kullanıcı dostu hâle getirilmesi

### Kabul kriterleri

- Veri çağrılarının nerede olduğu belgelenmiş olacak.
- Prototip veri kaynağı ile üretim veri kaynağı ayrımı netleşecek.
- Mevcut çalışan uygulama bozulmayacak.
- Henüz ücretli veri sağlayıcı zorunlu tutulmayacak.
- Ticari yayın için lisans kontrolü açık kalacak.

### Şu an tamamlanan önceki sprint

Sprint 3.12 tamamlandı:

- Varlık türüne göre merkezi takvim standardı eklendi.
- Kripto için takvim günü standardı kullanıldı.
- Hisse ve döviz için işlem günü standardı kullanıldı.
- Vade seçim ekranı bu takvim standardına bağlandı.
- Tahmin motoru, grafik ve giriş paneli aynı merkezi sistemi kullanır hâle geldi.
