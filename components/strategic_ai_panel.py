from __future__ import annotations

import math
from html import escape as html_escape
from typing import Any, Mapping, Optional

import pandas as pd
import streamlit.components.v1 as components


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default

        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return number

    except Exception:
        return default


def _format_money(value: Any, symbol: str = "₺") -> str:
    number = _safe_float(value)

    if number is None:
        return "veri yok"

    text = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} {symbol}"


def _format_percent(value: Any) -> str:
    number = _safe_float(value)

    if number is None:
        return "veri yok"

    sign = "+" if number > 0 else "-" if number < 0 else ""
    arrow = "▲" if number > 0 else "▼" if number < 0 else "■"
    text = f"{abs(number):.2f}".replace(".", ",")
    return f"{arrow} {sign}%{text}"


def _plain_percent(value: Any) -> str:
    number = _safe_float(value)

    if number is None:
        return "veri yok"

    sign = "+" if number > 0 else "-" if number < 0 else ""
    text = f"{abs(number):.2f}".replace(".", ",")
    return f"{sign}%{text}"


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()

    replacements = {
        "OLLAMA": "",
        "Ollama": "",
        "ollama": "",
        "OPENAI": "",
        "OpenAI": "",
        "GPT": "",
        "POZİTİF": "olumlu eğilim",
        "NEGATİF": "risk baskısı",
        "NÖTR": "dengeli görünüm",
        "AL": "yukarı yönlü sinyal",
        "SAT": "aşağı yönlü risk",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split()).strip()


def _esc(value: Any) -> str:
    return html_escape(str(value if value is not None else ""), quote=True)


def _future_table(forecast_data: Any) -> pd.DataFrame:
    if isinstance(forecast_data, pd.DataFrame):
        return forecast_data.copy()

    if not isinstance(forecast_data, Mapping):
        return pd.DataFrame()

    keys = [
        "gelecek_tablo",
        "gelecek_df",
        "future_table",
        "forecast_table",
        "senaryo_tablosu",
        "scenario_table",
    ]

    for key in keys:
        value = forecast_data.get(key)

        if isinstance(value, pd.DataFrame) and not value.empty:
            return value.copy()

    for value in forecast_data.values():
        if isinstance(value, pd.DataFrame) and not value.empty:
            columns = set(map(str, value.columns))

            if (
                "Vade" in columns
                or "Sermaye Karşılığı" in columns
                or "Baz Senaryo" in columns
            ):
                return value.copy()

    return pd.DataFrame()


def _pick_selected_row(forecast_data: Any, selected_horizon_label: str) -> dict[str, Any]:
    df = _future_table(forecast_data)

    if df.empty:
        return {}

    if "Vade" in df.columns and selected_horizon_label:
        target = str(selected_horizon_label).strip().casefold()

        match = df[
            df["Vade"]
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq(target)
        ]

        if not match.empty:
            return match.iloc[0].to_dict()

    return df.iloc[-1].to_dict()


