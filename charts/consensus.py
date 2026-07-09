"""
Konsensüs tahmin grafiği.

Bu modül Monte Carlo güven koridorunu, tekil model tahminlerini
ve ağırlıklı konsensüs rotasını tek bir Plotly grafiğinde birleştirir.
"""

from collections.abc import Mapping
from typing import Any, Final

import numpy as np
import pandas as pd
import plotly.graph_objects as go


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
        raise ValueError(f"{field_name} içinde geçersiz sayısal değer var.")

    return array


def create_consensus_chart(
    forecast_data: Mapping[str, Any],
    last_date: Any,
) -> go.Figure:
    """
    Tahmin modellerini ve güven koridorunu tek grafikte gösterir.

    Args:
        forecast_data: Konsensüs rotası, Monte Carlo bantları ve
            model rotalarını içeren sözlük.
        last_date: Tarihsel verideki son gözlem tarihi.

    Returns:
        Hazırlanmış Plotly konsensüs grafiği.

    Raises:
        ValueError: Gerekli alanlar eksik veya uzunluklar uyumsuzsa.
    """
    required_keys = {
        "konsensus_rota",
        "mc_upper",
        "mc_lower",
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
    mc_upper = _to_one_dimensional_array(
        forecast_data["mc_upper"],
        "mc_upper",
    )
    mc_lower = _to_one_dimensional_array(
        forecast_data["mc_lower"],
        "mc_lower",
    )

    expected_length = len(consensus_path)

    if len(mc_upper) != expected_length or len(mc_lower) != expected_length:
        raise ValueError(
            "Monte Carlo güven bantları konsensüs rotasıyla aynı uzunlukta olmalıdır."
        )

    forecast_dates = pd.date_range(
        start=pd.Timestamp(last_date) + pd.Timedelta(days=1),
        periods=expected_length,
        freq="D",
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=mc_upper,
            mode="lines",
            line={"width": 0},
            hoverinfo="skip",
            showlegend=False,
            name="Üst Güven Sınırı",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=mc_lower,
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(0, 187, 255, 0.12)",
            line={"width": 0},
            name="%90 Monte Carlo Güven Koridoru",
            hovertemplate=(
                "Tarih: %{x|%d.%m.%Y}<br>"
                "Alt sınır: %{y:,.2f}<extra></extra>"
            ),
        )
    )

    model_paths = forecast_data["rotalar"]

    if not isinstance(model_paths, Mapping):
        raise ValueError("rotalar alanı sözlük benzeri bir yapı olmalıdır.")

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
                f"{model_name} rotasının uzunluğu konsensüs rotasıyla uyumlu değil."
            )

        display_name = str(model_name).replace("_", " ").upper()
        color = MODEL_COLORS[color_index % len(MODEL_COLORS)]
        color_index += 1

        figure.add_trace(
            go.Scatter(
                x=forecast_dates,
                y=model_path,
                mode="lines",
                name=display_name,
                line={
                    "color": color,
                    "width": 1.4,
                    "dash": "dash",
                },
                opacity=0.78,
                hovertemplate=(
                    f"{display_name}<br>"
                    "Tarih: %{x|%d.%m.%Y}<br>"
                    "Tahmin: %{y:,.2f}<extra></extra>"
                ),
            )
        )

    figure.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=consensus_path,
            mode="lines",
            name="🎯 AĞIRLIKLI KONSENSÜS",
            line={
                "color": "#00FF88",
                "width": 4,
            },
            hovertemplate=(
                "Konsensüs<br>"
                "Tarih: %{x|%d.%m.%Y}<br>"
                "Tahmin: %{y:,.2f}<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        template="plotly_dark",
        height=560,
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        hovermode="x unified",
        dragmode="pan",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        xaxis_title="Tahmin Tarihi",
        yaxis_title="Tahmini Fiyat",
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
