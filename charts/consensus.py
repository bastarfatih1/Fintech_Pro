"""
Konsensüs ve kalibre senaryo grafiği.

Bu modül model rotalarını, ağırlıklı baz senaryoyu ve
backtest hatalarıyla kalibre edilmiş kötümser-iyimser
senaryo bandını tek bir Plotly grafiğinde birleştirir.
"""

from collections.abc import Mapping
from typing import Any, Final

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.market_calendar import (
    build_forecast_dates,
    get_market_calendar_config,
)


MODEL_COLORS: Final[tuple[str, ...]] = (
    "#FF4B4B",
    "#00E676",
    "#E040FB",
    "#FFD54F",
    "#00B0FF",
    "#FF9100",
)


def _to_one_dimensional_array(
    values: Any,
    field_name: str,
) -> np.ndarray:
    """Grafik verisini doğrular ve tek boyutlu sayısal diziye dönüştürür."""
    array = np.asarray(values, dtype=float).reshape(-1)

    if array.size == 0:
        raise ValueError(f"{field_name} verisi boş olamaz.")

    if not np.isfinite(array).all():
        raise ValueError(
            f"{field_name} içinde geçersiz sayısal değer var."
        )

    return array


def create_consensus_chart(
    forecast_data: Mapping[str, Any],
    last_date: Any,
) -> go.Figure:
    """
    Model rotalarını ve kalibre senaryo aralığını tek grafikte gösterir.

    Gölge alan kesin bir fiyat garantisi değildir. Backtest hataları,
    model dağılımı ve uygun olduğunda Monte Carlo aralığı kullanılarak
    oluşturulan belirsizlik bandıdır.
    """
    required_keys = {
        "konsensus_rota",
        "senaryo_alt",
        "senaryo_ust",
        "rotalar",
    }
    missing_keys = required_keys.difference(forecast_data.keys())

    if missing_keys:
        raise ValueError(
            "Konsensüs grafiği için eksik alanlar: "
            + ", ".join(sorted(missing_keys))
        )

    consensus_path = _to_one_dimensional_array(
        forecast_data["konsensus_rota"],
        "konsensus_rota",
    )
    scenario_lower = _to_one_dimensional_array(
        forecast_data["senaryo_alt"],
        "senaryo_alt",
    )
    scenario_upper = _to_one_dimensional_array(
        forecast_data["senaryo_ust"],
        "senaryo_ust",
    )

    expected_length = len(consensus_path)

    for field_name, values in (
        ("senaryo_alt", scenario_lower),
        ("senaryo_ust", scenario_upper),
    ):
        if len(values) != expected_length:
            raise ValueError(
                f"{field_name} konsensüs rotasıyla aynı uzunlukta olmalıdır."
            )

    if np.any(scenario_lower <= 0):
        raise ValueError("Kötümser senaryo sıfır veya negatif olamaz.")

    if np.any(scenario_lower > consensus_path):
        raise ValueError(
            "Kötümser senaryo baz senaryonun üzerinde olamaz."
        )

    if np.any(scenario_upper < consensus_path):
        raise ValueError(
            "İyimser senaryo baz senaryonun altında olamaz."
        )

    calendar_config = get_market_calendar_config(
        asset_type=forecast_data.get("varlik_turu"),
        market_symbol=forecast_data.get("market_symbol"),
    )
    forecast_dates = build_forecast_dates(
        last_date=last_date,
        periods=expected_length,
        asset_type=calendar_config.asset_type,
        market_symbol=forecast_data.get("market_symbol"),
    )

    confidence_method = str(
        forecast_data.get(
            "guven_araligi_yontemi",
            "Backtest hatasıyla kalibre senaryo aralığı",
        )
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=scenario_upper,
            mode="lines",
            line={"width": 0},
            hovertemplate=(
                "İyimser sınır<br>"
                "Tarih: %{x|%d.%m.%Y}<br>"
                "Fiyat: %{y:,.2f}<extra></extra>"
            ),
            showlegend=False,
            name="İyimser Senaryo",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=scenario_lower,
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(0, 187, 255, 0.14)",
            line={"width": 0},
            name="Kalibre Senaryo Aralığı",
            customdata=np.column_stack(
                (scenario_lower, scenario_upper)
            ),
            hovertemplate=(
                "Senaryo aralığı<br>"
                "Tarih: %{x|%d.%m.%Y}<br>"
                "Kötümser: %{customdata[0]:,.2f}<br>"
                "İyimser: %{customdata[1]:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    model_paths = forecast_data["rotalar"]

    if not isinstance(model_paths, Mapping):
        raise ValueError(
            "rotalar alanı sözlük benzeri bir yapı olmalıdır."
        )

    route_types = forecast_data.get("rota_turleri", {})

    if not isinstance(route_types, Mapping):
        route_types = {}

    color_index = 0

    for model_name, model_values in model_paths.items():
        if model_name == "Monte_Carlo":
            continue

        model_path = _to_one_dimensional_array(
            model_values,
            str(model_name),
        )

        if len(model_path) != expected_length:
            raise ValueError(
                f"{model_name} rotasının uzunluğu "
                "konsensüs rotasıyla uyumlu değil."
            )

        route_type = str(
            route_types.get(
                model_name,
                "Model Tahmin Rotası",
            )
        )
        is_visual_route = route_type.lower().startswith("görsel")

        base_display_name = (
            str(model_name).replace("_", " ").upper()
        )
        display_name = (
            f"{base_display_name} · GÖRSEL ROTA"
            if is_visual_route
            else base_display_name
        )

        color = MODEL_COLORS[
            color_index % len(MODEL_COLORS)
        ]
        color_index += 1

        figure.add_trace(
            go.Scatter(
                x=forecast_dates,
                y=model_path,
                mode="lines",
                name=display_name,
                line={
                    "color": color,
                    "width": 1.3,
                    "dash": "dot" if is_visual_route else "dash",
                },
                opacity=0.65 if is_visual_route else 0.78,
                customdata=np.full(
                    expected_length,
                    route_type,
                    dtype=object,
                ),
                hovertemplate=(
                    f"{base_display_name}<br>"
                    "Tarih: %{x|%d.%m.%Y}<br>"
                    "Değer: %{y:,.2f}<br>"
                    "Tür: %{customdata}"
                    "<extra></extra>"
                ),
            )
        )

    figure.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=consensus_path,
            mode="lines",
            name="BAZ SENARYO · AĞIRLIKLI KONSENSÜS",
            line={
                "color": "#00FF88",
                "width": 4,
            },
            hovertemplate=(
                "Baz senaryo<br>"
                "Tarih: %{x|%d.%m.%Y}<br>"
                "Fiyat: %{y:,.2f}<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        template="plotly_dark",
        height=580,
        margin={"l": 0, "r": 0, "t": 55, "b": 0},
        hovermode="x unified",
        dragmode="pan",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        xaxis_title=calendar_config.xaxis_title,
        yaxis_title="Senaryo Fiyatı",
        annotations=[
            {
                "text": (
                    "Gölge alan kesin fiyat garantisi değildir. "
                    + confidence_method
                    + " | Takvim: "
                    + calendar_config.calendar_name
                ),
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": -0.17,
                "showarrow": False,
                "align": "left",
                "font": {
                    "size": 11,
                    "color": "#A0A0A0",
                },
            }
        ],
    )

    figure.update_xaxes(
        showspikes=True,
        spikecolor="#808080",
        spikesnap="cursor",
        spikemode="across",
    )

    figure.update_yaxes(
        showspikes=True,
        spikecolor="#808080",
        spikemode="across",
    )

    return figure
