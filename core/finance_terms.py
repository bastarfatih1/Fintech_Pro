"""
Finans terimleri sözlüğü.

Amaç:
Finans bilmeyen bir kullanıcının grafikte, tabloda ve risk kartlarında
gördüğü terimleri sade dille anlayabilmesi.
"""

from __future__ import annotations

from typing import Dict


FINANCE_TERMS: Dict[str, Dict[str, str]] = {
    "RSI": {
        "title": "RSI ne demek?",
        "simple": (
            "RSI, fiyatın son günlerde fazla mı hızlandığını yoksa fazla mı "
            "zayıfladığını anlamaya çalışan bir göstergedir."
        ),
        "why": (
            "Örneğin RSI 70 üstüne çıkarsa fiyat kısa vadede fazla ısınmış "
            "olabilir. 30 altına inerse fiyat fazla zayıflamış olabilir."
        ),
        "example": (
            "Bir araba çok hızlı giderse viraja girerken dikkat etmek gerekir. "
            "RSI da fiyatın hızını anlamaya yardım eder."
        ),
        "watch": "Tek başına alış veya satış kararı değildir.",
    },
    "Volatilite": {
        "title": "Volatilite ne demek?",
        "simple": (
            "Volatilite, fiyatın ne kadar sert dalgalandığını anlatır. "
            "Fiyat sakin sakin gidiyorsa volatilite düşük, sert inip çıkıyorsa yüksektir."
        ),
        "why": (
            "Aynı getiri ihtimali olsa bile volatilite yüksekse yol daha sarsıntılı olur. "
            "Yani sadece nereye gittiği değil, giderken ne kadar oynadığı da önemlidir."
        ),
        "example": (
            "Düz yolda giden araba düşük volatilite gibidir. Bozuk yolda zıplayarak "
            "giden araba yüksek volatilite gibidir."
        ),
        "watch": "Yüksek volatilite fırsat da risk de yaratabilir; tek başına iyi veya kötü değildir.",
    },
    "Max Drawdown": {
        "title": "Max Drawdown ne demek?",
        "simple": (
            "Max Drawdown, geçmişte fiyatın en yüksek gördüğü yerden sonra en kötü "
            "anda ne kadar düştüğünü gösterir."
        ),
        "why": (
            "Bu metrik, kötü bir dönemde yatırımın ne kadar geri çekilebildiğini "
            "anlamaya yarar. Örneğin değer 31% ise geçmişte bir zirveden sonra "
            "yaklaşık üçte bir oranında düşüş yaşanmış demektir."
        ),
        "example": (
            "100 TL olan bir varlık önce 120 TL'ye çıktı, sonra 84 TL'ye düştü diyelim. "
            "Zirve 120 TL idi. 84 TL'ye düşmesi yaklaşık 30% geri çekilme demektir."
        ),
        "watch": "Bu geçmişte olan en kötü düşüşü gösterir; gelecekte aynısı olur veya olmaz diye garanti vermez.",
    },
    "VaR": {
        "title": "VaR ne demek?",
        "simple": (
            "VaR, normal piyasa koşullarında kötü bir günde yaklaşık ne kadar kayıp "
            "görülebileceğini tahmin etmeye çalışan risk ölçüsüdür."
        ),
        "why": (
            "Örneğin 95% VaR 2.27% ise sistem şunu söyler: Normal şartlarda günlerin "
            "çoğunda kayıp bu civarı aşmayabilir; ama nadir kötü günlerde daha fazlası olabilir."
        ),
        "example": (
            "Hava durumu gibi düşün. 'Bugün yağmur ihtimali düşük' denebilir ama bu hiç "
            "yağmur yağmaz demek değildir. VaR da risk için yaklaşık sınır verir."
        ),
        "watch": "Panik, kriz veya olağanüstü haber dönemlerinde VaR eşiği aşılabilir.",
    },
    "Sharpe": {
        "title": "Sharpe oranı ne demek?",
        "simple": (
            "Sharpe, alınan toplam riske karşı ne kadar getiri üretildiğini ölçmeye "
            "çalışır. Yani 'bu oynaklığa değmiş mi?' sorusuna bakar."
        ),
        "why": (
            "Sharpe yüksekse geçmişte risk başına getiri daha verimli görünür. "
            "Düşükse varlık çok sallanmış ama buna değecek kadar getiri üretmemiş olabilir."
        ),
        "example": (
            "İki yol düşün: Biri çok sarsıntılı ama aynı yere götürüyor, diğeri daha sakin. "
            "Sharpe, bu sarsıntıya değip değmediğini anlamaya yardım eder."
        ),
        "watch": "Sharpe geçmiş veriye bakar; gelecek performansı garanti etmez.",
    },
    "Sortino": {
        "title": "Sortino oranı ne demek?",
        "simple": (
            "Sortino, özellikle kötü düşüşlere bakarak getiri kalitesini ölçer. "
            "Sharpe tüm dalgalanmayı dikkate alırken Sortino daha çok aşağı yönlü riske odaklanır."
        ),
        "why": (
            "Yatırımcı için yukarı yönlü dalgalanma her zaman rahatsız edici değildir; "
            "asıl önemli olan aşağı yönlü sert düşüşlerdir. Sortino bunu ayırmaya çalışır."
        ),
        "example": (
            "Bir asansör hızlı yukarı çıkıyorsa sorun olmayabilir; ama hızlı aşağı iniyorsa "
            "risk hissi artar. Sortino daha çok aşağı hareketlere bakar."
        ),
        "watch": "Kısa veri dönemlerinde veya aşırı sakin piyasalarda yanıltıcı olabilir.",
    },
    "Beta": {
        "title": "Beta ne demek?",
        "simple": (
            "Beta, bu varlığın genel piyasaya göre ne kadar hassas hareket ettiğini anlatır."
        ),
        "why": (
            "Beta 1 civarıysa piyasa ile benzer hareket eder. 1.5 civarıysa piyasa hareketlerine "
            "daha sert tepki verebilir. 0.5 civarıysa daha sakin kalabilir."
        ),
        "example": (
            "Piyasa 1 adım atınca bu varlık da yaklaşık 1 adım atıyorsa beta 1 gibidir. "
            "Piyasa 1 adım atınca bu varlık 1.5 adım atıyorsa beta daha yüksektir."
        ),
        "watch": "Beta geçmiş ilişkiyi gösterir; piyasa koşulları değişirse beta davranışı da değişebilir.",
    },
    "Konsensüs": {
        "title": "Konsensüs ne demek?",
        "simple": "Birden fazla modelin tek bir ortak senaryo altında birleştirilmesidir.",
        "why": "Tek modelin hatasına çok bağımlı kalmamak için farklı modellerin sesi bir araya getirilir.",
        "example": "Bir konuda tek kişiye değil, birkaç uzmana sorup ortak fikre bakmak gibidir.",
        "watch": "Konsensüs de tahmindir; kesin sonuç değildir.",
    },
    "Model Ağırlığı": {
        "title": "Model ağırlığı ne demek?",
        "simple": "Sistemin hangi modele ne kadar önem verdiğini gösterir.",
        "why": "Geçmiş testlerde daha tutarlı görünen model, ortak tahminde daha fazla söz sahibi olabilir.",
        "example": "Bir kurulda bazı kişilerin fikrine daha fazla güvenmek gibi düşünebilirsin.",
        "watch": "Yüksek ağırlık, modelin kesin doğru olduğu anlamına gelmez.",
    },
    "Backtest": {
        "title": "Backtest ne demek?",
        "simple": "Bir modelin geçmiş veride denenmesidir. Model geçmişte çalışsaydı ne kadar hata yapardı diye bakılır.",
        "why": "Modelin geçmiş koşullarda işe yarayıp yaramadığını anlamaya yardım eder.",
        "example": "Bir öğrencinin deneme sınavına girmesi gibi. Gerçek sınavı garanti etmez ama fikir verir.",
        "watch": "Geçmişte iyi çalışan model gelecekte mutlaka iyi çalışacak demek değildir.",
    },
    "RMSE": {
        "title": "RMSE ne demek?",
        "simple": "Tahmin hatasının büyüklüğünü ölçer. Düşük RMSE genelde daha küçük hata demektir.",
        "why": "Modellerin geçmişte hedef fiyata ne kadar yakın tahmin yaptığını karşılaştırmaya yardım eder.",
        "example": "Hedef tahtasına atış yapmak gibi. Ok merkeze ne kadar yakınsa hata o kadar küçüktür.",
        "watch": "RMSE fiyat seviyesini ölçer; yönü doğru tahmin edip etmediğini tek başına göstermez.",
    },
    "Yön Doğruluğu": {
        "title": "Yön doğruluğu ne demek?",
        "simple": "Modelin fiyatın yukarı mı aşağı mı gideceğini geçmişte ne kadar doğru tahmin ettiğini gösterir.",
        "why": "Fiyat hedefi tam tutmasa bile yön tahmini bazı kullanıcılar için önemli olabilir.",
        "example": "Yağmur miktarını bilememek ama yağmur yağacağını doğru tahmin etmek gibi.",
        "watch": "Yön doğru olsa bile fiyat hedefi hatalı olabilir.",
    },
    "Stabilite Skoru": {
        "title": "Stabilite skoru ne demek?",
        "simple": "Modelin farklı dönemlerde ne kadar tutarlı çalıştığını anlatır.",
        "why": "Sadece bir dönemde iyi çalışan değil, farklı piyasa koşullarında da dengeli kalan modeller daha güvenilir görünebilir.",
        "example": "Sadece bir maçta değil, sezon boyunca iyi oynayan takım gibi.",
        "watch": "Yüksek stabilite geleceği garanti etmez.",
    },
    "Boğa Senaryosu": {
        "title": "Boğa senaryosu ne demek?",
        "simple": "Fiyat için daha olumlu koşullarda oluşabilecek yukarı yönlü olası senaryodur.",
        "why": "İyimser tarafı görmeye yardım eder.",
        "example": "Hava açarsa yol daha rahat olur demek gibidir.",
        "watch": "Kesin hedef değil, olasılık senaryosudur.",
    },
    "Ayı Senaryosu": {
        "title": "Ayı senaryosu ne demek?",
        "simple": "Fiyat için daha olumsuz koşullarda oluşabilecek aşağı yönlü baskı senaryosudur.",
        "why": "Kötümser tarafı ve riski görünür yapar.",
        "example": "Hava bozarsa yol zorlaşabilir demek gibidir.",
        "watch": "Kesin düşüş tahmini değildir.",
    },
    "Senaryo Bandı": {
        "title": "Senaryo bandı ne demek?",
        "simple": "Grafikteki gölgeli alan, fiyatın tek çizgi yerine hangi aralıkta oynayabileceğini anlatır.",
        "why": "Tahminin çevresindeki belirsizliği görmeyi sağlar.",
        "example": "Navigasyonda varış süresi 20-30 dakika yazması gibi; tek sayı yerine aralık verir.",
        "watch": "Fiyat bu bandın dışına da çıkabilir.",
    },
    "Baz Senaryo": {
        "title": "Baz senaryo ne demek?",
        "simple": "Modellerin ağırlıklı ortak ana tahmin çizgisidir.",
        "why": "Kötümser ve iyimser uçların arasında ana yol gibi okunur.",
        "example": "En kötü ve en iyi ihtimal arasında en makul görülen rota gibidir.",
        "watch": "Tek kesin fiyat değildir.",
    },
    "Destek": {
        "title": "Destek seviyesi ne demek?",
        "simple": "Fiyat düşerken alıcıların güçlenebileceği düşünülen bölgedir.",
        "why": "Fiyatın nerede tutunmaya çalışabileceğini izlemek için kullanılır.",
        "example": "Aşağı düşen topun yere çarpıp sekmesi gibi düşünülebilir.",
        "watch": "Destek kırılabilir; garanti zemin değildir.",
    },
    "Direnç": {
        "title": "Direnç seviyesi ne demek?",
        "simple": "Fiyat yükselirken satış baskısının artabileceği düşünülen bölgedir.",
        "why": "Fiyatın nerede zorlanabileceğini izlemek için kullanılır.",
        "example": "Yukarı çıkan topun tavana çarpması gibi düşünülebilir.",
        "watch": "Direnç aşılabilir; garanti tavan değildir.",
    },
    "Momentum": {
        "title": "Momentum ne demek?",
        "simple": "Fiyat hareketinin hızını ve gücünü anlatır.",
        "why": "Yükseliş veya düşüşün ne kadar canlı olduğunu görmeye yardım eder.",
        "example": "Bisikletin hızlanması veya yavaşlaması gibi.",
        "watch": "Momentum hızlı değişebilir.",
    },
    "AI Güven Skoru": {
        "title": "AI güven skoru ne demek?",
        "simple": "AI yorumunun haber başlığına ne kadar emin yaklaştığını gösteren kaba bir puandır.",
        "why": "Yorumun güçlü mü zayıf mı olduğunu ayırt etmeye yardım eder.",
        "example": "Bir tahminin yanında 'bu konuda ne kadar eminim' notu gibi.",
        "watch": "Bu skor gerçek piyasa garantisi değildir.",
    },
}


def get_term(term: str) -> Dict[str, str]:
    """Sözlükten güvenli terim döndürür."""
    return FINANCE_TERMS.get(
        term,
        {
            "title": f"{term} ne demek?",
            "simple": "Bu terim için açıklama henüz eklenmedi.",
            "why": "Yeni sözlük katmanında genişletilebilir.",
            "example": "Örnek açıklama sonraki sürümde eklenebilir.",
            "watch": "Tek başına yatırım kararı için kullanılmamalıdır.",
        },
    )
