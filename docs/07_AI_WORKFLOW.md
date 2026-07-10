# AI WORKFLOW

Son güncelleme: 11 Temmuz 2026

## Amaç

Bu belge, Fintech_Pro2 projesinde farklı yapay zekâ araçlarının güçlü yönlerine göre nasıl kullanılacağını tanımlar.

Hedef:

- Çalışan uygulamayı bozmadan geliştirmek
- Her zaman küçük ve geri alınabilir sprintlerle ilerlemek
- Kod, tasarım, araştırma, lisans ve test işlerini doğru araçlara bölmek
- Tek bir AI çıktısına körü körüne güvenmemek
- Nihai kararları merkezi bir kontrol süzgecinden geçirmek

Bu belge bir ürün geliştirme çalışma düzenidir.

---

## Ana prensip

Fintech_Pro2 için temel çalışma düzeni:

```text
PLAN -> IMPLEMENT -> TEST -> REVIEW -> COMMIT -> DEMO
```

Her sprintte şu kural korunur:

```text
Önce çalışan uygulama
Sonra küçük değişiklik
Sonra test
Sonra commit
```

Büyük ve dağınık değişiklik yapılmaz.

---

## Ana karar mekanizması

Projede ana karar merkezi:

```text
ChatGPT = Ana mimar / sprint yöneticisi / kalite kontrol
```

Diğer AI araçları yardımcı ekip gibi kullanılacaktır.

Hiçbir AI çıktısı doğrudan üretime alınmaz.

Her çıktı şu süzgeçten geçer:

```text
1. Proje mimarisine uyuyor mu?
2. Çalışan uygulamayı bozuyor mu?
3. Finansal hesap mantığını değiştiriyor mu?
4. Lisans / SPK / hukuki risk oluşturuyor mu?
5. Test edilebilir mi?
6. Geri alınabilir mi?
```

---

## AI araçlarının görev dağılımı

## 1. ChatGPT

### Rol

Ana orkestratör.

### Kullanım alanı

- Sprint planlama
- Mimari kararlar
- Kod değişiklik stratejisi
- Finansal model mantığı
- Backtest değerlendirmesi
- Veri sağlayıcı mimarisi
- Güvenlik / lisans / SPK sınırı
- Prompt tasarımı
- Diğer AI çıktılarının kontrolü
- Commit öncesi kalite kontrol

### ChatGPT'ye verilecek görev örnekleri

```text
Bu sprint için plan çıkar.
Bu kod değişikliği mimariyi bozar mı?
Bu model mantığı gerçekçi mi?
Bu provider yapısı üretime uygun mu?
Bu AI çıktısını denetle.
Bu dosyaları bozmadan güncelle.
```

### ChatGPT'nin sorumluluğu

```text
Son teknik karar
Son ürün kararı
Son kalite kontrol
```

---

## 2. Claude

### Rol

Dil, anlatım, kullanıcı deneyimi ve rapor kalitesi uzmanı.

### Kullanım alanı

- Premium arayüz metinleri
- Kullanıcıya gösterilecek açıklamalar
- Rapor dili
- Onboarding metinleri
- Hata mesajlarını yumuşatma
- Yatırım tavsiyesi gibi algılanabilecek ifadeleri azaltma
- Hukuki/etik dilin sadeleştirilmesi
- Pazarlama metni taslağı

### Claude'a verilecek görev örnekleri

```text
Bu analiz özetini daha premium ve güven veren bir dille yaz.
Bu uyarıyı kullanıcıyı korkutmadan açıkla.
Bu raporu yatırım tavsiyesi gibi görünmeyecek şekilde düzenle.
Bu onboarding ekranını daha anlaşılır hale getir.
```

### Claude çıktısı doğrudan kullanılmaz

Claude metni şu kontrolden geçer:

```text
1. Fazla iddialı mı?
2. Yatırım tavsiyesi gibi mi?
3. Kullanıcıyı yanıltıyor mu?
4. Teknik gerçeklikle uyumlu mu?
```

