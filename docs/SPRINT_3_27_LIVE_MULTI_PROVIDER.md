# Sprint 3.27 - Live Multi Provider Market Data

Bu sprint uygulamaya canlı/çok yakın fiyat sağlayıcı katmanı ekler.

Öncelik:
1. Twelve Data
2. Finnhub
3. CoinGecko
4. Alpha Vantage
5. Eski uygulama verisi / fallback

Secrets örneği:

```toml
MARKET_DATA_PROVIDER = "live"
TWELVE_DATA_API_KEY = "..."
FINNHUB_API_KEY = "..."
COINGECKO_API_KEY = "..."
ALPHA_VANTAGE_API_KEY = "..."
GRAM_ALTIN_OVERRIDE_ENABLED = "false"
```

Not: Gram Altın, XAU/USD ve USD/TRY verisinden türetilir. Bu nedenle Matriks/serbest piyasa gram altınla birebir aynı olmak zorunda değildir.