def _get_value(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row.get(name)

    return None


def _model_summary(forecast_data: Any) -> str:
    if not isinstance(forecast_data, Mapping):
        return (
            "Model konsensüsü üretildi; ancak doğrulama ve ağırlık detayları sınırlı olduğu için "
            "sonuç temkinli okunmalıdır."
        )

    active_model_count = 0

    weights = forecast_data.get("model_agirliklari")

    if weights is None:
        weights = forecast_data.get("model_weights")

    if weights is None:
        weights = {}

    if isinstance(weights, Mapping):
        for value in weights.values():
            if (_safe_float(value, 0.0) or 0.0) > 0:
                active_model_count += 1

    backtest_df = forecast_data.get("backtest_df")

    if backtest_df is None:
        backtest_df = forecast_data.get("test_df")

    test_sentence = ""

    if isinstance(backtest_df, pd.DataFrame) and not backtest_df.empty:
        total = len(backtest_df)
        passed = None

        if "Başarılı mı?" in backtest_df.columns:
            passed = int(backtest_df["Başarılı mı?"].astype(bool).sum())

        elif "Durum" in backtest_df.columns:
            passed = int(
                backtest_df["Durum"]
                .astype(str)
                .str.contains("başar|success|geçti", case=False, regex=True)
                .sum()
            )

        if passed is not None:
            test_sentence = (
                f" Test ve backtest tarafında {passed}/{total} kontrol olumlu görünmektedir. "
                "Bu oran modelin geçmiş veride tamamen kusursuz olmadığını, ancak seçili vadede "
                "izlenebilir bir sinyal ürettiğini gösterir."
            )

    if active_model_count:
        return (
            f"Konsensüs hesaplamasına {active_model_count} aktif model katkı vermektedir."
            f"{test_sentence} Modellerin ortak yönü baz senaryo etrafında toplanıyorsa beklenti daha tutarlı okunur. "
            "Kötümser ve iyimser aralık birbirinden uzaklaştıkça belirsizlik artar. "
            "Bu nedenle model sonucu kesin fiyat tahmini değil, senaryo bazlı karar destek çıktısıdır."
        )

    return (
        "Model tarafında senaryo üretimi yapılmış olsa da aktif model ağırlıkları sınırlı okunmaktadır. "
        f"{test_sentence} Bu nedenle sonuç, haber akışı, fiyat oynaklığı ve risk aralığıyla birlikte değerlendirilmelidir."
    )


def _tone_label(base_return: Optional[float]) -> str:
    if base_return is None:
        return "Dengeli görünüm"

    if base_return > 3:
        return "Olumlu eğilim"

    if base_return < -3:
        return "Risk baskısı"

    return "Dengeli görünüm"


def _tone_class(value: Optional[float]) -> str:
    if value is None:
        return "neutral"

    if value > 0:
        return "positive"

    if value < 0:
        return "negative"

    return "neutral"


def _direction_text(base_return: Optional[float]) -> str:
    if base_return is None:
        return "belirgin yön verisi üretmemektedir"

    if base_return > 3:
        return "yukarı yönlü beklentiyi desteklemektedir"

    if base_return < -3:
        return "aşağı yönlü risk baskısına işaret etmektedir"

    return "dengeli ve sınırlı yön beklentisi üretmektedir"


def _paragraphs(text: str) -> str:
    text = _clean_text(text)

    if not text:
        return "<p>Veri sınırlı olduğu için bu bölüm temkinli okunmalıdır.</p>"

    chunks = [chunk.strip() for chunk in text.split(". ") if chunk.strip()]

    if len(chunks) <= 1:
        return f"<p>{_esc(text)}</p>"

    html = ""

    for chunk in chunks:
        sentence = chunk if chunk.endswith(".") else chunk + "."
        html += f"<p>{_esc(sentence)}</p>"

    return html


def _details(title: str, body_html: str, *, tone: str = "blue") -> str:
    return f"""
    <details class="ai-detail {tone}">
      <summary>
        <span>{_esc(title)}</span>
        <b>Detayı aç</b>
      </summary>
      <div class="detail-body">
        {body_html}
      </div>
    </details>
    """


def render_strategic_ai_panel(
    *,
    ai_bundle: Optional[Mapping[str, Any]] = None,
    forecast_data: Optional[Mapping[str, Any]] = None,
    investment_amount: Any = None,
    current_price: Any = None,
    currency_rate: Any = 1.0,
    currency_symbol: str = "₺",
    asset_name: str = "Seçili varlık",
    selected_horizon_label: str = "Seçili vade",
) -> None:
    ai_bundle = dict(ai_bundle) if isinstance(ai_bundle, Mapping) else {}
    forecast_data = dict(forecast_data) if isinstance(forecast_data, Mapping) else {}

    selected_row = _pick_selected_row(forecast_data, selected_horizon_label)

    invested = _safe_float(investment_amount)
    current_native = _safe_float(current_price)
    rate = _safe_float(currency_rate, 1.0) or 1.0
    current_display = current_native * rate if current_native is not None else None

    base_price = _safe_float(_get_value(selected_row, "Baz Senaryo", "Tahmin", "Base Scenario"))
    bad_price = _safe_float(_get_value(selected_row, "Kötümser Senaryo", "Pessimistic Scenario"))
    good_price = _safe_float(_get_value(selected_row, "İyimser Senaryo", "Optimistic Scenario"))

    base_return = _safe_float(_get_value(selected_row, "Nominal Getiri %", "Baz Getiri %", "Getiri %"))
    bad_return = _safe_float(_get_value(selected_row, "Kötümser Getiri %"))
    good_return = _safe_float(_get_value(selected_row, "İyimser Getiri %"))

    base_capital = _safe_float(_get_value(selected_row, "Sermaye Karşılığı", "Baz Sermaye"))
    bad_capital = _safe_float(_get_value(selected_row, "Kötümser Sermaye"))
    good_capital = _safe_float(_get_value(selected_row, "İyimser Sermaye"))

    if invested is not None:
        if base_capital is None and base_return is not None:
            base_capital = invested * (1 + base_return / 100.0)

        if bad_capital is None and bad_return is not None:
            bad_capital = invested * (1 + bad_return / 100.0)

        if good_capital is None and good_return is not None:
            good_capital = invested * (1 + good_return / 100.0)

    if base_return is None and current_display and base_price:
        base_return = ((base_price / current_display) - 1.0) * 100.0

    if bad_return is None and current_display and bad_price:
        bad_return = ((bad_price / current_display) - 1.0) * 100.0

    if good_return is None and current_display and good_price:
        good_return = ((good_price / current_display) - 1.0) * 100.0

    base_gain = base_capital - invested if base_capital is not None and invested is not None else None
    bad_gain = bad_capital - invested if bad_capital is not None and invested is not None else None
    good_gain = good_capital - invested if good_capital is not None and invested is not None else None

    technical_summary = _clean_text(ai_bundle.get("technical_summary", ""))
    market_synthesis = _clean_text(ai_bundle.get("market_synthesis", ""))
    risk_note = _clean_text(ai_bundle.get("risk_note", ""))
    news_effect_summary = _clean_text(ai_bundle.get("news_effect_summary", ""))

    model_text = _model_summary(forecast_data)
    tone_label = _tone_label(base_return)
    tone_class = _tone_class(base_return)
    direction_text = _direction_text(base_return)

    intro_text = (
        market_synthesis
        or technical_summary
        or (
            "Haber akışı ve teknik görünüm birlikte değerlendirildiğinde sonuçlar "
            "model konsensüsü ve seçili vade üzerinden yorumlanmalıdır."
        )
    )

    news_detail = (
        f"{news_effect_summary or intro_text} "
        "Haber tarafı yorumlanırken yalnızca tek bir başlık değil, haberlerin fiyat üzerindeki olası yönü, "
        "haber tonunun güçlü mü zayıf mı olduğu, model senaryosunu destekleyip desteklemediği ve olası risk etkisi birlikte değerlendirilir. "
        "Haber akışı güçlü biçimde olumluysa baz senaryo desteklenir; haber dili belirsiz ya da zayıfsa model sonucu daha temkinli okunmalıdır."
    )

    general_html = f"""
    <p><strong>{_esc(asset_name)}</strong> için genel görünüm <strong>{_esc(tone_label)}</strong> olarak okunmaktadır.
    Seçilen <strong>{_esc(selected_horizon_label)}</strong> vadede baz senaryo
    <strong>{_esc(_format_percent(base_return))}</strong> getiri üretmektedir.</p>

    <p>Bu sonuç, modelin mevcut veri seti üzerinden <strong>{_esc(direction_text)}</strong> anlamına gelir.
    Yatırım tutarı <strong>{_esc(_format_money(invested, currency_symbol))}</strong> olduğunda baz senaryoda
    sermaye yaklaşık <strong>{_esc(_format_money(base_capital, currency_symbol))}</strong> seviyesine ulaşır.
    Bu da yaklaşık <strong>{_esc(_format_money(base_gain, currency_symbol))}</strong> nominal fark anlamına gelir.</p>

    <p>Baz senaryo ana beklentiyi, kötümser senaryo aşağı yönlü risk sınırını,
    iyimser senaryo ise haber ve piyasa koşullarının desteklemesi halinde oluşabilecek genişleme alanını gösterir.</p>
    """

    scenario_html = f"""
    <div class="scenario-grid">
      <div class="scenario-card negative">
        <small>Kötümser Senaryo</small>
        <strong>{_esc(_format_money(bad_capital, currency_symbol))}</strong>
        <span>{_esc(_format_percent(bad_return))} · {_esc(_format_money(bad_gain, currency_symbol))}</span>
      </div>
      <div class="scenario-card base">
        <small>Baz Senaryo</small>
        <strong>{_esc(_format_money(base_capital, currency_symbol))}</strong>
        <span>{_esc(_format_percent(base_return))} · {_esc(_format_money(base_gain, currency_symbol))}</span>
      </div>
      <div class="scenario-card positive">
        <small>İyimser Senaryo</small>
        <strong>{_esc(_format_money(good_capital, currency_symbol))}</strong>
        <span>{_esc(_format_percent(good_return))} · {_esc(_format_money(good_gain, currency_symbol))}</span>
      </div>
    </div>

    <p>Fiyat hedefleri tarafında kötümser hedef <strong>{_esc(_format_money(bad_price, currency_symbol))}</strong>,
    baz hedef <strong>{_esc(_format_money(base_price, currency_symbol))}</strong>, iyimser hedef ise
    <strong>{_esc(_format_money(good_price, currency_symbol))}</strong> olarak okunmaktadır.</p>

    <p>Yatırım tutarı açısından bakıldığında baz senaryo sermayeyi
    <strong>{_esc(_format_money(base_capital, currency_symbol))}</strong> seviyesine taşırken,
    kötümser senaryo sermayeyi <strong>{_esc(_format_money(bad_capital, currency_symbol))}</strong>
    seviyesine çekebilir. İyimser senaryo ise sermayeyi
    <strong>{_esc(_format_money(good_capital, currency_symbol))}</strong> seviyesine çıkarabilir.</p>
    """

    up_html = f"""
    <ul>
      <li>Baz senaryonun seçili vadede <strong>{_esc(_format_percent(base_return))}</strong> getiri üretmesi.</li>
      <li>Haber akışında sert negatif baskının öne çıkmaması.</li>
      <li>Model konsensüsünün seçili vade için ölçülebilir senaryo üretmesi.</li>
      <li>İyimser senaryoda sermayenin <strong>{_esc(_format_money(good_capital, currency_symbol))}</strong> seviyesine çıkabilmesi.</li>
    </ul>
    <p>Artış ihtimali özellikle haber akışının fiyatı desteklemesi, model dağılımının baz senaryo etrafında toplanması ve geçmiş fiyat davranışının yukarı yönlü momentumu bozmadığı durumlarda güçlenir.</p>
    """

    down_html = f"""
    <ul>
      <li>Kötümser senaryoda getiri <strong>{_esc(_format_percent(bad_return))}</strong> seviyesine gerileyebilir.</li>
      <li>Senaryolar arası fark yüksekse oynaklık ve belirsizlik riski artar.</li>
      <li>Dış haber akışı, likidite, makro veri veya piyasa koşulları modeli aşağı yönlü bozabilir.</li>
      <li>Geçmiş performans gelecekte aynı sonucun oluşacağını garanti etmez.</li>
    </ul>
    {_paragraphs(risk_note or "Bu nedenle kötümser, baz ve iyimser sonuçlar birlikte okunmalıdır.")}
    """

    result_html = f"""
    <p>Sonuç olarak <strong>{_esc(asset_name)}</strong> için seçilen
    <strong>{_esc(selected_horizon_label)}</strong> vadede baz senaryo
    <strong>{_esc(_format_percent(base_return))}</strong> performans üretmektedir.</p>

    <p><strong>{_esc(_format_money(invested, currency_symbol))}</strong> yatırım tutarı baz alındığında tahmini sermaye
    <strong>{_esc(_format_money(base_capital, currency_symbol))}</strong> seviyesine ulaşır.
    Bu sonuç tek başına karar değil, haber, model, test ve risk aralığıyla birlikte okunacak bir karar destek çıktısıdır.</p>
    """

    details_html = ""
    details_html += _details("Genel stratejik yorum", general_html, tone="blue")
    details_html += _details("Haberlerin genel yorumu", _paragraphs(news_detail), tone="cyan")
    details_html += _details("Model ve konsensüs yorumu", _paragraphs(model_text), tone="indigo")
    details_html += _details("Yatırım tutarına göre senaryo sonucu", scenario_html, tone="green")
    details_html += _details("Neden artabilir?", up_html, tone="positive")
    details_html += _details("Neden azalabilir?", down_html, tone="negative")
    details_html += _details("Sonuç ve karar destek özeti", result_html, tone="gold")

    css = """
    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      padding: 0;
      background: transparent;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
      color: #f8fafc;
    }

    .ai-shell {
      width: 100%;
      border-radius: 24px;
      padding: 18px;
      background:
        radial-gradient(circle at 0% 0%, rgba(56,189,248,0.20), transparent 34%),
        radial-gradient(circle at 100% 0%, rgba(34,197,94,0.13), transparent 34%),
        linear-gradient(180deg, rgba(15,23,42,0.98), rgba(2,6,23,0.98));
      border: 1px solid rgba(56,189,248,0.34);
      box-shadow: 0 22px 65px rgba(0,0,0,0.38);
      overflow: hidden;
    }

    .ai-header {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 14px;
    }

    .kicker {
      color: #93c5fd;
      font-size: 11px;
      font-weight: 950;
      letter-spacing: 0.10em;
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .title {
      color: #ffffff;
      font-size: 22px;
      font-weight: 950;
      letter-spacing: -0.04em;
      line-height: 1.12;
      margin-bottom: 6px;
    }

    .subtitle {
      color: #dbeafe;
      font-size: 12.5px;
      font-weight: 700;
      line-height: 1.45;
      max-width: 900px;
    }

    .status-pill {
      flex: 0 0 auto;
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 11px;
      font-weight: 950;
      border: 1px solid rgba(255,255,255,0.12);
      background: rgba(15,23,42,0.72);
    }

    .positive { color: #86efac; }
    .negative { color: #fca5a5; }
    .neutral { color: #fde68a; }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }

    .metric {
      min-height: 88px;
      border-radius: 16px;
      padding: 12px;
      background: linear-gradient(180deg, rgba(30,41,59,0.90), rgba(15,23,42,0.98));
      border: 1px solid rgba(148,163,184,0.20);
      overflow: hidden;
    }

    .metric-label {
      color: #bfdbfe;
      font-size: 10px;
      font-weight: 950;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 7px;
    }

    .metric-value {
      color: #ffffff;
      font-size: 18px;
      font-weight: 950;
      line-height: 1.15;
      letter-spacing: -0.03em;
      word-break: break-word;
    }

    .metric-sub {
      color: #cbd5e1;
      font-size: 11px;
      font-weight: 700;
      line-height: 1.35;
      margin-top: 7px;
    }

    .detail-wrap {
      border-radius: 20px;
      padding: 13px;
      background: linear-gradient(180deg, rgba(15,23,42,0.72), rgba(2,6,23,0.82));
      border: 1px solid rgba(148,163,184,0.18);
    }

    .detail-title {
      font-size: 17px;
      font-weight: 950;
      color: #ffffff;
      letter-spacing: -0.03em;
      margin-bottom: 4px;
    }

    .detail-subtitle {
      color: #cbd5e1;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 10px;
    }

    details.ai-detail {
      border-radius: 15px;
      border: 1px solid rgba(56,189,248,0.20);
      background: rgba(15,23,42,0.72);
      overflow: hidden;
      margin-bottom: 9px;
    }

    details.ai-detail[open] {
      border-color: rgba(56,189,248,0.42);
      box-shadow: 0 12px 34px rgba(0,0,0,0.20);
    }

    details.ai-detail.blue[open] { background: linear-gradient(180deg, rgba(37,99,235,0.18), rgba(15,23,42,0.82)); }
    details.ai-detail.green[open], details.ai-detail.positive[open] { background: linear-gradient(180deg, rgba(20,184,166,0.17), rgba(15,23,42,0.82)); }
    details.ai-detail.negative[open] { background: linear-gradient(180deg, rgba(239,68,68,0.14), rgba(15,23,42,0.82)); }
    details.ai-detail.gold[open] { background: linear-gradient(180deg, rgba(234,179,8,0.13), rgba(15,23,42,0.82)); }

    summary {
      list-style: none;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      color: #ffffff;
      font-size: 14px;
      font-weight: 950;
    }

    summary::-webkit-details-marker { display: none; }

    summary b {
      flex: 0 0 auto;
      font-size: 10px;
      color: #93c5fd;
      font-weight: 950;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 5px 8px;
      border-radius: 999px;
      background: rgba(56,189,248,0.10);
      border: 1px solid rgba(56,189,248,0.20);
    }

    .detail-body {
      padding: 0 14px 14px 14px;
      color: #e2e8f0;
      font-size: 13.2px;
      line-height: 1.58;
      font-weight: 650;
    }

    .detail-body p { margin: 0 0 9px 0; }
    .detail-body strong { color: #ffffff; font-weight: 950; }

    ul { margin: 0; padding-left: 19px; }
    li { margin-bottom: 7px; }

    .scenario-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }

    .scenario-card {
      border-radius: 14px;
      padding: 12px;
      border: 1px solid rgba(255,255,255,0.10);
      background: rgba(15,23,42,0.72);
    }

    .scenario-card small {
      display: block;
      color: #cbd5e1;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 950;
      margin-bottom: 7px;
    }

    .scenario-card strong {
      display: block;
      font-size: 17px;
      line-height: 1.15;
      margin-bottom: 7px;
    }

    .scenario-card span {
      display: block;
      color: #dbeafe;
      font-size: 11.5px;
      font-weight: 800;
    }

    .scenario-card.negative { background: rgba(239,68,68,0.11); border-color: rgba(239,68,68,0.28); }
    .scenario-card.base { background: rgba(56,189,248,0.11); border-color: rgba(56,189,248,0.28); }
    .scenario-card.positive { background: rgba(34,197,94,0.11); border-color: rgba(34,197,94,0.28); }

    .footer-note {
      margin-top: 10px;
      color: #94a3b8;
      font-size: 11.5px;
      line-height: 1.45;
      font-weight: 700;
    }

    @media (max-width: 1180px) {
      .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .scenario-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
    }
    """

    html = f"""
    <!doctype html>
    <html lang="tr">
    <head>
      <meta charset="utf-8" />
      <style>{css}</style>
    </head>
    <body>
      <section class="ai-shell">
        <div class="ai-header">
          <div>
            <div class="kicker">Yapay Zekâ Stratejik Yorum</div>
            <div class="title">{_esc(asset_name)} · Premium Analiz Merkezi</div>
            <div class="subtitle">
              Seçili vade, yatırım tutarı, haber etkisi, model konsensüsü ve senaryo sonuçları tek merkezde özetlenir.
            </div>
          </div>
          <div class="status-pill {tone_class}">{_esc(tone_label)}</div>
        </div>

        <div class="metric-grid">
          <div class="metric">
            <div class="metric-label">Genel Görünüm</div>
            <div class="metric-value {tone_class}">{_esc(tone_label)}</div>
            <div class="metric-sub">Model yönü: {_esc(_plain_percent(base_return))}</div>
          </div>

          <div class="metric">
            <div class="metric-label">Seçili Vade</div>
            <div class="metric-value">{_esc(selected_horizon_label)}</div>
            <div class="metric-sub">Vade bazlı yorum</div>
          </div>

          <div class="metric">
            <div class="metric-label">Baz Hedef</div>
            <div class="metric-value">{_esc(_format_money(base_price, currency_symbol))}</div>
            <div class="metric-sub">Güncel: {_esc(_format_money(current_display, currency_symbol))}</div>
          </div>

          <div class="metric">
            <div class="metric-label">Beklenen Getiri</div>
            <div class="metric-value {tone_class}">{_esc(_format_percent(base_return))}</div>
            <div class="metric-sub">Kötümser {_esc(_plain_percent(bad_return))} · İyimser {_esc(_plain_percent(good_return))}</div>
          </div>

          <div class="metric">
            <div class="metric-label">Tahmini Sermaye</div>
            <div class="metric-value">{_esc(_format_money(base_capital, currency_symbol))}</div>
            <div class="metric-sub">Baz fark: {_esc(_format_money(base_gain, currency_symbol))}</div>
          </div>
        </div>

        <div class="detail-wrap">
          <div class="detail-title">Detaylı Yapay Zekâ Yorumu</div>
          <div class="detail-subtitle">Başlıklar tek analiz kutusu içinde açılır/kapanır premium kartlar halinde düzenlenmiştir.</div>
          {details_html}
        </div>

        <div class="footer-note">
          Bu bölüm model çıktıları, haber bağlamı ve senaryo verilerini karar destek amacıyla yorumlar. Yatırım tavsiyesi değildir.
        </div>
      </section>
    </body>
    </html>
    """

    components.html(html, height=720, scrolling=True)
