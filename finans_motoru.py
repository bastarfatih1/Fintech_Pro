import logging
from dataclasses import dataclass
import os
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests
import warnings
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor
from statsmodels.tsa.arima.model import ARIMA
from risk.metrics import calculate_risk_metrics
from core.market_calendar import get_market_calendar_config
from services.data_provider import get_market_history
from services.eviews_regression_engine import build_multi_factor_ols_route, evaluate_multi_factor_ols_backtest
from forecast.backtest import (
    calculate_dynamic_model_weights,
    calculate_weighted_calibration_error,
    evaluate_arima_and_monte_carlo,
    evaluate_regression_models,
)

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

FALLBACK_CURRENCY_RATES = {
    "USD": 1.0,
    "TRY": 34.20,
    "EUR": 0.92,
    "CNY": 7.25,
    "RUB": 88.0,
    "SAR": 3.75,
    "KWD": 0.31,
    "JPY": 155.0,
}


@dataclass(frozen=True)
class CurrencyDataMetadata:
    """Döviz kuru sonucunun kaynak ve lisans bilgisini taşır."""

    source_name: str
    provider_type: str
    base_currency: str
    retrieved_at: datetime
    data_delay: str
    license_status: str
    is_production_allowed: bool
    fallback_used: bool = False
    note: str = ""


@dataclass(frozen=True)
class CurrencyDataResult:
    """Döviz kurları ve kaynak bilgisini birlikte taşır."""

    rates: dict[str, float]
    metadata: CurrencyDataMetadata


def _build_currency_metadata(
    source_name: str,
    provider_type: str,
    data_delay: str,
    license_status: str,
    is_production_allowed: bool,
    fallback_used: bool = False,
    note: str = "",
) -> CurrencyDataMetadata:
    """Döviz kuru metadata nesnesini standart biçimde oluşturur."""
    return CurrencyDataMetadata(
        source_name=source_name,
        provider_type=provider_type,
        base_currency="USD",
        retrieved_at=datetime.now(timezone.utc),
        data_delay=data_delay,
        license_status=license_status,
        is_production_allowed=is_production_allowed,
        fallback_used=fallback_used,
        note=note,
    )


def _fallback_currency_result(note: str) -> CurrencyDataResult:
    """Güvenli yedek kur tablosunu metadata ile birlikte döndürür."""
    metadata = _build_currency_metadata(
        source_name="Fallback currency table",
        provider_type="fallback",
        data_delay="Güncel piyasa verisi değildir",
        license_status="Sabit yedek değer / üretim için uygun değil",
        is_production_allowed=False,
        fallback_used=True,
        note=note,
    )

    return CurrencyDataResult(
        rates=FALLBACK_CURRENCY_RATES.copy(),
        metadata=metadata,
    )



def _load_local_env() -> None:
    """
    Proje kökündeki .env dosyasını ek paket gerektirmeden yükler.

    Mevcut sistem ortam değişkenleri korunur.
    """
    env_path = Path(__file__).resolve().parent / ".env"

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


_load_local_env()


