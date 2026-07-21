# Sprint 3.28 - Hiyerarşik Varlık Seçim Sistemi

Bu sprint tek listeyi üç kademeli seçime dönüştürür:

1. Varlık Sınıfı
2. Piyasa / Grup
3. Alt Varlık

Örnek:

Hisse Senetleri → BIST 30 → Tüpraş → `TUPRS.IS`

Seçilen sembol mevcut analiz motoruna `market_symbol` olarak gider. Bu sayede grafikler, risk metrikleri, senaryo analizi, AI yorumları ve geçmiş performans ekranları aynı akışla çalışır.

## Notlar

- BIST listeleri prototip başlangıç listesidir.
- Endeks bileşenleri dönemsel değişebilir; ticari sürümde sağlayıcıdan dinamik sembol listesi alınmalıdır.
- Gram Altın canlı teorik formülle çalışır: XAU/USD × USD/TRY / 31.1034768.
- Çeyrek, tam, cumhuriyet ve 22 ayar gibi ürünler prototipte teorik altın katsayılarıyla geliştirilmeye hazır semboller olarak eklendi.
