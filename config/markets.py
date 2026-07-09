"""
Market instruments configuration.

Bu dosya analiz edilecek finansal varlıkları ve sembollerini içerir.
"""

INSTRUMENTS = {
    "BIST 100": "XU100.IS",
    "Bitcoin (BTC)": "BTC-USD",
    "Altın (Ons)": "GC=F",
    "Gümüş (Ons)": "SI=F",
    "S&P 500": "^GSPC",
    "NVIDIA": "NVDA",
    "APPLE": "AAPL",
}

FORECAST_PERIODS = {
    "1 Ay": 30,
    "3 Ay": 90,
    "6 Ay": 180,
    "1 Yıl": 365,
    "3 Yıl": 1095,
    "5 Yıl": 1825,
}