import streamlit as st

from components.premium_ui import render_premium_table

from services.horizon_validation_engine import build_horizon_validation_report


def _safe_display_table(df):
    if df is None:
        return df

    safe = df.copy()

    for col in safe.columns:
        if safe[col].dtype == "object":
            safe[col] = safe[col].astype(str)

    return safe


def render_horizon_validation_panel(
    data,
    market_symbol: str,
    asset_name: str,
    asset_type: str,
) -> None:
    st.markdown("## Vade Bazlı Çoklu Benchmark Doğrulama")
    st.caption(
        "Bu panel ana gelecek tablosunu değiştirmez. "
        "Modelin kısa, orta ve uzun vadelerde birden fazla benchmarka karşı ne kadar başarılı olduğunu ölçer."
    )

    with st.spinner("Vade bazlı doğrulama çalışıyor..."):
        report = build_horizon_validation_report(
            target_data=data,
            market_symbol=market_symbol,
            asset_name=asset_name,
            asset_type=asset_type,
        )

    summary = report.get("summary")
    diagnostics = report.get("diagnostics")

    if summary is None or summary.empty:
        st.error("Vade bazlı doğrulama sonucu üretilemedi.")
        if diagnostics is not None and not diagnostics.empty:
            render_premium_table(
                _safe_display_table(diagnostics),
                title="Vade Bazlı Tanı",
                subtitle="Hesaplanamayan veya veri yetersiz kalan vadeler burada görünür.",
            )
        return

    strong_count = int((summary["Vade Başarısı"] == "Güçlü").sum())
    partial_count = int((summary["Vade Başarısı"] == "Kısmi").sum())
    failed_count = int((summary["Vade Başarısı"] == "Hayır").sum())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Güçlü Vade", strong_count)

    with col2:
        st.metric("Kısmi Vade", partial_count)

    with col3:
        st.metric("Başarısız Vade", failed_count)

    st.markdown("### Vade Bazlı Model Başarısı")

    preferred_columns = [
        "Vade",
        "Vade Grubu",
        "Gün",
        "Model RMSE",
        "Model MAPE %",
        "Mutlak En İyi Benchmark",
        "Mutlak En İyi Benchmark RMSE",
        "Geçtiği Benchmark",
        "Toplam Benchmark",
        "Vade Başarısı",
        "Yön Doğruluğu %",
        "Test Gözlemi",
    ]

    visible_columns = [
        col for col in preferred_columns
        if col in summary.columns
    ]

    summary_display = summary[visible_columns].copy()

    render_premium_table(
        _safe_display_table(summary_display),
        title="Vade Bazlı Başarı Özeti",
        subtitle=(
            "Bu tablo modelin kısa, orta ve uzun vadelerde hangi benchmarklara karşı "
            "başarılı olduğunu sade biçimde gösterir."
        ),
    )

    with st.expander("Tüm benchmark ve MAPE detayları", expanded=False):
        render_premium_table(
            _safe_display_table(summary),
            title="Tüm Benchmark ve MAPE Detayları",
            subtitle="Teknik inceleme için ayrıntılı vade tablosu.",
        )

    with st.expander("Vade Bazlı Tanı Paneli", expanded=False):
        render_premium_table(_safe_display_table(diagnostics), width="stretch")

    st.info(
        "Kısa vadede başarısız olan model uzun vadede otomatik silinmez. "
        "Bu panel, modelin hangi vadede işe yaradığını ayrı ayrı gösterir."
    )
