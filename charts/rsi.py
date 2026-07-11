"""
RSI hesaplama ve yorumlama yardımcıları.

RSI = Relative Strength Index
Türkçesi: Göreceli Güç Endeksi
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RSIResult:
    """RSI hesaplama sonucunu temsil eder."""

    value: float
    status: str
    message: str


def calculate_rsi(
    close_prices: pd.Series,
    period: int = 14,
) -> float:
    """
    Kapanış fiyatlarından RSI değerini hesaplar.

    Args:
        close_prices: Kapanış fiyatları.
        period: RSI hesaplama periyodu.

    Returns:
        Son RSI değeri.

    Raises:
        ValueError: Veri yetersizse veya periyot geçersizse.
    """
    if period <= 0:
        raise ValueError("RSI periyodu sıfırdan büyük olmalıdır.")

    if close_prices is None or len(close_prices) < period + 1:
        raise ValueError("RSI hesaplamak için yeterli veri bulunamadı.")

    prices = pd.to_numeric(close_prices, errors="coerce").dropna()

    if len(prices) < period + 1:
        raise ValueError("RSI hesaplamak için yeterli geçerli fiyat yok.")

    delta = prices.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    average_loss = losses.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    relative_strength = average_gain / average_loss.replace(0, 1e-12)

    rsi = 100 - (100 / (1 + relative_strength))

    latest_rsi = float(rsi.iloc[-1])

    return max(0.0, min(100.0, latest_rsi))


def analyze_rsi(
    close_prices: pd.Series,
    period: int = 14,
) -> RSIResult:
    """
    RSI değerini hesaplar ve anlaşılır yorum üretir.
    """
    value = calculate_rsi(close_prices, period)

    if value >= 70:
        return RSIResult(
            value=value,
            status="overbought",
            message=(
                f"RSI {value:.1f} seviyesinde. "
                "Fiyat son dönemde hızlı yükselmiş ve kısa vadede fazla ısınmış olabilir. "
                "Bu tek başına satış sinyali değildir."
            ),
        )

    if value <= 30:
        return RSIResult(
            value=value,
            status="oversold",
            message=(
                f"RSI {value:.1f} seviyesinde. "
                "Fiyat son dönemde hızlı düşmüş ve kısa vadede fazla zayıflamış olabilir. "
                "Bu tek başına alış sinyali değildir."
            ),
        )

    return RSIResult(
        value=value,
        status="neutral",
        message=(
            f"RSI {value:.1f} seviyesinde. "
            "Fiyat hareketinin hızı şu an orta bölgede; belirgin aşırı ısınma veya aşırı zayıflama görünmüyor."
        ),
    )
