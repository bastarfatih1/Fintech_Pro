"""
Hiyerarşik varlık kataloğu.

Bu dosya kullanıcı arayüzünde şu akışı sağlar:
Varlık sınıfı -> Piyasa/Grup -> Alt varlık.

Not: BIST listeleri prototip başlangıç listesidir. Endeks bileşenleri zamanla
 değişebilir; ticari sürümde sağlayıcıdan dinamik sembol listesi çekilmelidir.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterable, Mapping


# UI'da gösterilen isim -> analiz motorunda kullanılacak sembol
INSTRUMENT_CATALOG: "OrderedDict[str, OrderedDict[str, OrderedDict[str, str]]]" = OrderedDict(
    {
        "Hisse Senetleri": OrderedDict(
            {
                "BIST 30": OrderedDict(
                    {
                        "Tüpraş": "TUPRS.IS",
                        "THY": "THYAO.IS",
                        "Aselsan": "ASELS.IS",
                        "BİM Mağazalar": "BIMAS.IS",
                        "Koç Holding": "KCHOL.IS",
                        "Sabancı Holding": "SAHOL.IS",
                        "Ford Otosan": "FROTO.IS",
                        "Ereğli Demir Çelik": "EREGL.IS",
                        "Şişecam": "SISE.IS",
                        "Akbank": "AKBNK.IS",
                        "Garanti BBVA": "GARAN.IS",
                        "İş Bankası C": "ISCTR.IS",
                        "Yapı Kredi": "YKBNK.IS",
                        "Turkcell": "TCELL.IS",
                        "Pegasus": "PGSUS.IS",
                    }
                ),
                "BIST 100 - Sık Kullanılan": OrderedDict(
                    {
                        "Tüpraş": "TUPRS.IS",
                        "Türk Hava Yolları": "THYAO.IS",
                        "Aselsan": "ASELS.IS",
                        "BİM Mağazalar": "BIMAS.IS",
                        "Koç Holding": "KCHOL.IS",
                        "Sabancı Holding": "SAHOL.IS",
                        "Ford Otosan": "FROTO.IS",
                        "Ereğli Demir Çelik": "EREGL.IS",
                        "Şişecam": "SISE.IS",
                        "Akbank": "AKBNK.IS",
                        "Garanti BBVA": "GARAN.IS",
                        "İş Bankası C": "ISCTR.IS",
                        "Yapı Kredi": "YKBNK.IS",
                        "Turkcell": "TCELL.IS",
                        "Pegasus": "PGSUS.IS",
                        "Arçelik": "ARCLK.IS",
                        "Tofaş": "TOASO.IS",
                        "Petkim": "PETKM.IS",
                        "Migros": "MGROS.IS",
                        "Vestel": "VESTL.IS",
                        "Türk Telekom": "TTKOM.IS",
                        "Emlak Konut GYO": "EKGYO.IS",
                        "Kardemir D": "KRDMD.IS",
                        "Gübre Fabrikaları": "GUBRF.IS",
                        "Sasa Polyester": "SASA.IS",
                    }
                ),
                "ABD Hisseleri - Mega Cap": OrderedDict(
                    {
                        "Apple": "AAPL",
                        "Microsoft": "MSFT",
                        "Nvidia": "NVDA",
                        "Amazon": "AMZN",
                        "Alphabet A": "GOOGL",
                        "Meta Platforms": "META",
                        "Tesla": "TSLA",
                        "Netflix": "NFLX",
                        "Berkshire Hathaway B": "BRK.B",
                        "JPMorgan Chase": "JPM",
                        "Visa": "V",
                        "Mastercard": "MA",
                        "Coca-Cola": "KO",
                        "McDonald's": "MCD",
                        "Walmart": "WMT",
                    }
                ),
                "ABD ETF": OrderedDict(
                    {
                        "S&P 500 ETF - SPY": "SPY",
                        "Nasdaq 100 ETF - QQQ": "QQQ",
                        "Dow Jones ETF - DIA": "DIA",
                        "Russell 2000 ETF - IWM": "IWM",
                        "Gold ETF - GLD": "GLD",
                        "Silver ETF - SLV": "SLV",
                    }
                ),
            }
        ),
        "Endeksler": OrderedDict(
            {
                "Türkiye Endeksleri": OrderedDict(
                    {
                        "BIST 100 Endeksi": "XU100.IS",
                        "BIST 30 Endeksi": "XU030.IS",
                    }
                ),
                "ABD Endeksleri": OrderedDict(
                    {
                        "S&P 500": "SPY",
                        "Nasdaq 100": "QQQ",
                        "Dow Jones": "DIA",
                        "Russell 2000": "IWM",
                    }
                ),
            }
        ),
        "Kripto Para": OrderedDict(
            {
                "Büyük Kriptolar": OrderedDict(
                    {
                        "Bitcoin": "BTC-USD",
                        "Ethereum": "ETH-USD",
                        "BNB": "BNB-USD",
                        "Solana": "SOL-USD",
                        "XRP": "XRP-USD",
                        "Cardano": "ADA-USD",
                        "Dogecoin": "DOGE-USD",
                        "Avalanche": "AVAX-USD",
                        "Chainlink": "LINK-USD",
                        "Polygon": "MATIC-USD",
                    }
                ),
                "Stabil ve Majör Pariteler": OrderedDict(
                    {
                        "Bitcoin / USD": "BTC-USD",
                        "Ethereum / USD": "ETH-USD",
                    }
                ),
            }
        ),
        "Altın & Değerli Maden": OrderedDict(
            {
                "Türkiye Altınları": OrderedDict(
                    {
                        "Gram Altın - teorik": "GRAM_ALTIN_TRY",
                        "Külçe Altın 1g - teorik": "GRAM_ALTIN_TRY",
                        "22 Ayar Gram - prototip": "ALTIN_22_AYAR_TRY",
                        "Çeyrek Altın - prototip": "CEYREK_ALTIN_TRY",
                        "Yarım Altın - prototip": "YARIM_ALTIN_TRY",
                        "Tam Altın - prototip": "TAM_ALTIN_TRY",
                        "Cumhuriyet Altını - prototip": "CUMHURIYET_ALTINI_TRY",
                    }
                ),
                "Global Metaller": OrderedDict(
                    {
                        "Ons Altın / USD": "XAU/USD",
                        "Ons Gümüş / USD": "XAG/USD",
                        "Gold ETF - GLD": "GLD",
                        "Silver ETF - SLV": "SLV",
                    }
                ),
            }
        ),
        "Döviz": OrderedDict(
            {
                "TRY Pariteleri": OrderedDict(
                    {
                        "Dolar / TL": "USDTRY=X",
                        "Euro / TL": "EURTRY=X",
                        "Sterlin / TL": "GBPTRY=X",
                        "Japon Yeni / TL": "JPYTRY=X",
                    }
                ),
                "Majör Pariteler": OrderedDict(
                    {
                        "Euro / Dolar": "EUR/USD",
                        "Sterlin / Dolar": "GBP/USD",
                        "Dolar / Japon Yeni": "USD/JPY",
                    }
                ),
            }
        ),
        "Emtia": OrderedDict(
            {
                "Enerji": OrderedDict(
                    {
                        "Brent Petrol": "BZ=F",
                        "WTI Petrol": "CL=F",
                        "Doğal Gaz": "NG=F",
                    }
                ),
                "Tarım & Sanayi": OrderedDict(
                    {
                        "Bakır": "HG=F",
                        "Mısır": "ZC=F",
                        "Buğday": "ZW=F",
                    }
                ),
            }
        ),
    }
)


# Bu semboller TRY bazlıdır. Uygulamada tekrar USD/TRY ile çarpılmamalıdır.
TRY_BASED_SYMBOLS = {
    "GRAM_ALTIN_TRY",
    "ALTIN_22_AYAR_TRY",
    "CEYREK_ALTIN_TRY",
    "YARIM_ALTIN_TRY",
    "TAM_ALTIN_TRY",
    "CUMHURIYET_ALTINI_TRY",
    "USDTRY=X",
    "EURTRY=X",
    "GBPTRY=X",
    "JPYTRY=X",
    "XU100.IS",
    "XU030.IS",
}


# Altın ürünleri prototipte teorik katsayıyla gram altından türetilir.
# Çeyrek/tam/cumhuriyet altınlarında işçilik ve piyasa primi farklı olabilir.
GOLD_VARIANT_MULTIPLIERS = {
    "ALTIN_22_AYAR_TRY": 0.916,
    "CEYREK_ALTIN_TRY": 1.754,
    "YARIM_ALTIN_TRY": 3.508,
    "TAM_ALTIN_TRY": 7.016,
    "CUMHURIYET_ALTINI_TRY": 7.216,
}


def get_asset_classes() -> list[str]:
    return list(INSTRUMENT_CATALOG.keys())


def get_groups(asset_class: str) -> list[str]:
    return list(INSTRUMENT_CATALOG.get(asset_class, {}).keys())


def get_assets(asset_class: str, group: str) -> list[str]:
    return list(INSTRUMENT_CATALOG.get(asset_class, {}).get(group, {}).keys())


def get_symbol(asset_class: str, group: str, asset_name: str) -> str:
    return INSTRUMENT_CATALOG[asset_class][group][asset_name]


def flatten_instruments() -> dict[str, str]:
    """Geriye dönük uyumluluk için düz varlık listesi üretir."""
    flattened: dict[str, str] = {}
    for asset_class, groups in INSTRUMENT_CATALOG.items():
        for group, assets in groups.items():
            for asset_name, symbol in assets.items():
                key = f"{asset_name} · {group}"
                flattened[key] = symbol
    return flattened


def is_try_based_symbol(symbol: str) -> bool:
    if symbol in TRY_BASED_SYMBOLS:
        return True
    if symbol.endswith(".IS"):
        return True
    if symbol.endswith("_TRY"):
        return True
    return False
