from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FactorSpec:
    name: str
    symbol: str
    group: str
    expected_role: str = ""
    transform: str = "log_return_1d"


BIST_STOCK_FACTORS = [
    FactorSpec("BIST 100 Getiri", "XU100.IS", "Piyasa", "Türkiye genel piyasa yönü"),
    FactorSpec("BIST 30 Getiri", "XU030.IS", "Piyasa", "Büyük ölçekli BIST hisseleri yönü"),
    FactorSpec("USDTRY Getiri", "USDTRY=X", "Kur", "Döviz kuru etkisi"),
    FactorSpec("EURTRY Getiri", "EURTRY=X", "Kur", "Euro kuru etkisi"),
    FactorSpec("Ons Altın Getiri", "GC=F", "Emtia", "Küresel altın/risksiz liman etkisi"),
    FactorSpec("Brent Petrol Getiri", "BZ=F", "Emtia", "Enerji ve maliyet etkisi"),
    FactorSpec("S&P 500 Getiri", "^GSPC", "Küresel Risk", "ABD piyasa yönü"),
    FactorSpec("Nasdaq Getiri", "^IXIC", "Küresel Risk", "Teknoloji/risk iştahı"),
    FactorSpec("VIX Getiri", "^VIX", "Risk", "Korku/volatilite endeksi"),
]

US_STOCK_FACTORS = [
    FactorSpec("S&P 500 Getiri", "^GSPC", "Piyasa", "ABD geniş piyasa yönü"),
    FactorSpec("Nasdaq Getiri", "^IXIC", "Piyasa", "Teknoloji/risk iştahı"),
    FactorSpec("VIX Getiri", "^VIX", "Risk", "Volatilite ve korku endeksi"),
    FactorSpec("DXY Getiri", "DX-Y.NYB", "Kur", "Dolar endeksi"),
    FactorSpec("ABD 10Y Getiri", "^TNX", "Faiz", "ABD 10 yıllık faiz etkisi"),
    FactorSpec("Ons Altın Getiri", "GC=F", "Emtia", "Altın etkisi"),
    FactorSpec("Brent Petrol Getiri", "BZ=F", "Emtia", "Enerji etkisi"),
]

CRYPTO_FACTORS = [
    FactorSpec("Bitcoin Getiri", "BTC-USD", "Kripto", "Kripto ana piyasa yönü"),
    FactorSpec("Ethereum Getiri", "ETH-USD", "Kripto", "Altcoin/akıllı kontrat piyasa yönü"),
    FactorSpec("Nasdaq Getiri", "^IXIC", "Küresel Risk", "Risk iştahı"),
    FactorSpec("S&P 500 Getiri", "^GSPC", "Küresel Risk", "ABD piyasa yönü"),
    FactorSpec("VIX Getiri", "^VIX", "Risk", "Volatilite/korku endeksi"),
    FactorSpec("DXY Getiri", "DX-Y.NYB", "Kur", "Dolar endeksi"),
]

GOLD_FACTORS = [
    FactorSpec("Ons Altın Getiri", "GC=F", "Altın", "Ana ons altın etkisi"),
    FactorSpec("USDTRY Getiri", "USDTRY=X", "Kur", "Gram altın için kur etkisi"),
    FactorSpec("EURTRY Getiri", "EURTRY=X", "Kur", "Euro/TL etkisi"),
    FactorSpec("DXY Getiri", "DX-Y.NYB", "Kur", "Dolar endeksi"),
    FactorSpec("ABD 10Y Getiri", "^TNX", "Faiz", "ABD faiz etkisi"),
    FactorSpec("VIX Getiri", "^VIX", "Risk", "Küresel risk etkisi"),
]


def get_factor_specs(market_symbol: str, asset_type: str | None = None) -> list[FactorSpec]:
    symbol = str(market_symbol or "").upper()

    if symbol == "GRAM_ALTIN_TRY" or "ALTIN" in symbol:
        return GOLD_FACTORS

    if symbol.endswith(".IS") or symbol.startswith("XU"):
        return BIST_STOCK_FACTORS

    if "-USD" in symbol or symbol in {"BTC", "ETH", "SOL"}:
        return CRYPTO_FACTORS

    return US_STOCK_FACTORS