---

## 3. Gemini

### Rol

Araştırma, hızlı karşılaştırma ve geniş bağlam taraması.

### Kullanım alanı

- Veri sağlayıcı alternatifleri
- Global piyasa veri API karşılaştırmaları
- Teknik ürün araştırması
- Rakip uygulama özellikleri
- Yeni model / kütüphane taraması
- Güncel teknoloji ekosistemi incelemesi

### Gemini'ye verilecek görev örnekleri

```text
BIST verisi sağlayabilecek veri sağlayıcıları karşılaştır.
Finansal analiz uygulamalarında en iyi dashboard özellikleri neler?
Küçük ekipler için uygun veri sağlayıcı modellerini çıkar.
```

### Dikkat

Gemini çıktıları güncel olabilir ama yine de doğrulanmalıdır.

Özellikle:

```text
Fiyat
Lisans
Ticari kullanım hakkı
Veri kapsamı
API limiti
```

bilgileri ayrıca kontrol edilmelidir.

---

## 4. Perplexity

### Rol

Kaynaklı araştırma ve alıntılanabilir bilgi toplama.

### Kullanım alanı

- Veri lisansı araştırması
- Yasal koşullar
- API kullanım şartları
- Rakip ürün incelemesi
- Pazar araştırması
- Resmi belge / kaynak bulma
- SPK ve finansal regülasyon araştırması

### Perplexity'ye verilecek görev örnekleri

```text
Yahoo Finance verisinin ticari kullanım koşullarını kaynaklarıyla araştır.
BIST verisi için lisanslı sağlayıcı alternatiflerini kaynaklarıyla listele.
Türkiye'de yatırım danışmanlığı sınırlarını resmi kaynaklara göre özetle.
```

### Zorunlu kontrol

Perplexity çıktısı geldiğinde:

```text
1. Kaynak var mı?
2. Kaynak resmi mi?
3. Tarih güncel mi?
4. Sonuç bizim kullanım senaryomuza uyuyor mu?
```

---

## 5. Cursor / Windsurf

### Rol

Kod düzenleme ve refactor uygulama ortamı.

### Kullanım alanı

- Dosya içi kod düzenleme
- Küçük refactor
- Import temizliği
- Modül taşıma
- Tekrarlı kod azaltma
- Test komutlarını çalıştırma
- Hızlı kod gezintisi

### Cursor/Windsurf'e verilecek görev örnekleri

```text
Sadece bu dosyada şu fonksiyonu düzenle.
Bu importları temizle.
Bu fonksiyonu iki küçük yardımcı fonksiyona böl.
Hiçbir davranışı değiştirmeden isimlendirmeyi düzelt.
```

### Yasaklar

Cursor/Windsurf ile şu işler doğrudan yapılmaz:

```text
Büyük mimari değişiklik
Tüm projeyi yeniden yazma
Finansal model mantığını değiştirme
Lisans / güvenlik kararı verme
Çalışan sistemi test etmeden commit
```

---

## 6. Notebook / Python

### Rol

Matematiksel doğrulama ve deney ortamı.

### Kullanım alanı

- Model testleri
- Backtest karşılaştırması
- RMSE / MAE / yön doğruluğu kontrolü
- Monte Carlo simülasyon doğrulaması
- Portföy optimizasyon denemeleri
- Veri temizleme denemeleri
- Grafik prototipleri

### Notebook/Python görev örnekleri

```text
Bu iki modelin RMSE sonuçlarını karşılaştır.
Monte Carlo bandı çok geniş mi kontrol et.
Naive benchmark'a göre iyileşme var mı?
Bu risk metrikleri mantıklı mı?
```

### Kural

Notebook'ta başarılı olan şey doğrudan uygulamaya taşınmaz.

Önce:

```text
Deney -> Sonuç -> Küçük sprint -> Kod -> Test -> Commit
```

---

## İş türüne göre doğru AI seçimi

