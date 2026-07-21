"""
Finans açıklama katmanı.

Bu bileşenler grafik, tablo ve metriklerin altında sade açıklamalar gösterir.
"""

from __future__ import annotations

import html
from typing import Iterable

import streamlit as st

from core.finance_terms import get_term


def _e(value: str) -> str:
    """HTML güvenli metin."""
    return html.escape(str(value), quote=True)


def inject_education_style() -> None:
    """Açıklama kartları için premium ve okunaklı stil ekler."""
    st.markdown(
        """
        <style>
        .fp-edu-card {
            border: 1px solid rgba(56, 189, 248, 0.34);
            border-radius: 20px;
            padding: 18px 19px;
            margin: 14px 0 20px 0;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 34%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(2, 6, 23, 0.82));
            box-shadow: 0 14px 34px rgba(2, 6, 23, 0.22);
            color: #e2e8f0;
        }
        .fp-edu-title {
            color: #dff6ff;
            font-weight: 900;
            font-size: 1.08rem;
            margin-bottom: 9px;
            letter-spacing: -0.01em;
        }
        .fp-edu-text {
            color: #d7e3f0;
            font-size: 0.98rem;
            line-height: 1.70;
            font-weight: 520;
        }
        .fp-edu-why {
            margin-top: 10px;
            color: #c7d2fe;
            font-size: 0.94rem;
            line-height: 1.62;
        }
        .fp-edu-example {
            margin-top: 10px;
            color: #bbf7d0;
            font-size: 0.94rem;
            line-height: 1.62;
        }
        .fp-edu-warning {
            margin-top: 11px;
            color: #fde68a;
            font-size: 0.90rem;
            line-height: 1.55;
            font-weight: 650;
        }
        .fp-term-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(285px, 1fr));
            gap: 13px;
            margin: 10px 0 20px 0;
        }
        .fp-term-card {
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 18px;
            padding: 15px 16px;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
            box-shadow: 0 10px 26px rgba(2, 6, 23, 0.14);
        }
        .fp-term-title {
            color: #f8fafc;
            font-size: 0.98rem;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .fp-term-simple {
            color: #d1d9e6;
            font-size: 0.90rem;
            line-height: 1.55;
        }
        .fp-term-why {
            margin-top: 8px;
            color: #c7d2fe;
            font-size: 0.86rem;
            line-height: 1.48;
        }
        .fp-term-example {
            margin-top: 8px;
            color: #bbf7d0;
            font-size: 0.86rem;
            line-height: 1.48;
        }
        .fp-term-watch {
            margin-top: 8px;
            color: #fde68a;
            font-size: 0.82rem;
            line-height: 1.45;
            font-weight: 650;
        }
        .fp-edu-section-title {
            color: #f8fafc;
            font-size: 1.18rem;
            font-weight: 920;
            margin: 18px 0 10px 0;
        }
        .fp-risk-explain-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
            gap: 13px;
            margin: 12px 0 22px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_plain_explainer(title: str, simple: str, why: str = "", watch: str = "", example: str = "") -> None:
    """Tek açıklama kartı gösterir."""
    inject_education_style()

    why_html = (
        f"<div class='fp-edu-why'><strong>Neden önemli?</strong> {_e(why)}</div>"
        if why
        else ""
    )
    example_html = (
        f"<div class='fp-edu-example'><strong>Örnek:</strong> {_e(example)}</div>"
        if example
        else ""
    )
    watch_html = (
        f"<div class='fp-edu-warning'>Dikkat: {_e(watch)}</div>"
        if watch
        else ""
    )

    st.markdown(
        f"""<div class="fp-edu-card"><div class="fp-edu-title">{_e(title)}</div><div class="fp-edu-text">{_e(simple)}</div>{why_html}{example_html}{watch_html}</div>""",
        unsafe_allow_html=True,
    )


def render_term_explainer(term: str, expanded: bool = False) -> None:
    """Bir finans terimini expander içinde açıklar."""
    info = get_term(term)
    with st.expander(info["title"], expanded=expanded):
        st.write(info["simple"])
        st.caption("Neden önemli? " + info["why"])
        if info.get("example"):
            st.caption("Örnek: " + info["example"])
        st.warning("Dikkat: " + info["watch"])


def render_term_grid(terms: Iterable[str], title: str = "Bu bölümde geçen terimler") -> None:
    """Birden fazla terimi düzgün premium kartlar olarak gösterir."""
    inject_education_style()
    cards = []

    for term in terms:
        info = get_term(term)
        cards.append(
            "<div class='fp-term-card'>"
            f"<div class='fp-term-title'>{_e(info['title'])}</div>"
            f"<div class='fp-term-simple'>{_e(info['simple'])}</div>"
            f"<div class='fp-term-why'><strong>Neden önemli?</strong> {_e(info['why'])}</div>"
            f"<div class='fp-term-example'><strong>Örnek:</strong> {_e(info.get('example', ''))}</div>"
            f"<div class='fp-term-watch'>Dikkat: {_e(info['watch'])}</div>"
            "</div>"
        )

    st.markdown(f"<div class='fp-edu-section-title'>{_e(title)}</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='fp-term-grid'>" + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def render_chart_explanation(chart_name: str, plain_text: str, terms: Iterable[str] = ()) -> None:
    """Grafik altına sade açıklama ve terimler ekler."""
    render_plain_explainer(
        title=f"Bu grafik neyi anlatıyor? · {chart_name}",
        simple=plain_text,
        why=(
            "Grafik, sayıları gözle görülür hale getirir. Böylece fiyatın yönü, "
            "riskin büyüklüğü veya modellerin birbirinden ne kadar ayrıldığı daha kolay okunur."
        ),
        example=(
            "Bir haritada sadece adresi değil, yolu da görürsün. Grafik de fiyatın "
            "gittiği yolu görmeye yardım eder."
        ),
        watch="Grafikler kesin gelecek tahmini değil, mevcut veriyi anlamaya yardım eden araçlardır.",
    )
    if terms:
        render_term_grid(terms, title="Bu grafikte geçen terimler")


def render_table_explanation(table_name: str, plain_text: str, terms: Iterable[str] = ()) -> None:
    """Tablo altına sade açıklama ekler."""
    render_plain_explainer(
        title=f"Bu tablo neyi anlatıyor? · {table_name}",
        simple=plain_text,
        why=(
            "Tablo, aynı anda birden fazla değeri karşılaştırmak için kullanılır. "
            "Örneğin hangi model daha çok ağırlık almış, hangi senaryoda fiyat aralığı "
            "daha geniş, hangi testte hata daha düşük gibi sorulara cevap verir."
        ),
        example=(
            "Market fişindeki ürünleri tek tek görmek gibi düşün. Grafik genel resmi, "
            "tablo ise ayrıntıları gösterir."
        ),
        watch="Tablodaki değerler tek başına yatırım kararı için yeterli değildir.",
    )
    if terms:
        render_term_grid(terms, title="Bu tabloda geçen terimler")


def render_risk_deep_explanation(
    max_drawdown: float,
    var_value: float,
    sharpe: float,
    sortino: float,
    beta: float,
) -> None:
    """Risk metriklerini örneklerle daha kapsamlı açıklar."""
    inject_education_style()

    max_dd_pct = abs(float(max_drawdown)) * 100
    var_pct = abs(float(var_value)) * 100

    explanations = [
        (
            "Max Drawdown",
            (
                f"Bu varlık geçmişte bir zirve seviyesinden sonra en kötü noktaya kadar yaklaşık %{max_dd_pct:.2f} "
                "geri çekilmiş görünüyor. Bu, 'en kötü dönemlerde ne kadar can yakmış?' sorusuna bakar."
            ),
            (
                "Örneğin 100.000 TL'lik bir yatırımda benzer oranlı bir düşüş yaşansa, kağıt üzerinde "
                f"yaklaşık {max_dd_pct:.0f}.000 TL civarı bir geri çekilme hissedilebilir. "
                "Bu hesap sadece oranı sezmek içindir."
            ),
        ),
        (
            "95% VaR",
            (
                f"Bu değer günlük risk eşiğini yaklaşık %{var_pct:.2f} olarak gösteriyor. "
                "Basitçe, normal günlerin çoğunda günlük kayıp bu seviyenin altında kalabilir; "
                "ama kötü ve nadir günlerde bu sınır aşılabilir."
            ),
            (
                "Emniyet kemeri gibi düşün. Çoğu gün işe yaramıyor gibi görünür ama kötü bir günde "
                "riskin boyutunu hatırlatır."
            ),
        ),
        (
            "Sharpe",
            (
                f"Sharpe {sharpe:.2f}. Bu oran, alınan toplam riske karşı geçmişte ne kadar verimli "
                "getiri üretildiğini anlamaya çalışır."
            ),
            (
                "Aynı yere giden iki yol varsa, biri çok sarsıntılı diğeri daha sakinse, Sharpe bu "
                "sarsıntıya değip değmediğini ölçmeye benzer."
            ),
        ),
        (
            "Sortino",
            (
                f"Sortino {sortino:.2f}. Bu oran özellikle aşağı yönlü kötü dalgalanmalara odaklanır. "
                "Yani iyi yöndeki hareketleri değil, daha çok can sıkan düşüşleri dikkate alır."
            ),
            (
                "Bir asansörün yukarı hızlı çıkması rahatsız etmeyebilir; ama aşağı hızlı inmesi risk "
                "hissi yaratır. Sortino bu aşağı hareketlere daha fazla bakar."
            ),
        ),
        (
            "Beta",
            (
                f"Beta {beta:.2f}. Bu, varlığın genel piyasaya ne kadar benzer tepki verdiğini gösterir. "
                "1 civarı piyasa ile benzer hareket anlamına gelir."
            ),
            (
                "Piyasa 1 adım atınca bu varlık da yaklaşık 1 adım atıyorsa beta 1 gibidir. "
                "Daha fazla tepki veriyorsa beta yükselir."
            ),
        ),
    ]

    cards = []
    for title, body, example in explanations:
        cards.append(
            "<div class='fp-term-card'>"
            f"<div class='fp-term-title'>{_e(title)}</div>"
            f"<div class='fp-term-simple'>{_e(body)}</div>"
            f"<div class='fp-term-example'><strong>Örnek:</strong> {_e(example)}</div>"
            "<div class='fp-term-watch'>Dikkat: Bu metrikler geçmiş veriden hesaplanır; gelecek için garanti vermez.</div>"
            "</div>"
        )

    st.markdown("<div class='fp-edu-section-title'>Risk metrikleri neyi anlatıyor?</div>", unsafe_allow_html=True)
    st.markdown("<div class='fp-risk-explain-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)


def build_plain_market_summary(
    signal_label: str,
    risk_level: str,
    confidence: float,
    nominal_return: float,
    band_width: float,
) -> str:
    """Genel görünüm için sade özet cümlesi üretir."""
    if nominal_return > 5:
        direction = "Ana senaryo, seçili vadede yukarı tarafın biraz daha güçlü olabileceğini gösteriyor."
    elif nominal_return < -5:
        direction = "Ana senaryo, seçili vadede aşağı yönlü baskının daha görünür olabileceğini gösteriyor."
    else:
        direction = "Ana senaryo, seçili vadede büyük bir kopuş yerine daha sınırlı değişim gösteriyor."

    if risk_level == "Yüksek":
        risk = "Risk seviyesi yüksek olduğu için bu sonuçlar daha temkinli okunmalı."
    elif risk_level == "Orta":
        risk = "Risk seviyesi orta bölgede; yani tablo tamamen sakin değil ama aşırı alarm da vermiyor."
    else:
        risk = "Risk seviyesi görece düşük görünüyor; yine de bu güvence anlamına gelmez."

    if confidence < 40:
        trust = "Model güveni zayıf; çizgiler daha çok fikir verir, kesin yön göstermez."
    elif confidence < 70:
        trust = "Model güveni orta; farklı modeller kısmen aynı yöne bakıyor."
    else:
        trust = "Model güveni güçlü; geçmiş testlerde modeller daha uyumlu çalışmış görünüyor."

    if band_width > 35:
        band = "Senaryo bandı geniş; iyimser ve kötümser ihtimaller arasında fark büyük."
    elif band_width > 18:
        band = "Senaryo bandı orta genişlikte; bazı belirsizlikler var."
    else:
        band = "Senaryo bandı dar; modeller birbirine daha yakın sonuçlar üretiyor."

    return f"{direction} {risk} {trust} {band}"
