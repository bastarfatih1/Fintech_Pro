"""
Konsensüs tahmin paneli.

Bu bileşen konsensüs grafiğini ve
gelecek değerlemeleri tablosunu gösterir.
"""

from typing import Any, Mapping

import pandas as pd
import streamlit as st

from charts.consensus import create_consensus_chart


def _format_model_name(model_name: str) -> str:
    """Teknik model adını kullanıcı dostu biçime dönüştürür."""
    return str(model_name).replace("_", " ").title()


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
        "Konsensüse Katılan",
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
            "Konsensüse katılan modeller: "
            + readable_names
        )

    if failed_models:
        with st.expander(
            f"⚠️ Başarısız model ayrıntıları ({failed_count})",
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
    st.markdown("#### ⚖️ Dinamik Model Ağırlıkları")

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

        rows.append(
            {
                "Model": _format_model_name(model_name),
                "Konsensüs Ağırlığı %": round(weight * 100.0, 2),
                "RMSE": (
                    round(float(rmse_value), 2)
                    if pd.notna(rmse_value)
                    else None
                ),
                "Yön Doğruluğu %": (
                    round(float(direction_value), 1)
                    if pd.notna(direction_value)
                    else None
                ),
                "Konsensüse Katılıyor": (
                    "Evet" if weight > 0 else "Hayır"
                ),
                "Backtest Durumu": str(
                    backtest_info.get("Durum", "Kapsam Dışı")
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
        "Ağırlıklar backtest RMSE ve yön doğruluğuna göre "
        "dinamik olarak hesaplanır. ARIMA ve Monte Carlo henüz "
        "aynı backtest kapsamına alınmadığı için kontrollü temel "
        "ağırlık kullanabilir."
    )



def _render_backtest_results(
    backtest_table: Any,
    backtest_status: Any,
) -> None:
    """Backtest sonuçlarını özetler ve tablo halinde gösterir."""
    st.markdown("#### 🧪 Geçmiş Performans Testi")

    if str(backtest_status).lower() != "tamamlandı":
        st.warning(
            "Backtest tamamlanamadı: "
            + str(backtest_status)
        )
        return

    if not isinstance(backtest_table, pd.DataFrame):
        st.warning(
            "Backtest sonucu beklenen tablo biçiminde değil."
        )
        return

    if backtest_table.empty:
        st.info("Gösterilecek backtest sonucu bulunamadı.")
        return

    successful = backtest_table[
        backtest_table["Durum"] == "Başarılı"
    ].copy()

    if successful.empty:
        st.warning(
            "Backtest çalıştı ancak hiçbir model geçerli sonuç üretemedi."
        )
    else:
        successful["RMSE"] = pd.to_numeric(
            successful["RMSE"],
            errors="coerce",
        )
        successful["Yön Doğruluğu %"] = pd.to_numeric(
            successful["Yön Doğruluğu %"],
            errors="coerce",
        )

        best_rmse_row = successful.loc[
            successful["RMSE"].idxmin()
        ]
        best_direction_row = successful.loc[
            successful["Yön Doğruluğu %"].idxmax()
        ]

        col_count, col_rmse, col_direction = st.columns(3)

        col_count.metric(
            "Testi Geçen Model",
            len(successful),
        )
        col_rmse.metric(
            "En Düşük RMSE",
            f"{best_rmse_row['RMSE']:,.2f}",
            help=(
                "RMSE ne kadar düşükse modelin fiyat tahmini "
                "genel olarak o kadar başarılıdır."
            ),
        )
        col_direction.metric(
            "En İyi Yön Doğruluğu",
            f"%{best_direction_row['Yön Doğruluğu %']:.1f}",
            help=(
                "Modelin yükseliş veya düşüş yönünü doğru "
                "tahmin etme oranıdır."
            ),
        )

        st.caption(
            "En düşük RMSE: "
            f"{_format_model_name(best_rmse_row['Model'])} | "
            "En yüksek yön doğruluğu: "
            f"{_format_model_name(best_direction_row['Model'])}"
        )

    display_table = backtest_table.copy()

    for column in ("MAE", "RMSE"):
        if column in display_table.columns:
            display_table[column] = pd.to_numeric(
                display_table[column],
                errors="coerce",
            ).round(2)

    if "Yön Doğruluğu %" in display_table.columns:
        display_table["Yön Doğruluğu %"] = pd.to_numeric(
            display_table["Yön Doğruluğu %"],
            errors="coerce",
        ).round(1)

    if "Konsensüs Ağırlığı %" in display_table.columns:
        display_table["Konsensüs Ağırlığı %"] = pd.to_numeric(
            display_table["Konsensüs Ağırlığı %"],
            errors="coerce",
        ).round(2)

    visible_columns = [
        column
        for column in (
            "Model",
            "MAE",
            "RMSE",
            "Yön Doğruluğu %",
            "Konsensüs Ağırlığı %",
            "Test Gözlemi",
            "Durum",
        )
        if column in display_table.columns
    ]

    st.dataframe(
        display_table[visible_columns],
        hide_index=True,
    )

    failed = backtest_table[
        backtest_table["Durum"] == "Başarısız"
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
    """
    Konsensüs sekmesinin tamamını oluşturur.

    Args:
        forecast_data: Tahmin rotaları, güven bantları ve
            gelecek tablosunu içeren sözlük.
        last_date: Tarihsel verideki son gözlem tarihi.
    """
    st.markdown("### 🎯 Kurumsal Konsensüs & AI Projeksiyonu")

    required_keys = {
        "konsensus_rota",
        "mc_upper",
        "mc_lower",
        "rotalar",
        "model_durumlari",
        "model_agirliklari",
        "backtest_df",
        "backtest_status",
        "gelecek_df",
    }
    missing_keys = required_keys.difference(forecast_data.keys())

    if missing_keys:
        st.error(
            "Konsensüs paneli için eksik veri alanları: "
            + ", ".join(sorted(missing_keys))
        )
        return

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
    except Exception as exc:
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

    st.markdown("#### Detaylı Gelecek Değerlemeleri")

    future_table = forecast_data["gelecek_df"]

    if future_table is None:
        st.info("Gelecek değerlemeleri bulunamadı.")
    elif isinstance(future_table, pd.DataFrame):
        if future_table.empty:
            st.info("Gelecek değerlemeleri bulunamadı.")
        else:
            st.table(future_table)
    else:
        st.warning(
            "Gelecek değerlemeleri beklenen tablo biçiminde değil."
        )

    _render_backtest_results(
        backtest_table=forecast_data["backtest_df"],
        backtest_status=forecast_data["backtest_status"],
    )
