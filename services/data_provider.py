"""
Veri sağlayıcı arayüzü.

Bu modül, prototip veri kaynakları ile ileride eklenecek lisanslı
üretim veri kaynakları arasında ortak bir sözleşme sağlar.

Sprint 3.13B kapsamı:
    - Henüz mevcut uygulama akışı değiştirilmez.
    - Sadece provider sözleşmesi ve Yahoo/yfinance prototip sağlayıcısı eklenir.
    - Üretim izni varsayılan olarak kapalıdır.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

import pandas as pd


@dataclass(frozen=True)
class DataSourceMetadata:
    """Bir veri sonucunun kaynak ve lisans bilgisini taşır."""

    source_name: str
    provider_type: str
    asset_type: str
    symbol: str
    retrieved_at: datetime
    data_delay: str
    license_status: str
    is_production_allowed: bool
    fallback_used: bool = False
    note: str = ""


@dataclass(frozen=True)
class MarketDataResult:
    """Piyasa verisi ve kaynak bilgisini birlikte taşır."""

    data: pd.DataFrame
    metadata: DataSourceMetadata

    @property
    def is_empty(self) -> bool:
        """Veri sonucunun boş olup olmadığını söyler."""
        return self.data is None or self.data.empty


class MarketDataProvider(Protocol):
    """Tüm piyasa veri sağlayıcılarının uyması gereken arayüz."""

    provider_name: str

    def get_history(
        self,
        symbol: str,
        period: str = "10y",
        asset_type: str = "stock",
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
    ) -> MarketDataResult:
        """Geçmiş OHLCV piyasa verisini döndürür."""


class YahooFinancePrototypeProvider:
    """
    yfinance tabanlı prototip piyasa veri sağlayıcısı.

    Bu sağlayıcı geliştirme ve demo amaçlıdır.
    Ticari üretim için lisans kontrolü yapılmadan kullanılmamalıdır.
    """

    provider_name = "Yahoo Finance via yfinance"

    def get_history(
        self,
        symbol: str,
        period: str = "10y",
        asset_type: str = "stock",
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
    ) -> MarketDataResult:
        """
        Yahoo Finance sembolü için geçmiş OHLCV verisini getirir.

        Hata durumunda boş DataFrame döner ancak metadata korunur.
        Böylece arayüz tarafı veri kaynağını kullanıcıya gösterebilir.
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)

            if start_date is not None or end_date is not None:
                data = ticker.history(
                    start=start_date,
                    end=end_date,
                )
            else:
                data = ticker.history(period=period)

            if data is None:
                data = pd.DataFrame()
        except Exception as exc:
            data = pd.DataFrame()
            note = f"yfinance veri çağrısı başarısız: {exc}"
        else:
            note = (
                "Prototip veri kaynağıdır. Ticari kullanım öncesi "
                "veri lisansı ayrıca doğrulanmalıdır."
            )

        metadata = DataSourceMetadata(
            source_name=self.provider_name,
            provider_type="prototype",
            asset_type=str(asset_type),
            symbol=str(symbol),
            retrieved_at=datetime.now(timezone.utc),
            data_delay="Bilinmiyor",
            license_status="Prototip / üretim lisansı doğrulanmadı",
            is_production_allowed=False,
            fallback_used=False,
            note=note,
        )

        return MarketDataResult(
            data=data,
            metadata=metadata,
        )


def get_default_market_data_provider() -> MarketDataProvider:
    """
    Varsayılan piyasa veri sağlayıcısını döndürür.

    Şimdilik prototip Yahoo/yfinance sağlayıcısı kullanılır.
    İleride burada ortam değişkeni veya konfigürasyon ile
    lisanslı sağlayıcı seçimi yapılacaktır.
    """
    return YahooFinancePrototypeProvider()


def get_market_history(
    symbol: str,
    period: str = "10y",
    asset_type: str = "stock",
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
    provider: Optional[MarketDataProvider] = None,
) -> MarketDataResult:
    """
    Piyasa verisini seçili sağlayıcıdan alır.

    Bu yardımcı fonksiyon, cache katmanının ve beta hesabının
    provider mimarisine bağlanmasını kolaylaştırır.

    period verilirse dönem bazlı veri alınır.
    start_date / end_date verilirse tarih aralığı bazlı veri alınır.
    """
    selected_provider = provider or get_default_market_data_provider()

    return selected_provider.get_history(
        symbol=symbol,
        period=period,
        asset_type=asset_type,
        start_date=start_date,
        end_date=end_date,
    )
