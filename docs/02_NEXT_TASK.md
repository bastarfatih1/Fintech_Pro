# NEXT TASK

## Sprint 3.12 - Varlık Türüne Göre Takvim ve Vade Standardı

### Amaç

Hisse senedi, kripto, döviz ve diğer yatırım araçlarının farklı işlem takvimlerini doğru şekilde yönetmek.

### İlk küçük adım

1. Varlık türü alanını standardize et.
2. Hisse senedi için işlem günü takvimi kullan.
3. Kripto için haftanın 7 günü takvim kullan.
4. Döviz için hafta sonlarını hariç tut.
5. Grafik tarihlerini varlık türüne göre üret.
6. Vade etiketlerini aynı merkezi yardımcı fonksiyondan al.
7. Mevcut uygulamayı bozmadan geriye uyumluluğu koru.

### Sonraki alt adımlar

- BIST tatil takvimi
- ABD borsaları tatil takvimi
- Londra Borsası tatil takvimi
- Piyasa saatleri ve zaman dilimi
- Varlık bazlı veri gecikme etiketi

### Kabul kriterleri

- Kripto grafiği hafta sonlarını atlamaz.
- Hisse senedi grafiği hafta sonlarını atlar.
- Vade sayıları merkezi yapıdan gelir.
- Aynı vade motor ve arayüzde farklı hesaplanmaz.
- Mevcut tahmin ve backtest testleri çalışmaya devam eder.