def get_kurlar_with_metadata() -> CurrencyDataResult:
    """
    Güncel döviz kurlarını kaynak bilgisiyle birlikte getirir.

    API anahtarı EXCHANGE_RATE_API_KEY ortam değişkeninden okunur.
    Anahtar yoksa veya istek başarısız olursa güvenli yedek değerler döner.
    """
    api_key = os.getenv("EXCHANGE_RATE_API_KEY", "").strip()

    if not api_key:
        return _fallback_currency_result(
            "EXCHANGE_RATE_API_KEY bulunamadı. Sabit yedek kur tablosu kullanıldı."
        )

    url = (
        "https://v6.exchangerate-api.com/v6/"
        f"{api_key}/latest/USD"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        payload = response.json()
        rates = payload.get("conversion_rates", {})

        if not rates:
            return _fallback_currency_result(
                "ExchangeRate-API yanıtında conversion_rates alanı boş geldi."
            )

        selected_rates = {
            "USD": 1.0,
            "TRY": rates.get("TRY", FALLBACK_CURRENCY_RATES["TRY"]),
            "EUR": rates.get("EUR", FALLBACK_CURRENCY_RATES["EUR"]),
            "CNY": rates.get("CNY", FALLBACK_CURRENCY_RATES["CNY"]),
            "RUB": rates.get("RUB", FALLBACK_CURRENCY_RATES["RUB"]),
            "SAR": rates.get("SAR", FALLBACK_CURRENCY_RATES["SAR"]),
            "KWD": rates.get("KWD", FALLBACK_CURRENCY_RATES["KWD"]),
            "JPY": rates.get("JPY", FALLBACK_CURRENCY_RATES["JPY"]),
        }

        metadata = _build_currency_metadata(
            source_name="ExchangeRate-API",
            provider_type="api",
            data_delay=str(
                payload.get(
                    "time_last_update_utc",
                    "API yanıt zamanı belirtilmedi",
                )
            ),
            license_status=(
                "API planı ve ticari kullanım koşulları üretim öncesi "
                "doğrulanmalıdır"
            ),
            is_production_allowed=False,
            fallback_used=False,
            note=(
                "Döviz kuru verisi API üzerinden alındı. Ticari sürümde "
                "sağlayıcı planı, kota ve lisans koşulları ayrıca kontrol edilmelidir."
            ),
        )

        return CurrencyDataResult(
            rates=selected_rates,
            metadata=metadata,
        )
    except (requests.RequestException, ValueError, TypeError) as exc:
        return _fallback_currency_result(
            f"ExchangeRate-API çağrısı başarısız oldu. Sabit yedek kur tablosu kullanıldı. Hata: {exc}"
        )


def get_kurlar():
    """
    Güncel döviz kurlarını getirir.

    Geriye uyumluluk için sadece kur sözlüğü döndürür.
    Kaynak ve lisans bilgisi gereken yerlerde get_kurlar_with_metadata()
    kullanılmalıdır.
    """
    return get_kurlar_with_metadata().rates



def _prepare_forecast_dataframe(df: pd.DataFrame, minimum_rows: int = 80) -> pd.DataFrame:
    """
    Tüm model motoruna girmeden önce piyasa verisini güvenli hale getirir.
    Amaç: hiçbir varlıkta NaN / sonsuz / sıfır / negatif Close yüzünden model kırılmasın.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Analiz için piyasa verisi bulunamadı.")

    data = df.copy()

    if "Close" not in data.columns:
        raise ValueError("Analiz için Close fiyat sütunu bulunamadı.")

    numeric_columns = ["Open", "High", "Low", "Close", "Volume"]

    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
            data[col] = data[col].replace([np.inf, -np.inf], np.nan)

    data = data.dropna(subset=["Close"])
    data = data[data["Close"] > 0]

    if data.empty:
        raise ValueError("Analiz için geçerli pozitif kapanış fiyatı bulunamadı.")

    for col in ["Open", "High", "Low"]:
        if col not in data.columns:
            data[col] = data["Close"]
        else:
            data[col] = data[col].fillna(data["Close"])
            data.loc[data[col] <= 0, col] = data["Close"]

    if "Volume" not in data.columns:
        data["Volume"] = 0.0
    else:
        data["Volume"] = data["Volume"].fillna(0.0)

    data = data[~data.index.duplicated(keep="last")]
    data = data.sort_index()

    if len(data) < minimum_rows:
        raise ValueError(
            f"Analiz için yeterli geçmiş veri yok. Gerekli en az satır: {minimum_rows}, mevcut: {len(data)}."
        )

    return data

def volatile_path_generator(
    curr,
    target,
    days,
    daily_vol,
    random_state=42,
):
    """
    Başlangıç fiyatından hedef fiyata kontrollü ve pozitif rota üretir.

    Not:
        Bu rota gerçek model tahmini değildir.
        Yalnızca tek hedef fiyatın görselleştirilmesi içindir.
    """
    curr = float(curr)
    target = float(target)
    days = int(days)

    if days <= 0:
        return np.array([], dtype=float)

    if curr <= 0:
        raise ValueError("Başlangıç fiyatı pozitif olmalıdır.")

    if not np.isfinite(target) or target <= 0:
        target = curr

    if days == 1:
        return np.array([target], dtype=float)

    rng = np.random.default_rng(random_state)

    progress = np.linspace(0.0, 1.0, days)

    base_path = curr * np.exp(
        np.log(target / curr) * progress
    )

    noise = rng.normal(
        loc=0.0,
        scale=min(float(daily_vol), 0.05),
        size=days,
    )

    noise[0] = 0.0
    noise[-1] = 0.0

    noise = np.cumsum(noise)
    noise = noise - np.linspace(
        noise[0],
        noise[-1],
        days,
    )

    path = base_path * np.exp(noise)

    lower_limit = curr * 0.05
    upper_limit = curr * 20.0

    path = np.clip(
        path,
        lower_limit,
        upper_limit,
    )

    path[0] = curr
    path[-1] = target

    return path


def _build_calibrated_scenario_bands(
    consensus_path,
    current_price,
    daily_volatility,
    horizon,
    calibration_log_error,
    monte_carlo_lower=None,
    monte_carlo_upper=None,
    include_monte_carlo=False,
):
    """
    Backtest hata dağılımı ve tarihsel volatiliteyle senaryo bantları üretir.

    Bantlar çarpımsal log-fiyat ölçeğinde oluşturulur. Böylece alt bant
    sıfır veya negatif fiyat üretemez.
    """
    consensus = np.asarray(
        consensus_path,
        dtype=float,
    ).reshape(-1)
    horizon = int(horizon)
    current_price = float(current_price)

    if len(consensus) != horizon or horizon <= 0:
        raise ValueError("Senaryo bandı uzunluğu tahmin vadesiyle uyumsuz.")

    if (
        current_price <= 0
        or not np.isfinite(consensus).all()
        or np.any(consensus <= 0)
    ):
        raise ValueError("Senaryo bantları pozitif geçerli fiyat gerektirir.")

    volatility_error = (
        1.645
        * max(float(daily_volatility), 1e-6)
        * np.sqrt(horizon)
    )

    if (
        calibration_log_error is None
        or not np.isfinite(float(calibration_log_error))
        or float(calibration_log_error) < 0
    ):
        endpoint_log_error = volatility_error
        calibration_source = "Tarihsel volatilite yedeği"
    else:
        endpoint_log_error = max(
            float(calibration_log_error),
            volatility_error,
        )
        calibration_source = (
            "Backtest %90 log hata ve tarihsel volatilite"
        )

    # Sayısal taşmayı engeller; çok yüksek belirsizlik yine geniş bant üretir.
    endpoint_log_error = float(
        np.clip(endpoint_log_error, 0.01, 3.0)
    )

    progress = (
        np.arange(1, horizon + 1, dtype=float)
        / float(horizon)
    )
    widening = endpoint_log_error * np.sqrt(progress)

    lower = consensus * np.exp(-widening)
    upper = consensus * np.exp(widening)

    if include_monte_carlo:
        mc_lower = np.asarray(
            monte_carlo_lower,
            dtype=float,
        ).reshape(-1)
        mc_upper = np.asarray(
            monte_carlo_upper,
            dtype=float,
        ).reshape(-1)

        if (
            len(mc_lower) == horizon
            and len(mc_upper) == horizon
        ):
            valid_mc = (
                np.isfinite(mc_lower)
                & np.isfinite(mc_upper)
                & (mc_lower > 0)
                & (mc_upper > 0)
            )
            lower = np.where(
                valid_mc,
                np.minimum(lower, mc_lower),
                lower,
            )
            upper = np.where(
                valid_mc,
                np.maximum(upper, mc_upper),
                upper,
            )
            calibration_source += " + Monte Carlo %5-%95 zarfı"

    positive_floor = max(current_price * 0.01, 1e-9)
    lower = np.maximum(lower, positive_floor)
    lower = np.minimum(lower, consensus)
    upper = np.maximum(upper, consensus)

    return (
        lower,
        upper,
        endpoint_log_error,
        calibration_source,
    )



def _normalize_model_key(model_name):
    """Model adlarını eşleştirmek için sade anahtar üretir."""
    return (
        str(model_name)
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .lower()
    )


def _safe_numeric(value, default=0.0):
    """Sayısal değeri güvenli şekilde float'a çevirir."""
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return default
    return float(numeric)




def _normalize_model_key(model_name):
    """Model adlarını karşılaştırmak için sadeleştirir."""
    return (
        str(model_name or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )



def _normalize_backtest_status_columns(backtest_df):
    """
    Backtest tablolarında Durum kolonu eksik/boş gelirse standartlaştırır.
    Başarılı RMSE üreten aktif modelin Durum alanı boş kalmamalıdır.
    """
    if not isinstance(backtest_df, pd.DataFrame) or backtest_df.empty:
        return backtest_df

    df = backtest_df.copy()

    if "Durum" not in df.columns:
        df["Durum"] = ""

    for idx, row in df.iterrows():
        status = str(row.get("Durum", "")).strip()
        model = str(row.get("Model", "")).strip()
        rmse = _safe_numeric(row.get("RMSE"), default=np.nan)

        if status in {"", "-", "—", "None", "nan", "NaN"}:
            if model and np.isfinite(rmse) and rmse > 0:
                df.at[idx, "Durum"] = "başarılı"
            else:
                df.at[idx, "Durum"] = "bilinmiyor"

    return df


def _apply_strict_consensus_gate(
    model_weights,
    active_models,
    backtest_results,
    min_passed_weight=0.03,
):
    """
    Sprint 3.32A - Strict Consensus Gate Fix

    Kurallar:
    1. Referansı geçmeyen model konsensüse katılamaz.
    2. Referansı geçen aktif model ağırlığı 0 kalamaz.
    3. Ağırlıklar tekrar normalize edilir.
    """
    if not isinstance(backtest_results, pd.DataFrame) or backtest_results.empty:
        return {
            model_name: float(model_weights.get(model_name, 0.0))
            for model_name in active_models
        }

    if "Model" not in backtest_results.columns or "Referansı Geçti" not in backtest_results.columns:
        return {
            model_name: float(model_weights.get(model_name, 0.0))
            for model_name in active_models
        }

    active_models = list(active_models)
    active_key_map = {
        _normalize_model_key(model_name): model_name
        for model_name in active_models
    }

    passed_keys = set()

    for _, row in backtest_results.iterrows():
        model_raw = row.get("Model", "")
        passed_raw = str(row.get("Referansı Geçti", "")).strip().lower()

        model_key = _normalize_model_key(model_raw)

        if model_key in {"naive_last_price", "no_change_benchmark", "referans"}:
            continue

        if passed_raw == "evet" and model_key in active_key_map:
            passed_keys.add(model_key)

    if not passed_keys:
        raise RuntimeError(
            "Referans benchmarkı geçen aktif model yok. "
            "Konsensüs tahmini üretilmedi."
        )

    strict_weights = {}

    for model_name in active_models:
        model_key = _normalize_model_key(model_name)

        if model_key not in passed_keys:
            strict_weights[model_name] = 0.0
            continue

        old_weight = float(model_weights.get(model_name, 0.0) or 0.0)

        # Kritik düzeltme:
        # Model testi geçtiyse ağırlığı 0 kalamaz.
        strict_weights[model_name] = max(old_weight, float(min_passed_weight))

    total_weight = float(sum(strict_weights.values()))

    if total_weight <= 0:
        raise RuntimeError(
            "Konsensüs ağırlığı üretilemedi. "
            "Referansı geçen modeller ağırlık alamadı."
        )

    return {
        model_name: weight / total_weight
        for model_name, weight in strict_weights.items()
    }




def _add_consensus_explainability_columns(
    backtest_df,
    model_weights,
    active_models,
    model_statuses,
):
    """
    Sprint 3.32C - Consensus Explainability Layer

    Tabloda sadece Evet/Hayır göstermeyelim.
    Neden konsensüse girdi/girmedi açıkça yazalım.
    """
    if not isinstance(backtest_df, pd.DataFrame) or backtest_df.empty:
        return backtest_df

    if "Model" not in backtest_df.columns:
        return backtest_df

    enriched = backtest_df.copy()

    active_models = list(active_models)
    active_key_map = {
        _normalize_model_key(model_name): model_name
        for model_name in active_models
    }

    weight_key_map = {
        _normalize_model_key(model_name): float(weight or 0.0)
        for model_name, weight in dict(model_weights or {}).items()
    }

    status_key_map = {
        _normalize_model_key(model_name): status
        for model_name, status in dict(model_statuses or {}).items()
    }

    benchmark_keys = {
        "naive_last_price",
        "no_change_benchmark",
        "historical_drift_benchmark",
        "moving_average_benchmark",
        "referans",
    }

    reasons = []
    joins = []
    display_weights = []
    technical_statuses = []
    rmse_ratios = []
    rmse_scores = []

    for _, row in enriched.iterrows():
        model_name = row.get("Model", "")
        model_key = _normalize_model_key(model_name)

        is_benchmark = model_key in benchmark_keys
        active = model_key in active_key_map
        weight = float(weight_key_map.get(model_key, 0.0) or 0.0)

        status_obj = status_key_map.get(model_key, {})
        if isinstance(status_obj, dict):
            technical_status = str(status_obj.get("durum", "bilinmiyor"))
            technical_error = str(status_obj.get("hata", "") or "")
        else:
            technical_status = str(status_obj or "bilinmiyor")
            technical_error = ""

        passed_raw = str(row.get("Referansı Geçti", "")).strip().lower()
        passed = passed_raw == "evet"

        rmse = np.nan
        ref_rmse = np.nan

        try:
            rmse = float(row.get("RMSE", np.nan))
        except Exception:
            rmse = np.nan

        try:
            ref_rmse = float(row.get("Referans RMSE", np.nan))
        except Exception:
            ref_rmse = np.nan

        if np.isfinite(rmse) and np.isfinite(ref_rmse) and ref_rmse > 0:
            rmse_ratio = rmse / ref_rmse
            rmse_score = max(0.0, min(100.0, (1.0 - rmse_ratio) * 100.0))
        else:
            rmse_ratio = np.nan
            rmse_score = np.nan

        if is_benchmark:
            join = "Hayır"
            reason = "Kontrol benchmarkı; tahmin modeli olmadığı için konsensüse katılmaz."
            display_weight = 0.0
        elif not active:
            join = "Hayır"
            reason = "Aktif model rotası üretmedi veya model listesinde yok."
            display_weight = 0.0
        elif technical_status != "başarılı":
            join = "Hayır"
            reason = "Model teknik olarak geçerli rota üretemedi."
            if technical_error:
                reason += f" Hata: {technical_error}"
            display_weight = 0.0
        elif not passed:
            join = "Hayır"
            reason = "Benchmark testini geçemedi; bu yüzden konsensüse alınmadı."
            display_weight = 0.0
        elif weight <= 0:
            join = "Hayır"
            reason = (
                "Model testi geçti ama ağırlık skoru 0 kaldı. "
                "Bu durum mantıksal kontrol gerektirir."
            )
            display_weight = 0.0
        else:
            join = "Evet"
            reason = "Model testi geçti ve pozitif konsensüs ağırlığı aldı."
            display_weight = weight * 100.0

        reasons.append(reason)
        joins.append(join)
        display_weights.append(round(display_weight, 4))
        technical_statuses.append(technical_status)
        rmse_ratios.append(round(rmse_ratio, 4) if np.isfinite(rmse_ratio) else np.nan)
        rmse_scores.append(round(rmse_score, 2) if np.isfinite(rmse_score) else np.nan)

    enriched["Teknik Durum"] = technical_statuses
    enriched["RMSE / Referans RMSE"] = rmse_ratios
    enriched["RMSE Skoru"] = rmse_scores
    enriched["Konsensüs Ağırlığı %"] = display_weights
    enriched["Konsensüse Katılıyor"] = joins
    enriched["Konsensüse Girememe Nedeni"] = reasons

    return enriched


def _ensure_diversified_consensus_weights(
    model_weights,
    active_models,
    backtest_results,
):
    """
    Konsensüsün tek modele kilitlenmesini engeller.

    İlk ağırlık sistemi hâlâ ana karar vericidir. Ancak yalnızca tek model
    ağırlık alırsa, çalışan diğer modeller geçmiş hata, yön doğruluğu ve
    stabilite skoruna göre sınırlı katkı alır. Böylece grafik tek modelin
    çizgisine dönüşmez; çoklu model görünümü korunur.
    """
    active = [str(model_name) for model_name in active_models]
    if not active:
        return {}

    cleaned = {}
    for model_name in active:
        try:
            cleaned[model_name] = max(float(model_weights.get(model_name, 0.0)), 0.0)
        except (TypeError, ValueError):
            cleaned[model_name] = 0.0

    positive_models = [
        model_name
        for model_name, weight in cleaned.items()
        if weight > 0
    ]

    total_current = sum(cleaned.values())
    if len(positive_models) >= 2 and total_current > 0:
        return {
            model_name: weight / total_current
            for model_name, weight in cleaned.items()
        }

    row_lookup = {}
    rmse_values = []

    if isinstance(backtest_results, pd.DataFrame) and not backtest_results.empty:
        for _, row in backtest_results.iterrows():
            model_name = str(row.get("Model", ""))
            if _normalize_model_key(model_name) == "naive last price":
                continue

            key = _normalize_model_key(model_name)
            row_lookup[key] = row

            rmse = _safe_numeric(row.get("RMSE"), default=0.0)
            status = str(row.get("Durum", "")).lower()
            if rmse > 0 and (not status or status == "başarılı"):
                rmse_values.append(rmse)

    best_rmse = min(rmse_values) if rmse_values else None

    candidate_scores = {}
    for model_name in active:
        key = _normalize_model_key(model_name)
        row = row_lookup.get(key)

        if row is None:
            candidate_scores[model_name] = 0.05
            continue

        status = str(row.get("Durum", "")).lower()
        if status and status != "başarılı":
            candidate_scores[model_name] = 0.01
            continue

        rmse = _safe_numeric(row.get("RMSE"), default=0.0)
        direction = _safe_numeric(row.get("Yön Doğruluğu %"), default=50.0)
        stability = _safe_numeric(row.get("Stabilite Skoru"), default=50.0)
        improvement = _safe_numeric(row.get("RMSE İyileşme %"), default=0.0)
        passed = str(row.get("Referansı Geçti", "")).lower() == "evet"

        rmse_score = 0.20
        if best_rmse and rmse > 0:
            rmse_score = min(best_rmse / rmse, 1.0)

        direction_score = max(0.0, min(direction / 100.0, 1.0))
        stability_score = max(0.0, min(stability / 100.0, 1.0))
        improvement_score = max(0.0, min((improvement + 100.0) / 200.0, 1.0))
        pass_bonus = 1.0 if passed else 0.55

        candidate_scores[model_name] = max(
            0.01,
            rmse_score * 0.35
            + direction_score * 0.25
            + stability_score * 0.25
            + improvement_score * 0.10
            + pass_bonus * 0.05,
        )

    if not candidate_scores:
        equal_weight = 1.0 / len(active)
        return {model_name: equal_weight for model_name in active}

    if len(positive_models) == 1 and len(active) > 1:
        winner = positive_models[0]
        other_models = [
            model_name
            for model_name in active
            if model_name != winner
        ]

        diversified = {model_name: 0.0 for model_name in active}
        other_score_total = sum(
            candidate_scores.get(model_name, 0.0)
            for model_name in other_models
        )

        remaining_share = 0.50
        if other_score_total > 0:
            for model_name in other_models:
                raw_share = (
                    remaining_share
                    * candidate_scores.get(model_name, 0.0)
                    / other_score_total
                )
                diversified[model_name] = min(raw_share, 0.16)

        diversified[winner] = max(0.0, 1.0 - sum(diversified.values()))

        total = sum(diversified.values())
        if total > 0:
            return {
                model_name: weight / total
                for model_name, weight in diversified.items()
            }

    score_total = sum(candidate_scores.values())
    if score_total <= 0:
        equal_weight = 1.0 / len(active)
        return {model_name: equal_weight for model_name in active}

    return {
        model_name: candidate_scores.get(model_name, 0.0) / score_total
        for model_name in active
    }


def destek_direnc_bul(df, window=20):
    destek = df['Low'].rolling(window=window).min().iloc[-1]
    direnc = df['High'].rolling(window=window).max().iloc[-1]
    return destek, direnc

def get_sp500_data(start_date, end_date):
    """
    S&P 500 kapanış verisini provider katmanı üzerinden güvenli şekilde getirir.

    Beta hesabı için kullanılan ^GSPC verisi artık doğrudan yfinance ile
    çekilmez. Böylece ileride lisanslı veya farklı bir endeks sağlayıcısına
    geçiş tek provider katmanından yapılabilir.
    """
    try:
        result = get_market_history(
            symbol="^GSPC",
            asset_type="index",
            start_date=start_date,
            end_date=end_date,
        )

        if result.is_empty or "Close" not in result.data.columns:
            return pd.Series(dtype=float)

        return result.data["Close"]
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        logger.warning("S&P 500 verisi alınamadı: %s", exc)
        return pd.Series(dtype=float)

def hesapla_gecmis_performans(data, curr, ana_para, kur_val, s):
    try:
        close_prices = data['Close']
        son = float(close_prices.iloc[-1])
        periyotlar = [
            ("1 Hafta Önce", 7), ("1 Ay Önce", 30), ("3 Ay Önce", 90),
            ("6 Ay Önce", 180), ("1 Yıl Önce", 252), ("3 Yıl Önce", 252 * 3), ("5 Yıl Önce", 252 * 5)
        ]
        gecmis_tablo = []
        for etiket, gun in periyotlar:
            if len(close_prices) >= gun:
                eski_fiyat = float(close_prices.iloc[-gun])
                degisim = ((son - eski_fiyat) / eski_fiyat) * 100
                sermaye_degeri = ana_para * (son / eski_fiyat) if eski_fiyat != 0 else ana_para
                yil_katsayisi = gun / 365
                enflasyon_etkisi = (1.035 ** yil_katsayisi) - 1
                reel_getiri = degisim - (enflasyon_etkisi * 100)
                gecmis_tablo.append({
                    "Dönem": etiket,
                    "Eski Fiyat": f"{eski_fiyat * kur_val:,.2f} {s}",
                    "Güncel Fiyat": f"{son * kur_val:,.2f} {s}",
                    "Nominal Getiri": f"{degisim:+.2f}%",
                    "Reel Getiri": f"{reel_getiri:+.2f}%",
                    "Sermaye Değeri": f"{sermaye_degeri:,.2f} {s}"
                })
        return pd.DataFrame(gecmis_tablo)
    except Exception:
        return pd.DataFrame([{"Dönem": "Veri Yok", "Eski Fiyat": "-", "Güncel Fiyat": "-", "Nominal Getiri": "-", "Reel Getiri": "-", "Sermaye Değeri": "-"}])


def _clip01(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0

    if not np.isfinite(value):
        return 0.0

    return max(0.0, min(value, 1.0))


def _model_horizon_profile(model_name, horizon_days):
    """
    Modelin hangi vadede daha anlamlı kullanılacağını gösteren profil katsayısı.
    Bu katsayı tek başına karar vermez; RMSE, yön doğruluğu, stabilite ve benchmark sonucu
    ile birlikte çalışır.
    """
    key = _normalize_model_key(model_name)
    d = int(horizon_days or 1)

    if d <= 5:
        profile = {
            "arima": 1.25,
            "monte_carlo": 0.85,
            "linear_regression": 0.85,
            "multi_factor_ols": 0.80,
            "random_forest": 0.75,
            "xgboost": 0.75,
            "svr": 0.65,
        }
    elif d <= 20:
        profile = {
            "arima": 1.15,
            "monte_carlo": 0.95,
            "linear_regression": 0.95,
            "multi_factor_ols": 0.95,
            "random_forest": 0.85,
            "xgboost": 0.85,
            "svr": 0.70,
        }
    elif d <= 126:
        profile = {
            "multi_factor_ols": 1.25,
            "linear_regression": 1.10,
            "monte_carlo": 1.00,
            "arima": 0.90,
            "random_forest": 0.90,
            "xgboost": 0.90,
            "svr": 0.75,
        }
    elif d <= 252:
        profile = {
            "multi_factor_ols": 1.35,
            "linear_regression": 1.10,
            "monte_carlo": 1.05,
            "random_forest": 0.90,
            "xgboost": 0.90,
            "arima": 0.75,
            "svr": 0.70,
        }
    else:
        profile = {
            "multi_factor_ols": 1.50,
            "monte_carlo": 1.10,
            "linear_regression": 0.95,
            "random_forest": 0.75,
            "xgboost": 0.75,
            "arima": 0.55,
            "svr": 0.65,
        }

    return float(profile.get(key, 0.70))


def _collect_backtest_metrics(backtest_df):
    metrics = {}

    if not isinstance(backtest_df, pd.DataFrame) or backtest_df.empty:
        return metrics

    if "Model" not in backtest_df.columns:
        return metrics

    for _, row in backtest_df.iterrows():
        model_name = str(row.get("Model", ""))
        key = _normalize_model_key(model_name)

        if key in {
            "naive_last_price",
            "no_change_benchmark",
            "historical_drift_benchmark",
            "moving_average_benchmark",
            "referans",
        }:
            continue

        metrics[key] = {
            "model_name": model_name,
            "status": str(row.get("Durum", "")).strip().lower(),
            "passed": str(row.get("Referansı Geçti", "")).strip().lower() == "evet",
            "rmse": _safe_numeric(row.get("RMSE"), default=np.nan),
            "benchmark_rmse": _safe_numeric(row.get("Benchmark RMSE"), default=np.nan),
            "improvement": _safe_numeric(row.get("RMSE İyileşme %"), default=0.0),
            "direction": _safe_numeric(row.get("Yön Doğruluğu %"), default=50.0),
            "stability": _safe_numeric(row.get("Stabilite Skoru"), default=50.0),
        }

    return metrics


def _score_model_for_horizon(model_name, model_metrics, best_rmse, horizon_days):
    key = _normalize_model_key(model_name)
    row = model_metrics.get(key, {})

    status = str(row.get("status", "")).lower()
    if status and status not in {"başarılı", "basarili", "success", "successful"}:
        return 0.0

    rmse = _safe_numeric(row.get("rmse"), default=np.nan)
    benchmark_rmse = _safe_numeric(row.get("benchmark_rmse"), default=np.nan)
    direction = _safe_numeric(row.get("direction"), default=50.0)
    stability = _safe_numeric(row.get("stability"), default=50.0)
    improvement = _safe_numeric(row.get("improvement"), default=0.0)
    passed = bool(row.get("passed", False))

    if np.isfinite(rmse) and rmse > 0 and np.isfinite(best_rmse) and best_rmse > 0:
        rmse_score = _clip01(best_rmse / rmse)
    else:
        rmse_score = 0.20

    direction_score = _clip01(direction / 100.0)
    stability_score = _clip01(stability / 100.0)

    # -100 kötü, 0 nötr, +100 çok iyi olacak şekilde yumuşak skor.
    improvement_score = _clip01((improvement + 100.0) / 200.0)

    profile_score = _model_horizon_profile(model_name, horizon_days)

    if passed:
        pass_multiplier = 1.00
    else:
        # Benchmarkı geçemeyen model lider olamaz; ama vade profilinde bilgi taşıyorsa
        # sınırlı destek ağırlığı alabilir.
        rmse_ratio = np.inf
        if np.isfinite(rmse) and rmse > 0 and np.isfinite(benchmark_rmse) and benchmark_rmse > 0:
            rmse_ratio = rmse / benchmark_rmse

        if rmse_ratio <= 1.08:
            pass_multiplier = 0.42
        elif rmse_ratio <= 1.25:
            pass_multiplier = 0.28
        else:
            pass_multiplier = 0.12

    score = (
        (0.48 * rmse_score)
        + (0.22 * direction_score)
        + (0.18 * stability_score)
        + (0.12 * improvement_score)
    )

    score *= profile_score
    score *= pass_multiplier

    return max(float(score), 0.0)


def _normalize_weight_dict(weights):
    cleaned = {}

    for model_name, weight in dict(weights or {}).items():
        try:
            value = float(weight)
        except (TypeError, ValueError):
            value = 0.0

        if not np.isfinite(value) or value < 0:
            value = 0.0

        cleaned[model_name] = value

    total = float(sum(cleaned.values()))

    if total <= 0:
        return {
            model_name: 0.0
            for model_name in cleaned.keys()
        }

    return {
        model_name: weight / total
        for model_name, weight in cleaned.items()
    }


def _cap_failed_model_weight(weights, model_metrics, max_failed_total=0.35):
    """
    Benchmarkı geçemeyen modeller tamamen yok edilmez; ama toplam etkileri sınırlanır.
    Böylece tek modele kilitlenme azalır, ama başarısız modeller konsensüsü ele geçiremez.
    """
    weights = _normalize_weight_dict(weights)

    passed_total = 0.0
    failed_total = 0.0

    for model_name, weight in weights.items():
        key = _normalize_model_key(model_name)
        passed = bool(model_metrics.get(key, {}).get("passed", False))

        if passed:
            passed_total += weight
        else:
            failed_total += weight

    if passed_total <= 0 or failed_total <= max_failed_total:
        return weights

    failed_scale = max_failed_total / failed_total
    passed_scale = (1.0 - max_failed_total) / passed_total

    capped = {}

    for model_name, weight in weights.items():
        key = _normalize_model_key(model_name)
        passed = bool(model_metrics.get(key, {}).get("passed", False))

        if passed:
            capped[model_name] = weight * passed_scale
        else:
            capped[model_name] = weight * failed_scale

    return _normalize_weight_dict(capped)


def _weights_for_horizon(rotalar, backtest_df, horizon_days):
    model_metrics = _collect_backtest_metrics(backtest_df)

    rmse_values = [
        row.get("rmse")
        for row in model_metrics.values()
        if np.isfinite(row.get("rmse", np.nan)) and row.get("rmse", np.nan) > 0
    ]

    best_rmse = min(rmse_values) if rmse_values else np.nan

    raw_weights = {}

    for model_name, route in dict(rotalar or {}).items():
        try:
            route_array = np.asarray(route, dtype=float)
        except Exception:
            continue

        idx = int(horizon_days) - 1

        if idx < 0 or idx >= len(route_array):
            continue

        value = route_array[idx]

        if not np.isfinite(value) or value <= 0:
            continue

        raw_weights[model_name] = _score_model_for_horizon(
            model_name=model_name,
            model_metrics=model_metrics,
            best_rmse=best_rmse,
            horizon_days=horizon_days,
        )

    # Eğer tüm skorlar sıfırlandıysa, veri üreten modellerden en iyi RMSE'ye yakın olanlara
    # çok düşük ama normalize edilebilir bir skor ver.
    if sum(raw_weights.values()) <= 0:
        for model_name in raw_weights.keys():
            raw_weights[model_name] = 0.01

    weights = _normalize_weight_dict(raw_weights)
    weights = _cap_failed_model_weight(weights, model_metrics=model_metrics)

    return weights


def _leader_from_weights(weights):
    if not weights:
        return "-", 0.0, 0

    positive = {
        model_name: float(weight)
        for model_name, weight in weights.items()
        if float(weight) > 0.0001
    }

    if not positive:
        return "-", 0.0, 0

    leader = max(positive, key=positive.get)

    return leader, float(positive[leader]), len(positive)


def _average_weight_dict(weight_dicts):
    accumulator = {}
    count = 0

    for weights in weight_dicts:
        if not isinstance(weights, dict) or not weights:
            continue

        count += 1

        for model_name, weight in weights.items():
            accumulator[model_name] = accumulator.get(model_name, 0.0) + float(weight)

    if count <= 0:
        return {}

    averaged = {
        model_name: weight / count
        for model_name, weight in accumulator.items()
    }

    return _normalize_weight_dict(averaged)


def _build_horizon_aware_consensus_path(
    rotalar,
    backtest_df,
    periyot_gun,
    target_horizons,
):
    """
    Tek genel ağırlık yerine, her gün/vade için ayrı model ağırlığı üretir.
    Kısa vadede kısa vade profili güçlü modeller, uzun vadede faktör/uzun vade profili
    güçlü modeller daha fazla söz sahibi olur.
    """
    if not rotalar:
        raise RuntimeError("Vade bazlı konsensüs için geçerli model rotası bulunamadı.")

    consensus_path = np.zeros(int(periyot_gun), dtype=float)
    daily_weights = []

    for day in range(1, int(periyot_gun) + 1):
        weights = _weights_for_horizon(
            rotalar=rotalar,
            backtest_df=backtest_df,
            horizon_days=day,
        )

        value = 0.0
        total = 0.0

        for model_name, weight in weights.items():
            if weight <= 0:
                continue

            route = np.asarray(rotalar[model_name], dtype=float)

            if day - 1 >= len(route):
                continue

            route_value = route[day - 1]

            if not np.isfinite(route_value) or route_value <= 0:
                continue

            value += float(route_value) * float(weight)
            total += float(weight)

        if total <= 0:
            raise RuntimeError(
                f"{day}. gün için vade bazlı konsensüs ağırlığı üretilemedi."
            )

        consensus_path[day - 1] = value / total
        daily_weights.append(weights)

    if not np.isfinite(consensus_path).all() or np.any(consensus_path <= 0):
        raise RuntimeError("Vade bazlı konsensüs rotası geçersiz değer üretti.")

    horizon_model_weights = {}
    horizon_summary = []

    for label, days in list(target_horizons or []):
        if int(days) > int(periyot_gun):
            continue

        weights = _weights_for_horizon(
            rotalar=rotalar,
            backtest_df=backtest_df,
            horizon_days=int(days),
        )

        leader, leader_weight, active_count = _leader_from_weights(weights)

        horizon_model_weights[str(label)] = weights
        horizon_summary.append(
            {
                "Vade": str(label),
                "Gün": int(days),
                "Konsensüse Giren Model": int(active_count),
                "Lider Model": str(leader),
                "Lider Ağırlık %": round(float(leader_weight) * 100.0, 2),
                "Ağırlık Dağılımı": ", ".join(
                    [
                        f"{model}: %{weight * 100.0:.1f}"
                        for model, weight in sorted(
                            weights.items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                        if weight > 0.0001
                    ]
                ),
            }
        )

    average_weights = _average_weight_dict(
        horizon_model_weights.values()
        if horizon_model_weights
        else daily_weights
    )

    return consensus_path, average_weights, horizon_model_weights, horizon_summary


def gelecek_senaryolari_hesapla(
    data,
    periyot_gun,
    ana_para,
    curr,
    kur_val=1.0,
    asset_type=None,
    market_symbol=None,
):
    calendar_config = get_market_calendar_config(
        asset_type=asset_type,
        market_symbol=market_symbol,
    )
    df = _prepare_forecast_dataframe(data)
    curr = float(pd.to_numeric(df["Close"], errors="coerce").dropna().iloc[-1])
    df['Lag_1'] = df['Close'].shift(1)
    df['Lag_2'] = df['Close'].shift(2)
    df['Lag_3'] = df['Close'].shift(3)
    df['MA_14'] = df['Close'].rolling(window=14).mean()
    df['Vol_14'] = df['Close'].rolling(window=14).std()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['Target'] = df['Close'].shift(-periyot_gun)
    
    features = ['Lag_1', 'Lag_2', 'Lag_3', 'MA_14', 'Vol_14', 'RSI']
    train_df = df.dropna(subset=features + ['Target'])
    latest_features = df.dropna(subset=features)
    
    if not latest_features.empty:
        X_latest = latest_features[features].iloc[-1].values.reshape(1, -1)
    else:
        X_latest = np.zeros((1, len(features)))
        
    rotalar = {}
    model_durumlari = {}
    rota_turleri = {}

    hist_prices = df["Close"].dropna().values
    log_returns = np.log(hist_prices[1:] / hist_prices[:-1])
    daily_vol = np.std(log_returns) if np.std(log_returns) > 0 else 0.01

    if train_df.empty:
        raise ValueError(
            "Seçilen tahmin vadesi için yeterli eğitim verisi bulunamadı."
        )

    backtest_frames = []
    backtest_messages = []

    try:
        regression_backtest = evaluate_regression_models(
            data=train_df,
            features=features,
            target_column="Target",
            reference_column="Close",
        )
        backtest_frames.append(regression_backtest)
    except ValueError as exc:
        logger.warning("Regresyon backtesti çalıştırılamadı: %s", exc)
        backtest_messages.append(f"Regresyon: {exc}")

    try:
        time_series_backtest = evaluate_arima_and_monte_carlo(
            close_prices=df["Close"],
            horizon=periyot_gun,
        )
        backtest_frames.append(time_series_backtest)
    except ValueError as exc:
        logger.warning(
            "ARIMA/Monte Carlo backtesti çalıştırılamadı: %s",
            exc,
        )
        backtest_messages.append(f"ARIMA/Monte Carlo: {exc}")

    if backtest_frames:
        backtest_df = pd.concat(
            backtest_frames,
            ignore_index=True,
            sort=False,
        )
        if "Model" in backtest_df.columns:
            backtest_df = backtest_df.drop_duplicates(
                subset=["Model"],
                keep="first",
            ).reset_index(drop=True)
        backtest_status = (
            "tamamlandı"
            if not backtest_messages
            else "kısmi: " + " | ".join(backtest_messages)
        )
    else:
        backtest_df = pd.DataFrame(
            columns=[
                "Model",
                "MAE",
                "RMSE",
                "Yön Doğruluğu %",
                "Test Gözlemi",
                "Durum",
                "Backtest Türü",
                "Hata",
            ]
        )
        backtest_status = (
            " | ".join(backtest_messages)
            or "Backtest sonucu üretilemedi."
        )

    def kaydet_basarili_model(
        model_adi,
        rota,
        rota_turu="Model Tahmin Rotası",
    ):
        """Başarılı model rotasını doğrular ve kaydeder."""
        rota = np.asarray(rota, dtype=float).reshape(-1)

        if len(rota) != periyot_gun:
            raise ValueError(
                f"{model_adi} rota uzunluğu beklenen vadeyle uyumlu değil."
            )

        if not np.isfinite(rota).all():
            raise ValueError(
                f"{model_adi} geçersiz sayısal değer üretti."
            )

        if np.any(rota <= 0):
            raise ValueError(
                f"{model_adi} sıfır veya negatif fiyat üretti."
            )

        rotalar[model_adi] = rota
        rota_turleri[model_adi] = rota_turu
        model_durumlari[model_adi] = {
            "durum": "başarılı",
            "hata": None,
        }

    def kaydet_basarisiz_model(model_adi, hata):
        """Başarısız modeli konsensüsten çıkarır ve hata bilgisini kaydeder."""
        logger.debug("%s modeli başarısız: %s", model_adi, hata)
        model_durumlari[model_adi] = {
            "durum": "başarısız",
            "hata": str(hata),
        }

    try:
        multi_factor_ols_route = build_multi_factor_ols_route(
            target_data=df,
            forecast_days=periyot_gun,
            current_price=curr,
            market_symbol=market_symbol or "",
            asset_name=str(market_symbol or "Seçilen Varlık"),
            asset_type=asset_type,
        )
        kaydet_basarili_model(
            "Multi_Factor_OLS",
            multi_factor_ols_route,
            rota_turu="Dynamic Factor Intelligence OLS Rotası",
        )
    except (
        ValueError,
        TypeError,
        FloatingPointError,
        RuntimeError,
        KeyError,
        ImportError,
    ) as exc:
        kaydet_basarisiz_model("Multi_Factor_OLS", exc)

    try:
        lr = LinearRegression()
        lr.fit(train_df[features], train_df["Target"])
        lr_target = float(lr.predict(X_latest)[0])
        kaydet_basarili_model(
            "Linear_Regression",
            volatile_path_generator(
                curr,
                lr_target,
                periyot_gun,
                daily_vol,
                random_state=11,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("Linear_Regression", exc)

    try:
        rf = RandomForestRegressor(
            n_estimators=50,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(train_df[features], train_df["Target"])
        rf_target = float(rf.predict(X_latest)[0])
        kaydet_basarili_model(
            "Random_Forest",
            volatile_path_generator(
                curr,
                rf_target,
                periyot_gun,
                daily_vol,
                random_state=22,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("Random_Forest", exc)

    try:
        svr = SVR(C=1.0, epsilon=0.2)
        svr.fit(train_df[features], train_df["Target"])
        svr_target = float(svr.predict(X_latest)[0])
        kaydet_basarili_model(
            "SVR",
            volatile_path_generator(
                curr,
                svr_target,
                periyot_gun,
                daily_vol,
                random_state=33,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("SVR", exc)

    try:
        xgb = XGBRegressor(
            n_estimators=50,
            random_state=42,
            n_jobs=-1,
        )
        xgb.fit(train_df[features], train_df["Target"])
        xgb_target = float(xgb.predict(X_latest)[0])
        kaydet_basarili_model(
            "XGBoost",
            volatile_path_generator(
                curr,
                xgb_target,
                periyot_gun,
                daily_vol,
                random_state=44,
            ),
            rota_turu="Görsel Senaryo Rotası",
        )
    except (ValueError, TypeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("XGBoost", exc)

    try:
        arima_model = ARIMA(hist_prices, order=(1, 1, 1))
        arima_fit = arima_model.fit()
        kaydet_basarili_model(
            "ARIMA",
            arima_fit.forecast(steps=periyot_gun),
        )
    except (ValueError, TypeError, RuntimeError, FloatingPointError) as exc:
        kaydet_basarisiz_model("ARIMA", exc)

    n_sim = 10000

    try:
        rng = np.random.default_rng(55)
        mu = np.mean(log_returns)
        z_values = rng.normal(0, 1, (n_sim, periyot_gun))
        drift = mu - 0.5 * (daily_vol ** 2)
        growth = np.exp(drift + daily_vol * z_values)
        cum_growth = np.cumprod(growth, axis=1)
        mc_paths = curr * cum_growth

        monte_carlo_mean = np.mean(mc_paths, axis=0)
        mc_upper = np.percentile(mc_paths, 95, axis=0)
        mc_lower = np.percentile(mc_paths, 5, axis=0)

        kaydet_basarili_model(
            "Monte_Carlo",
            monte_carlo_mean,
        )
    except (ValueError, TypeError, FloatingPointError, MemoryError) as exc:
        kaydet_basarisiz_model("Monte_Carlo", exc)
        mc_upper = np.full(periyot_gun, np.nan)
        mc_lower = np.full(periyot_gun, np.nan)

    try:
        multi_factor_backtest_df = evaluate_multi_factor_ols_backtest(
            target_data=df,
            market_symbol=market_symbol or "",
            asset_name=str(market_symbol or "Seçilen Varlık"),
            asset_type=asset_type,
            test_window=5,
            max_windows=250,
        )

        if isinstance(backtest_df, pd.DataFrame):
            backtest_df = pd.concat(
                [backtest_df, multi_factor_backtest_df],
                ignore_index=True,
            )
        else:
            backtest_df = multi_factor_backtest_df

    except (
        ValueError,
        TypeError,
        FloatingPointError,
        RuntimeError,
        KeyError,
        ImportError,
    ) as exc:
        logger.warning("Multi_Factor_OLS backtesti çalıştırılamadı: %s", exc)
        backtest_messages.append(f"Multi_Factor_OLS: {exc}")

    backtest_df = _normalize_backtest_status_columns(backtest_df)

    if not rotalar:
        raise RuntimeError(
            "Tahmin modellerinin hiçbiri geçerli sonuç üretemedi."
        )

    # Sprint 3.40 - Horizon-Aware Consensus Engine
    # Tek genel ağırlık yerine, her vade için ayrı model ağırlığı üretilir.
    periyotlar = calendar_config.horizons

    (
        konsensus_rota,
        model_agirliklari,
        horizon_model_agirliklari,
        horizon_consensus_summary,
    ) = _build_horizon_aware_consensus_path(
        rotalar=rotalar,
        backtest_df=backtest_df,
        periyot_gun=periyot_gun,
        target_horizons=periyotlar,
    )

    if not backtest_df.empty and "Model" in backtest_df.columns:
        backtest_df = _add_consensus_explainability_columns(
            backtest_df=backtest_df,
            model_weights=model_agirliklari,
            active_models=rotalar.keys(),
            model_statuses=model_durumlari,
        )

    if not rotalar:
        raise ValueError(
            "Hiçbir model geçerli rota üretemedi. "
            "Sistem güvenli yedek rota üretmedi. "
            "Veri, feature veya model eğitim koşulları tanı panelinden incelenmelidir."
        )

    if "Monte_Carlo" not in rotalar:
        mc_upper = konsensus_rota.copy()
        mc_lower = konsensus_rota.copy()

    calibration_log_error = calculate_weighted_calibration_error(
        backtest_results=backtest_df,
        model_weights=model_agirliklari,
    )

    monte_carlo_is_active = (
        float(model_agirliklari.get("Monte_Carlo", 0.0)) > 0
        and "Monte_Carlo" in rotalar
    )

    (
        senaryo_alt_rota,
        senaryo_ust_rota,
        kalibrasyon_log_hata_90,
        guven_araligi_yontemi,
    ) = _build_calibrated_scenario_bands(
        consensus_path=konsensus_rota,
        current_price=curr,
        daily_volatility=daily_vol,
        horizon=periyot_gun,
        calibration_log_error=calibration_log_error,
        monte_carlo_lower=mc_lower,
        monte_carlo_upper=mc_upper,
        include_monte_carlo=monte_carlo_is_active,
    )

    risk_stats = calculate_risk_metrics(df["Close"])
    
    # DÜZELTİLMİŞ BETA HESAPLAMASI
    sp500_data = get_sp500_data(data.index[0], data.index[-1])
    beta = 1.0
    if not sp500_data.empty and len(sp500_data) > 10:
        df_beta = pd.concat([data['Close'], sp500_data], axis=1, join='inner')
        df_beta.columns = ['Stock', 'SP500']
        stock_returns = df_beta['Stock'].pct_change().dropna()
        sp_returns = df_beta['SP500'].pct_change().dropna()
        min_len = min(len(stock_returns), len(sp_returns))
        if min_len > 1:
            stock_returns = stock_returns.iloc[-min_len:].values.flatten()
            sp_returns = sp_returns.iloc[-min_len:].values.flatten()
            cov_matrix = np.cov(stock_returns, sp_returns)
            beta = float(cov_matrix[0, 1] / (cov_matrix[1, 1] + 1e-9))

    gelecek_tablo = []
    periyotlar = calendar_config.horizons
    for l, d in periyotlar:
        if d <= periyot_gun:
            alt_native = float(senaryo_alt_rota[d - 1])
            baz_native = float(konsensus_rota[d - 1])
            ust_native = float(senaryo_ust_rota[d - 1])

            vade_weights = horizon_model_agirliklari.get(str(l), {})
            lider_model, lider_agirlik, aktif_model_sayisi = _leader_from_weights(vade_weights)

            baz_getiri = (baz_native - curr) / curr
            alt_getiri = (alt_native - curr) / curr
            ust_getiri = (ust_native - curr) / curr

            gelecek_tablo.append(
                {
                    "Vade": l,
                    "Konsensüs Model Sayısı": int(aktif_model_sayisi),
                    "Lider Model": str(lider_model),
                    "Lider Ağırlık %": round(float(lider_agirlik) * 100.0, 2),
                    "Kötümser Senaryo": round(
                        alt_native * kur_val,
                        2,
                    ),
                    "Baz Senaryo": round(
                        baz_native * kur_val,
                        2,
                    ),
                    "İyimser Senaryo": round(
                        ust_native * kur_val,
                        2,
                    ),
                    # Mevcut arayüz uyumluluğu için baz senaryo alias'ı.
                    "Tahmin": round(
                        baz_native * kur_val,
                        2,
                    ),
                    "Kötümser Getiri %": round(
                        alt_getiri * 100.0,
                        2,
                    ),
                    "Nominal Getiri %": round(
                        baz_getiri * 100.0,
                        2,
                    ),
                    "İyimser Getiri %": round(
                        ust_getiri * 100.0,
                        2,
                    ),
                    "Kötümser Sermaye": round(
                        ana_para * (1.0 + alt_getiri),
                        2,
                    ),
                    "Sermaye Karşılığı": round(
                        ana_para * (1.0 + baz_getiri),
                        2,
                    ),
                    "İyimser Sermaye": round(
                        ana_para * (1.0 + ust_getiri),
                        2,
                    ),
                }
            )

    destek, direnc = destek_direnc_bul(df)
    return {
        "konsensus_rota": konsensus_rota * kur_val,
        "senaryo_alt": senaryo_alt_rota * kur_val,
        "senaryo_ust": senaryo_ust_rota * kur_val,
        "mc_upper": mc_upper * kur_val,
        "mc_lower": mc_lower * kur_val,
        "mc_raw_upper": mc_upper * kur_val,
        "mc_raw_lower": mc_lower * kur_val,
        "rotalar": {k: v * kur_val for k, v in rotalar.items()},
        "model_durumlari": model_durumlari,
        "model_agirliklari": model_agirliklari,
        "horizon_model_agirliklari": horizon_model_agirliklari,
        "horizon_consensus_summary": horizon_consensus_summary,
        "rota_turleri": rota_turleri,
        "projeksiyon_bildirimi": (
            "Regresyon modellerinin ara dönem çizgileri görsel senaryo "
            "rotasıdır; modelin doğrudan günlük tahmini değildir. "
            "Vade sonu hedefleri ve ARIMA/Monte Carlo yolları ayrı "
            "değerlendirilmelidir. Kötümser ve iyimser senaryo bantları "
            "backtest hataları, tarihsel volatilite ve uygun olduğunda "
            "Monte Carlo dağılımıyla kalibre edilir. "
            f"Takvim standardı: {calendar_config.calendar_name}."
        ),
        "varlik_turu": calendar_config.asset_type,
        "varlik_turu_etiketi": calendar_config.display_name,
        "market_symbol": str(market_symbol or ""),
        "vade_birimi": calendar_config.period_unit,
        "takvim_frekansi": calendar_config.date_frequency,
        "takvim_adi": calendar_config.calendar_name,
        "takvim_aciklamasi": calendar_config.calendar_note,
        "vade_standardlari": [
            {"etiket": etiket, "periyot": gun}
            for etiket, gun in calendar_config.horizons
        ],
        "guven_araligi_yontemi": guven_araligi_yontemi,
        "kalibrasyon_log_hata_90": kalibrasyon_log_hata_90,
        "backtest_df": backtest_df,
        "backtest_status": backtest_status,
        "stats": {
            **risk_stats,
            "Beta": beta,
        },
        "gelecek_df": pd.DataFrame(gelecek_tablo),
        "boga": float(senaryo_ust_rota[-1] * kur_val),
        "ayi": float(senaryo_alt_rota[-1] * kur_val),
        "destek": destek * kur_val,
        "direnc": direnc * kur_val
    }