| İş türü | Birincil AI | İkincil AI | Son kontrol |
|---|---|---|---|
| Mimari karar | ChatGPT | Cursor | ChatGPT |
| Kod yazma | Cursor/Windsurf | ChatGPT | ChatGPT |
| Kod denetimi | ChatGPT | Cursor | ChatGPT |
| Premium metin | Claude | ChatGPT | ChatGPT |
| Veri sağlayıcı araştırması | Perplexity | Gemini | ChatGPT |
| Pazar araştırması | Perplexity | Gemini | ChatGPT |
| Finansal model doğrulama | Notebook/Python | ChatGPT | ChatGPT |
| Hukuki/lisans araştırması | Perplexity | ChatGPT | Uzman kontrolü |
| UI metinleri | Claude | ChatGPT | ChatGPT |
| Rapor üretimi | Claude | ChatGPT | ChatGPT |
| Backtest analizi | Notebook/Python | ChatGPT | ChatGPT |
| Sprint planı | ChatGPT | - | ChatGPT |

---

## Standart sprint akışı

Her sprint şu formatla yürütülür:

```text
1. Sprint adı
2. Amaç
3. Değişecek dosyalar
4. Risk seviyesi
5. AI görev dağılımı
6. Uygulama
7. Test
8. Commit
9. Sonraki adım
```

Örnek:

```text
Sprint 3.16 - Rapor Üretim Modülü

Amaç:
Analiz sonucunu PDF/HTML rapora dönüştürmek.

AI görev dağılımı:
ChatGPT: Mimari ve kod planı
Claude: Rapor dili
Cursor: Kod uygulama
Notebook: Sayısal doğrulama
Perplexity: Raporlardaki hukuki ifade kontrolü

Test:
python -m py_compile ...
streamlit run app.py

Commit:
Sprint 3.16 - Add analysis report module
```

---

## Standart prompt şablonları

## 1. ChatGPT sprint plan promptu

```text
Fintech_Pro2 projesinde şu sprinti planla:

Sprint adı:
Amaç:
Mevcut durum:
Değişecek dosyalar:
Bozulmaması gerekenler:
Kabul kriterleri:

PLAN -> IMPLEMENT -> TEST -> COMMIT formatında ilerle.
Çalışan uygulamayı bozma.
Küçük ve geri alınabilir adım öner.
```

## 2. Claude kullanıcı metni promptu

```text
Aşağıdaki metni finansal analiz uygulaması için daha premium, sade ve güven veren hale getir.

Kurallar:
- Yatırım tavsiyesi gibi görünmesin.
- Abartılı kazanç vaadi olmasın.
- Kullanıcıya güven versin.
- Kısa ve profesyonel olsun.

Metin:
...
```

## 3. Perplexity araştırma promptu

```text
Aşağıdaki konuda kaynaklı araştırma yap:

Konu:
Kullanım senaryosu:
Ülke / pazar:
Önemli sorular:

Lütfen resmi kaynakları, kullanım koşullarını, tarihleri ve riskleri belirt.
Ticari kullanım açısından netleştir.
```

## 4. Gemini karşılaştırma promptu

```text
Aşağıdaki seçenekleri ürün geliştirme açısından karşılaştır:

Seçenekler:
Kriterler:
Bütçe:
Teknik kısıtlar:

Tablo halinde güçlü/zayıf yönleri çıkar.
Küçük ekip için en mantıklı yolu öner.
```

## 5. Cursor/Windsurf kod promptu

```text
Sadece şu dosyada değişiklik yap:

Dosya:
Amaç:
Değiştirilecek fonksiyon:
Korunacak davranış:
Test komutu:

Büyük refactor yapma.
Başka dosyaya dokunma.
Çalışan uygulamayı bozma.
```

---

## Kalite kapıları

Bir sprint commit edilmeden önce şu kapılardan geçmelidir:

```text
1. Python compile testi geçti mi?
2. Streamlit uygulaması açıldı mı?
3. Ana analiz akışı çalıştı mı?
4. Veri gelmeyince hata yönetimi düzgün mü?
5. UI kullanıcıyı yanıltıyor mu?
6. Yatırım tavsiyesi gibi görünen ifade var mı?
7. Lisans / veri kaynağı riski arttı mı?
8. Git status temiz mi?
```

