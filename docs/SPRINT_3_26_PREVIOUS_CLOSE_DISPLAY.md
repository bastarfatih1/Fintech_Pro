# Sprint 3.26 - Önceki Kapanış Gösterimi

Bu patch `components/landing_panel.py` dosyasını günceller.

## Ne değişti?

- Güncel fiyat kartına önceki kapanış eklendi.
- Günlük değişim yüzde ve TL olarak gösterilir.
- Gram Altın Matriks manuel override katmanında son satırın `Open` değeri önceki kapanış olarak kullanılır.
- `use_container_width=True` uyarısı için `width="stretch"` kullanıldı.

## Beklenen görünüm

Gram Altın kartında:

- Güncel Fiyat: Matriks son fiyatı
- Önceki kapanış: Matriks önceki kapanış fiyatı
- Günlük değişim: yüzde ve TL fark

