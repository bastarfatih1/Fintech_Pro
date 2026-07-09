"""
Fiyat ve hacim grafiği bileşenleri.

Bu modül mum grafiğini, hareketli ortalamaları, hacmi
ve tahmin bölgelerini oluşturur.
"""

from typing import Final

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


REQUIRED_COLUMNS: Final[set[str]] = {
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
}


def create_price_volume_chart(
    data: pd.DataFrame,
    currency_rate: float,
    current_price: float,
    bear_target: float,
    bull_target: float,
    visible_periods: int = 250,
) -> go.Figure:
    """
    Mum, EMA ve hacim grafiğini oluşturur.

    Args:
        data: OHLCV piyasa verisi.
        currency_rate: Seçilen para biriminin dönüşüm oranı.
        current_price: Varlığın kendi para birimindeki güncel fiyatı.
        bear_target: Seçilen para birimine çevrilmiş ayı hedefi.
        bull_target: Seçilen para birimine çevrilmiş boğa hedefi.
        visible_periods: Grafikte gösterilecek son veri sayısı.

    Returns:
        Hazırlanmış Plotly grafiği.

    Raises:
        ValueError: Veri boşsa veya gerekli sütunlar yoksa.
    """
    if data is None or data.empty:
        raise ValueError("Fiyat grafiği için piyasa verisi bulunamadı.")

    missing_columns = REQUIRED_COLUMNS.difference(data.columns)

    if missing_columns:
        raise ValueError(
            "Grafik için eksik sütunlar: "
            + ", ".join(sorted(missing_columns))
        )

    if currency_rate <= 0:
        raise ValueError("Para birimi dönüşüm oranı sıfırdan büyük olmalıdır.")

    chart_data = data.tail(visible_periods).copy()

    price_columns = ["Open", "High", "Low", "Close"]
    chart_data[price_columns] = (
        chart_data[price_columns].astype(float) * currency_rate
    )

    chart_data["EMA20"] = (
        chart_data["Close"].ewm(span=20, adjust=False).mean()
    )
    chart_data["EMA50"] = (
        chart_data["Close"].ewm(span=50, adjust=False).mean()
    )
    chart_data["EMA200"] = (
        chart_data["Close"].ewm(span=200, adjust=False).mean()
    )

    converted_current_price = current_price * currency_rate

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.72, 0.28],
    )

    figure.add_trace(
        go.Candlestick(
            x=chart_data.index,
            open=chart_data["Open"],
            high=chart_data["High"],
            low=chart_data["Low"],
            close=chart_data["Close"],
            name="Fiyat",
        ),
        row=1,
        col=1,
    )

    figure.add_trace(
        go.Scatter(
            x=chart_data.index,
            y=chart_data["EMA20"],
            mode="lines",
            name="EMA 20",
            line={"color": "#00B0FF", "width": 1.2},
        ),
        row=1,
        col=1,
    )

    figure.add_trace(
        go.Scatter(
            x=chart_data.index,
            y=chart_data["EMA50"],
            mode="lines",
            name="EMA 50",
            line={"color": "#FF9100", "width": 1.4},
        ),
        row=1,
        col=1,
    )

    figure.add_trace(
        go.Scatter(
            x=chart_data.index,
            y=chart_data["EMA200"],
            mode="lines",
            name="EMA 200",
            line={
                "color": "#FFFFFF",
                "width": 1.6,
                "dash": "dot",
            },
        ),
        row=1,
        col=1,
    )

    if bear_target < converted_current_price:
        figure.add_hrect(
            y0=bear_target,
            y1=converted_current_price,
            fillcolor="#FF4D4D",
            opacity=0.06,
            layer="below",
            line_width=0,
            row=1,
            col=1,
        )

    if bull_target > converted_current_price:
        figure.add_hrect(
            y0=converted_current_price,
            y1=bull_target,
            fillcolor="#00FF88",
            opacity=0.06,
            layer="below",
            line_width=0,
            row=1,
            col=1,
        )

    volume_colors = [
        "#00FF88" if close >= open_price else "#FF4D4D"
        for open_price, close in zip(
            chart_data["Open"],
            chart_data["Close"],
        )
    ]

    figure.add_trace(
        go.Bar(
            x=chart_data.index,
            y=chart_data["Volume"],
            marker_color=volume_colors,
            name="Hacim",
        ),
        row=2,
        col=1,
    )

    figure.update_layout(
        template="plotly_dark",
        height=650,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        xaxis_rangeslider_visible=False,
        showlegend=True,
        hovermode="x unified",
        dragmode="pan",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
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

    figure.update_yaxes(
        title_text="Fiyat",
        row=1,
        col=1,
    )

    figure.update_yaxes(
        title_text="Hacim",
        row=2,
        col=1,
    )

    return figure