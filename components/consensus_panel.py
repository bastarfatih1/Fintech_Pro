"""
Konsensüs tahmin paneli.

Bu bileşen kalibre senaryo grafiğini, model ağırlıklarını,
gelecek değerlemelerini ve backtest sonuçlarını gösterir.
"""

from typing import Any, Mapping

import pandas as pd
import streamlit as st

from charts.consensus import create_consensus_chart
from components.ui_icons import icon_html


def _inject_consensus_premium_style() -> None:
    """Konsensüs paneli için premium görünüm stillerini ekler."""
    st.markdown(
        """
        <style>
        .fp-panel-hero {
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 20px;
            padding: 20px 22px;
            margin: 8px 0 18px 0;
            background:
                radial-gradient(circle at top left, rgba(99, 102, 241, 0.22), transparent 34%),
                radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.16), transparent 30%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.90));
            box-shadow: 0 16px 40px rgba(2, 6, 23, 0.22);
        }
        .fp-panel-eyebrow {
            color: #a5b4fc;
            font-size: 0.76rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            font-weight: 800;
            margin-bottom: 7px;
        }
        .fp-panel-title {
            color: #f8fafc;
            font-size: 1.36rem;
            font-weight: 850;
            margin-bottom: 6px;
        }
        .fp-panel-subtitle {
            color: #cbd5e1;
            font-size: 0.94rem;
            line-height: 1.55;
            max-width: 900px;
        }
        .fp-signal-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }
        .fp-signal-pill {
            border: 1px solid rgba(226, 232, 240, 0.16);
            border-radius: 999px;
            padding: 6px 10px;
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.45);
            font-size: 0.78rem;
        }
        .fp-section-note {
            border-left: 4px solid #818cf8;
            border-radius: 14px;
            padding: 12px 14px;
            background: rgba(99, 102, 241, 0.10);
            color: #e2e8f0;
            line-height: 1.55;
            margin: 8px 0 16px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_consensus_hero(forecast_data: Mapping[str, Any]) -> None:
    """Konsensüs paneli için premium giriş alanı gösterir."""
    model_weights = forecast_data.get("model_agirliklari", {})
    backtest_status = str(
        forecast_data.get("backtest_status", "Bilinmiyor")
    )
    calendar_name = str(
        forecast_data.get("takvim_adi", "Takvim standardı yok")
    )

    active_models = 0
    top_model = "Model yok"
    top_weight = 0.0

    if isinstance(model_weights, Mapping) and model_weights:
        parsed_weights = []
        for model_name, raw_weight in model_weights.items():
            try:
                weight = float(raw_weight)
            except (TypeError, ValueError):
                weight = 0.0

            if weight > 0:
                active_models += 1
                parsed_weights.append((str(model_name), weight))

        if parsed_weights:
            top_model, top_weight = max(
                parsed_weights,
                key=lambda item: item[1],
            )
            top_model = _format_model_name(top_model)

    _inject_consensus_premium_style()

    st.markdown(
        f"""
        <div class="fp-panel-hero">
            <div class="fp-panel-eyebrow">Consensus Intelligence Engine</div>
            <div class="fp-panel-title"><span class="fp-title-with-icon">{icon_html("consensus_mesh")}</span>Model Konsensüsü & Senaryo Laboratuvarı</div>
            <div class="fp-panel-subtitle">
                Farklı modellerin çıktıları backtest, referans model ve stabilite filtresinden
                geçirilerek tek bir okunabilir senaryo haritasına dönüştürülür.
            </div>
            <div class="fp-signal-row">
                <div class="fp-signal-pill"><span class="fp-pill-with-icon">{icon_html("signal_node", "fp-icon-small")}</span>Aktif model: {active_models}</div>
                <div class="fp-signal-pill"><span class="fp-pill-with-icon">{icon_html("consensus_mesh", "fp-icon-small")}</span>Lider ağırlık: {top_model} · %{top_weight * 100:.1f}</div>
                <div class="fp-signal-pill"><span class="fp-pill-with-icon">{icon_html("performance_curve", "fp-icon-small")}</span>Backtest: {backtest_status}</div>
                <div class="fp-signal-pill"><span class="fp-pill-with-icon">{icon_html("scenario_path", "fp-icon-small")}</span>{calendar_name}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _format_model_name(model_name: str) -> str:
    """Teknik model adını kullanıcı dostu biçime dönüştürür."""
    return str(model_name).replace("_", " ").title()


def _render_projection_notice(
    forecast_data: Mapping[str, Any],
) -> None:
    """Projeksiyonun niteliğini ve güven aralığı yöntemini açıklar."""
    projection_notice = str(
        forecast_data.get(
            "projeksiyon_bildirimi",
            (
                "Sonuçlar olasılıksal senaryolardır; "
                "kesin gelecek fiyatı değildir."
            ),
        )
    )
    confidence_method = str(
        forecast_data.get(
            "guven_araligi_yontemi",
            "Backtest hatalarıyla kalibre senaryo aralığı",
        )
    )

    st.markdown(
        "<div class='fp-section-note'>Bilgi: "
        + projection_notice
        + "</div>",
        unsafe_allow_html=True,
    )
    with st.expander("Senaryo bandı yöntemi", expanded=False):
        st.caption(
            confidence_method
            + ". Gölge alan yatırım sonucu garantisi değildir."
        )


def _render_model_statuses(
    model_statuses: Mapping[str, Any],
) -> None:
    """Model çalışma durumlarını özetler ve ayrıntıları gösterir."""
    successful_models = []
    failed_models = []

    for model_name, status_info in model_statuses.items():
        if not isinstance(status_info, Mapping):
            failed_models.append(
                (
                    model_name,
                    "Model durum bilgisi beklenen biçimde değil.",
                )
            )
            continue

        status = str(status_info.get("durum", "")).lower()
        error_message = status_info.get("hata")

        if status == "başarılı":
            successful_models.append(model_name)
        else:
            failed_models.append(
                (
                    model_name,
                    str(error_message or "Bilinmeyen model hatası"),
                )
            )

    total_models = len(model_statuses)
    successful_count = len(successful_models)
    failed_count = len(failed_models)

    col_success, col_failed, col_total = st.columns(3)

    col_success.metric(
        "Çalışan Model",
        successful_count,
    )
    col_failed.metric(
        "Başarısız Model",
        failed_count,
    )
    col_total.metric(
        "Toplam Model",
        total_models,
    )

    if successful_models:
        readable_names = ", ".join(
            _format_model_name(name)
            for name in successful_models
        )
        st.success(
            "Geçerli rota üreten modeller: "
            + readable_names
        )

    if failed_models:
        with st.expander(
            f"Başarısız model ayrıntıları ({failed_count})",
            expanded=False,
        ):
            for model_name, error_message in failed_models:
                st.markdown(
                    f"**{_format_model_name(model_name)}**"
                )
                st.caption(error_message)


def _render_model_weights(
    model_weights: Mapping[str, Any],
    backtest_table: Any,
) -> None:
    """Dinamik konsensüs ağırlıklarını model bazında gösterir."""
    st.markdown("#### Dinamik Model Ağırlıkları")

    if not isinstance(model_weights, Mapping) or not model_weights:
        st.info("Gösterilecek model ağırlığı bulunamadı.")
        return

    backtest_lookup = {}

    if isinstance(backtest_table, pd.DataFrame) and not backtest_table.empty:
        for _, row in backtest_table.iterrows():
            model_name = str(row.get("Model", ""))

            backtest_lookup[model_name] = {
                "RMSE": row.get("RMSE"),
                "Yön Doğruluğu %": row.get("Yön Doğruluğu %"),
                "Stabilite Skoru": row.get("Stabilite Skoru"),
                "RMSE İyileşme %": row.get("RMSE İyileşme %"),
                "Referansı Geçti": row.get("Referansı Geçti", ""),
                "Durum": row.get("Durum", ""),
            }

    rows = []

    for model_name, raw_weight in model_weights.items():
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            weight = 0.0

        backtest_info = backtest_lookup.get(str(model_name), {})

        rmse_value = pd.to_numeric(
            backtest_info.get("RMSE"),
            errors="coerce",
        )
        direction_value = pd.to_numeric(
            backtest_info.get("Yön Doğruluğu %"),
            errors="coerce",
        )
        stability_value = pd.to_numeric(
            backtest_info.get("Stabilite Skoru"),
            errors="coerce",
        )
        improvement_value = pd.to_numeric(
            backtest_info.get("RMSE İyileşme %"),
            errors="coerce",
        )

        rows.append(
            {
                "Model": _format_model_name(model_name),
                "Konsensüs Ağırlığı %": round(weight * 100.0, 2),
                "RMSE": (
                    round(float(rmse_value), 2)
                    if pd.notna(rmse_value)
                    else None
                ),
                "RMSE İyileşme %": (
                    round(float(improvement_value), 1)
                    if pd.notna(improvement_value)
                    else None
                ),
                "Yön Doğruluğu %": (
                    round(float(direction_value), 1)
                    if pd.notna(direction_value)
                    else None
                ),
                "Stabilite Skoru": (
                    round(float(stability_value), 1)
                    if pd.notna(stability_value)
                    else None
                ),
                "Referansı Geçti": str(
                    backtest_info.get(
                        "Referansı Geçti",
                        "Bilinmiyor",
                    )
                ),
                "Konsensüse Katılıyor": (
                    "Evet" if weight > 0 else "Hayır"
                ),
            }
        )

    weight_table = pd.DataFrame(rows)

    if weight_table.empty:
        st.info("Gösterilecek model ağırlığı bulunamadı.")
        return

    weight_table = weight_table.sort_values(
        by="Konsensüs Ağırlığı %",
        ascending=False,
    ).reset_index(drop=True)

    total_weight = float(
        weight_table["Konsensüs Ağırlığı %"].sum()
    )
    active_count = int(
        (weight_table["Konsensüse Katılıyor"] == "Evet").sum()
    )

    col_total, col_active = st.columns(2)

    col_total.metric(
        "Toplam Ağırlık",
        f"%{total_weight:.2f}",
    )
    col_active.metric(
        "Ağırlık Alan Model",
        active_count,
    )

    st.dataframe(
        weight_table,
        hide_index=True,
    )

    st.caption(
        "Ağırlıklar RMSE, yön doğruluğu, stabilite ve "
        "Naive Last Price referans modelini geçme koşuluna göre "
        "hesaplanır. Referansı geçemeyen model ağırlık alamaz."
    )


def _render_future_values(
    future_table: Any,
) -> None:
    """Gelecek senaryo tablosunu okunur sütun sırasıyla gösterir."""
    st.markdown("#### Detaylı Gelecek Senaryoları")

    if future_table is None:
        st.info("Gelecek senaryoları bulunamadı.")
        return

    if not isinstance(future_table, pd.DataFrame):
        st.warning(
            "Gelecek senaryoları beklenen tablo biçiminde değil."
        )
        return

    if future_table.empty:
        st.info("Gelecek senaryoları bulunamadı.")
        return

    display_table = future_table.copy()

    preferred_columns = (
        "Vade",
        "Kötümser Senaryo",
        "Baz Senaryo",
        "İyimser Senaryo",
        "Kötümser Getiri %",
        "Nominal Getiri %",
        "İyimser Getiri %",
        "Sermaye Karşılığı",
        "Tahmin",
    )

    visible_columns = [
        column
        for column in preferred_columns
        if column in display_table.columns
    ]

    remaining_columns = [
        column
        for column in display_table.columns
        if column not in visible_columns
    ]

    st.dataframe(
        display_table[visible_columns + remaining_columns],
        hide_index=True,
    )

    st.caption(
        "Baz senaryo ağırlıklı model konsensüsüdür. "
        "Kötümser ve iyimser değerler geçmiş backtest hatalarıyla "
        "kalibre edilmiş belirsizlik sınırlarıdır."
    )


def _render_backtest_results(
    backtest_table: Any,
    backtest_status: Any,
) -> None:
    """Backtest sonuçlarını özetler ve tablo halinde gösterir."""
    st.markdown("#### Geçmiş Performans Testi")

    status_text = str(backtest_status)

    if status_text.lower() != "tamamlandı":
        st.warning(
            "Backtest durumu: "
            + status_text
        )

    if not isinstance(backtest_table, pd.DataFrame):
        st.warning(
            "Backtest sonucu beklenen tablo biçiminde değil."
        )
        return

    if backtest_table.empty:
        st.info("Gösterilecek backtest sonucu bulunamadı.")
        return

    required_columns = {"Model", "Durum"}

    if not required_columns.issubset(backtest_table.columns):
        st.warning(
            "Backtest tablosunda gerekli alanlar bulunamadı."
        )
        return

    successful = backtest_table[
        backtest_table["Durum"].astype(str).str.lower() == "başarılı"
    ].copy()

    evaluated_models = successful[
        successful["Model"] != "Naive_Last_Price"
    ].copy()

    if "Referansı Geçti" in evaluated_models.columns:
        benchmark_winners = evaluated_models[
            evaluated_models["Referansı Geçti"]
            .astype(str)
            .str.lower()
            == "evet"
        ].copy()
    else:
        benchmark_winners = evaluated_models.copy()

    if evaluated_models.empty:
        st.warning(
            "Backtest çalıştı ancak değerlendirilecek model sonucu yok."
        )
    else:
        evaluated_models["RMSE"] = pd.to_numeric(
            evaluated_models["RMSE"],
            errors="coerce",
        )
        evaluated_models["Yön Doğruluğu %"] = pd.to_numeric(
            evaluated_models["Yön Doğruluğu %"],
            errors="coerce",
        )

        valid_rmse = evaluated_models.dropna(subset=["RMSE"])
        valid_direction = evaluated_models.dropna(
            subset=["Yön Doğruluğu %"]
        )

        col_count, col_rmse, col_direction = st.columns(3)

        col_count.metric(
            "Referansı Geçen Model",
            len(benchmark_winners),
        )

        if not valid_rmse.empty:
            best_rmse_row = valid_rmse.loc[
                valid_rmse["RMSE"].idxmin()
            ]
            col_rmse.metric(
                "En Düşük Model RMSE",
                f"{best_rmse_row['RMSE']:,.2f}",
            )
        else:
            col_rmse.metric("En Düşük Model RMSE", "-")

        if not valid_direction.empty:
            best_direction_row = valid_direction.loc[
                valid_direction["Yön Doğruluğu %"].idxmax()
            ]
            col_direction.metric(
                "En İyi Yön Doğruluğu",
                (
                    f"%{best_direction_row['Yön Doğruluğu %']:.1f}"
                ),
            )
        else:
            col_direction.metric("En İyi Yön Doğruluğu", "-")

    display_table = backtest_table.copy()

    for column, decimals in (
        ("MAE", 2),
        ("RMSE", 2),
        ("RMSE Sapması", 2),
        ("Referans RMSE", 2),
        ("RMSE İyileşme %", 1),
        ("Yön Doğruluğu %", 1),
        ("Yön Sapması", 1),
        ("Stabilite Skoru", 1),
        ("Konsensüs Ağırlığı %", 2),
    ):
        if column in display_table.columns:
            display_table[column] = pd.to_numeric(
                display_table[column],
                errors="coerce",
            ).round(decimals)

    visible_columns = [
        column
        for column in (
            "Model",
            "RMSE",
            "Referans RMSE",
            "RMSE İyileşme %",
            "Referansı Geçti",
            "Yön Doğruluğu %",
            "Stabilite Skoru",
            "Konsensüs Ağırlığı %",
            "Test Penceresi",
            "Test Gözlemi",
            "Backtest Türü",
            "Durum",
        )
        if column in display_table.columns
    ]

    st.dataframe(
        display_table[visible_columns],
        hide_index=True,
    )

    failed = backtest_table[
        backtest_table["Durum"].astype(str).str.lower()
        == "başarısız"
    ]

    if not failed.empty and "Hata" in failed.columns:
        with st.expander(
            f"Backtest hata ayrıntıları ({len(failed)})",
            expanded=False,
        ):
            for _, row in failed.iterrows():
                st.markdown(
                    f"**{_format_model_name(row['Model'])}**"
                )
                st.caption(str(row["Hata"]))


def render_consensus_panel(
    forecast_data: Mapping[str, Any],
    last_date: Any,
) -> None:
    """Konsensüs ve senaryo sekmesinin tamamını oluşturur."""
    _render_consensus_hero(forecast_data)

    required_keys = {
        "konsensus_rota",
        "senaryo_alt",
        "senaryo_ust",
        "rotalar",
        "model_durumlari",
        "model_agirliklari",
        "backtest_df",
        "backtest_status",
        "gelecek_df",
        "projeksiyon_bildirimi",
        "guven_araligi_yontemi",
    }
    missing_keys = required_keys.difference(forecast_data.keys())

    if missing_keys:
        st.error(
            "Konsensüs paneli için eksik veri alanları: "
            + ", ".join(sorted(missing_keys))
        )
        return

    _render_projection_notice(forecast_data)

    _render_model_statuses(
        forecast_data["model_durumlari"]
    )

    _render_model_weights(
        model_weights=forecast_data["model_agirliklari"],
        backtest_table=forecast_data["backtest_df"],
    )

    try:
        consensus_figure = create_consensus_chart(
            forecast_data=forecast_data,
            last_date=last_date,
        )
    except (
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        st.error(
            "Konsensüs grafiği oluşturulamadı. "
            f"Detay: {exc}"
        )
    else:
        st.plotly_chart(
            consensus_figure,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "responsive": True,
            },
        )

    _render_future_values(
        forecast_data["gelecek_df"]
    )

    _render_backtest_results(
        backtest_table=forecast_data["backtest_df"],
        backtest_status=forecast_data["backtest_status"],
    )
