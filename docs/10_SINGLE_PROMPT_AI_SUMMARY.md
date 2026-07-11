# Sprint 3.19B - Single Prompt AI Summary

Bu sprintin amacı:

- Teknik analiz özeti
- Piyasa sentezi
- Risk notu
- Haberlerin genel etkisi
- Haber bazlı duyarlılık sonuçları

hepsini tek AI isteğinde üretmektir.

## Neden?

Önceki sistemde her haber için ayrı AI çağrısı yapılabiliyordu.
Bu, yayın modunda kota ve hız sorunları yaratır.

Yeni akış:

1 analiz çalıştırma = 1 AI isteği

## UI etkisi

- Haber panelinde her haberin altında AI yorumu görünür.
- Genel analiz paneline "Haber Etkisi" bloğu eklenir.
- Analiz sentezi AI bundle içinden gelir.
- AI çalışmazsa fallback metinler uygulamayı bozmaz.

## Güvenli dil

Al / sat / tut gibi yatırım tavsiyesi algısı veren ifadeler kullanılmaz.
