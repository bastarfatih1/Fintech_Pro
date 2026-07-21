import streamlit as st

from components.premium_ui import render_premium_table

from services.eviews_regression_engine import build_eviews_regression


def _fmt_money(value: float, symbol: str) -> str:
    try:
        return f"{float(value):,.2f} {symbol}"
    except Exception:
        return "-"


def _fmt_pct(value: float) -> str:
    try:
        return f"%{float(value) * 100:.2f}"
    except Exception:
        return "-"




def _safe_display_table(df):
    """
    Streamlit / PyArrow karışık tipli object sütunlarda hata verebiliyor.
    Bu yüzden sadece ekranda gösterilecek tabloyu güvenli string forma çevirir.
    Hesaplama verisine dokunmaz.
    """
    if df is None:
        return df

    safe = df.copy()

    for col in safe.columns:
        if safe[col].dtype == "object":
            safe[col] = safe[col].astype(str)

    return safe


def render_factor_intelligence_panel(
    data,
    forecast_days: int,
    market_symbol: str,
    asset_name: str,
    asset_type: str,
    currency_symbol: str,
    currency_rate: float,
) -> None:
    st.markdown("## Dynamic Factor Intelligence Engine")
    st.caption(
        "EViews benzeri OLS regresyon + faktör matrisi + etki yüzdesi + tanı paneli. "
        "Bağımlı değişken gelecek getiri, bağımsız değişkenler faktör getirileri ve teknik değişkenlerdir."
    )

    try:
        result = build_eviews_regression(
            target_data=data,
            forecast_days=forecast_days,
            market_symbol=market_symbol,
            asset_name=asset_name,
            asset_type=asset_type,
        )
    except Exception as exc:
        st.error("Dynamic Factor Intelligence Engine çalışamadı.")
        st.warning(str(exc))
        return

    current_display = result["current_price"] * currency_rate
    predicted_display = result["predicted_price"] * currency_rate

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Bugünkü Fiyat", _fmt_money(current_display, currency_symbol))

    with col2:
        st.metric("Faktör OLS Tahmini Fiyat", _fmt_money(predicted_display, currency_symbol))

    with col3:
        st.metric("Faktör OLS Tahmini Getiri", _fmt_pct(result["predicted_return"]))

    st.markdown("### Regresyon Denklemi")
    st.code(result["formula"], language="text")

    st.markdown("### EViews Benzeri Katsayı Tablosu")
    render_premium_table(
        _safe_display_table(result["coef_table"]),
        title="EViews Benzeri Katsayı Tablosu",
        subtitle="Bu tablo hangi faktörün geçmişte fiyatla nasıl ilişki kurduğunu gösterir. Katsayı pozitifse geçmişte aynı yönde, negatifse ters yönde ilişki görülmüştür.",
    )

    st.markdown("### Faktör Etki Payları")
    render_premium_table(
        _safe_display_table(result["effect_table"]),
        title="Faktör Etki Payları",
        subtitle="Bu tablo faktörlerin model içinde ne kadar açıklayıcı göründüğünü sade şekilde gösterir. Etki payı yüksek olan faktör, geçmişte fiyat hareketini daha fazla açıklamıştır.",
    )

    st.markdown("### Model İstatistikleri")
    render_premium_table(
        _safe_display_table(result["stats_table"]),
        title="Model İstatistikleri",
        subtitle="Bu bölüm modelin genel matematiksel kalitesini gösterir. R-kare, F-istatistiği ve hata testleri burada incelenir.",
    )

    st.markdown("### Çoklu Bağlantı Kontrolü / VIF")
    if result["vif_table"] is not None and not result["vif_table"].empty:
        render_premium_table(
            _safe_display_table(result["vif_table"]),
            title="Çoklu Bağlantı Kontrolü",
            subtitle="VIF değeri, faktörlerin birbirine fazla benzeyip benzemediğini gösterir. Çok yüksek VIF varsa model aynı bilgiyi tekrar tekrar kullanıyor olabilir.",
        )
    else:
        st.info("VIF tablosu üretilemedi veya yeterli değişken yok.")

    st.markdown("### Faktör Veri Tanı Paneli")
    render_premium_table(
        _safe_display_table(result["factor_diagnostics"]),
        title="Faktör Veri Tanı Paneli",
        subtitle="Bu tablo hangi faktör verisinin başarıyla geldiğini, hangisinin eksik veya hesaplanamaz olduğunu gösterir.",
    )

    dropped = result.get("dropped_correlated_factors", [])
    if dropped:
        st.warning(
            "Aşırı korelasyon nedeniyle çıkarılan faktörler: "
            + ", ".join(dropped)
        )

    st.info(
        "Bu analiz yatırım tavsiyesi değildir. OLS modeli geçmiş ilişkileri ölçer; "
        "ilişki nedensellik garantisi vermez. Ama hangi faktörün geçmişte ne kadar açıklayıcı olduğunu açıkça gösterir."
    )