Komutlar:

```bash
python -m py_compile app.py
streamlit run app.py
git status --short
```

Değişen dosyalara göre compile komutu genişletilir.

---

## Risk seviyesine göre çalışma modu

## Düşük risk

Örnekler:

- Metin düzeltme
- Küçük UI düzeni
- Caption ekleme
- Belge güncelleme

Akıl yürütme:

```text
Orta
```

## Orta risk

Örnekler:

- Yeni component
- Küçük servis fonksiyonu
- Basit grafik iyileştirme
- Cache düzenleme

Akıl yürütme:

```text
Orta / yüksek
```

## Yüksek risk

Örnekler:

- Finansal model mantığı
- Backtest hesapları
- Veri sağlayıcı mimarisi
- SPK / lisans / ticari yayın
- Kullanıcı verisi / güvenlik
- Büyük refactor

Akıl yürütme:

```text
Yüksek
```

---

## AI çıktısı kabul kriterleri

Her AI çıktısı şu şartları karşılamalı:

```text
1. Somut dosya veya net aksiyon üretmeli.
2. Gereksiz geniş refactor yapmamalı.
3. Mevcut proje mimarisine uymalı.
4. Test komutu vermeli.
5. Hata olursa geri dönüş planı olmalı.
6. Ticari ve hukuki riskleri gizlememeli.
```

---

## İş bölümü örnekleri

## Örnek 1: Yeni dashboard kartı

```text
ChatGPT:
Kartın mantığını ve dosya yerini belirler.

Claude:
Kart metnini daha premium hale getirir.

Cursor:
Kod düzenlemesini yapar.

ChatGPT:
Son kodu kontrol eder.

Test:
Streamlit çalıştırılır.

Commit:
Sprint adıyla kaydedilir.
```

## Örnek 2: Veri sağlayıcı seçimi

```text
Perplexity:
Kaynaklı lisans araştırması yapar.

Gemini:
Alternatif sağlayıcıları hızlı karşılaştırır.

ChatGPT:
Maliyet, lisans, teknik uyum ve proje bütçesine göre karar matrisi çıkarır.

Uzman kontrolü:
Ticari yayın öncesi gerekli görülür.
```

## Örnek 3: Model iyileştirme

```text
Notebook/Python:
Deney ve metrik karşılaştırması yapar.

ChatGPT:
Model sonucunun mantıklı olup olmadığını değerlendirir.

Cursor:
Kod entegrasyonunu küçük sprint halinde yapar.

ChatGPT:
Backtest ve UI sonucunu kontrol eder.
```

---

## Proje için kısa vadeli AI destekli yol haritası

## Sprint 3.15

AI iş bölümü ve üretim hattı belgesi.

## Sprint 3.16

Premium dashboard dilinin tüm panellere yayılması.

## Sprint 3.17

Analiz raporu üretim modülü.

## Sprint 3.18

Demo modu ve örnek veri paketi.

## Sprint 3.19

Kullanıcı onboarding ekranı.

## Sprint 3.20

Veri sağlayıcı karar matrisi ve maliyet tablosu.

---

## Nihai ürün hedefi

Fintech_Pro2 şuna dönüşmelidir:

```text
Kullanıcı dostu
Profesyonel görünümlü
Model çıktısını anlaşılır sunan
Backtest ile kendini denetleyen
Veri kaynağı risklerini açıkça yöneten
Ticari yayına kontrollü hazırlanan
Finansal analiz platformu
```

---

## Kesin kural

Hiçbir AI tek başına son karar vermez.

Son karar sırası:

```text
Araştırma
  ↓
AI önerisi
  ↓
ChatGPT mimari kontrolü
  ↓
Küçük uygulama
  ↓
Test
  ↓
Kullanıcı onayı
  ↓
Commit
```

