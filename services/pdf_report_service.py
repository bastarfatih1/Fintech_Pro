from __future__ import annotations

from io import BytesIO
from typing import Any, Mapping, Optional
from xml.sax.saxutils import escape as xml_escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _get(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _num(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        n = float(value)
        if pd.isna(n):
            return default
        return n
    except Exception:
        return default


def _safe_text(value: Any) -> str:
    text = str(value if value is not None else "")
    replacements = {
        "₺": "TL",
        "–": "-",
        "—": "-",
        "İ": "I",
        "ı": "i",
        "ğ": "g",
        "Ğ": "G",
        "ş": "s",
        "Ş": "S",
        "ç": "c",
        "Ç": "C",
        "ö": "o",
        "Ö": "O",
        "ü": "u",
        "Ü": "U",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _money(value: Any, symbol: str = "TL") -> str:
    n = _num(value)
    if n is None:
        return "Veri yok"
    text = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} {symbol}"


def _pct(value: Any) -> str:
    n = _num(value)
    if n is None:
        return "Veri yok"
    sign = "+" if n > 0 else "-" if n < 0 else ""
    return f"{sign}%{abs(n):.2f}".replace(".", ",")


def _styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle("TitleX", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"), spaceAfter=10)
    section = ParagraphStyle("SectionX", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor("#1e3a8a"), spaceBefore=9, spaceAfter=5)
    body = ParagraphStyle("BodyX", parent=base["BodyText"], fontName="Helvetica", fontSize=8.6, leading=11.3, textColor=colors.HexColor("#111827"))
    small = ParagraphStyle("SmallX", parent=base["BodyText"], fontName="Helvetica", fontSize=7.6, leading=9.5, textColor=colors.HexColor("#475569"))
    return title, section, body, small


def _p(value: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(xml_escape(_safe_text(value)), style)


def _rich(value: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_safe_text(value), style)


def _table(rows: list[list[Any]], widths: Optional[list[float]] = None) -> Table:
    _, _, body, _ = _styles()
    safe_rows = [[_p(cell, body) for cell in row] for row in rows]
    table = Table(safe_rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#eef2ff")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _future_table(payload: Mapping[str, Any]) -> pd.DataFrame:
    forecast_data = _get(payload, "forecast_data", {})
    if isinstance(forecast_data, pd.DataFrame):
        return forecast_data.copy()

    if isinstance(forecast_data, Mapping):
        for key in ["gelecek_tablo", "gelecek_df", "future_table", "forecast_table", "senaryo_tablosu", "scenario_table"]:
            value = forecast_data.get(key)
            if isinstance(value, pd.DataFrame) and not value.empty:
                return value.copy()

        for value in forecast_data.values():
            if isinstance(value, pd.DataFrame) and not value.empty:
                cols = set(map(str, value.columns))
                if "Vade" in cols or "Sermaye Karşılığı" in cols or "Baz Senaryo" in cols:
                    return value.copy()

    for key in ["future_table", "forecast_table", "gelecek_tablo"]:
        value = _get(payload, key)
        if isinstance(value, pd.DataFrame) and not value.empty:
            return value.copy()

    return pd.DataFrame()


def _pick_row(payload: Mapping[str, Any], label: str) -> dict[str, Any]:
    df = _future_table(payload)
    if df.empty:
        return {}

    if "Vade" in df.columns and label:
        target = str(label).strip().casefold()
        match = df[df["Vade"].astype(str).str.strip().str.casefold().eq(target)]
        if not match.empty:
            return match.iloc[0].to_dict()

    return df.iloc[-1].to_dict()


def _row(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _horizon_days(label: Any) -> int:
    text = str(label or "").strip().casefold()

    if "işlem" in text or "islem" in text or "1 gün" in text or "1 gun" in text:
        return 1
    if "hafta" in text:
        return 5
    if "1 ay" in text:
        return 21
    if "3 ay" in text:
        return 63
    if "6 ay" in text:
        return 126
    if "1 yıl" in text or "1 yil" in text:
        return 252
    if "3 yıl" in text or "3 yil" in text:
        return 756
    if "5 yıl" in text or "5 yil" in text:
        return 1260

    return 63


def _close_series_from_payload(payload: Mapping[str, Any]) -> pd.Series:
    for key in ["price_data", "data", "market_data", "history_data"]:
        value = _get(payload, key)

        if isinstance(value, pd.DataFrame) and not value.empty:
            for col in ["Close", "close", "Adj Close", "AdjClose", "Kapanış", "Kapanis"]:
                if col in value.columns:
                    series = pd.to_numeric(value[col], errors="coerce").dropna()

                    if not series.empty:
                        return series

    return pd.Series(dtype="float64")


def _history_from_payload(
    payload: Mapping[str, Any],
    forecast_label: Any,
    current_price: Any,
) -> dict[str, Any]:
    close = _close_series_from_payload(payload)

    if close.empty:
        return {}

    days = _horizon_days(forecast_label)

    if len(close) <= days:
        return {}

    current = _num(current_price)

    if current is None:
        current = _num(close.iloc[-1])

    past = _num(close.iloc[-(days + 1)])

    if current is None or past is None or past <= 0:
        return {}

    historical_return = ((current / past) - 1.0) * 100.0

    return {
        "current_price": current,
        "past_price": past,
        "historical_return_percent": historical_return,
    }


def _pdf_news_comment(
    raw_text: Any,
    asset_name: Any,
    forecast_label: Any,
    base_return: Any,
) -> str:
    raw = _safe_text(raw_text).strip()
    raw_lower = raw.casefold()
    ret = _num(base_return)

    if not raw or "various news" in raw_lower or "news articles" in raw_lower:
        base = (
            f"{asset_name} için haber akışı genel piyasa algısı, şirket/varlık görünümü "
            f"ve seçili {forecast_label} vade üzerindeki olası etkiler açısından okunmalıdır."
        )
    else:
        base = raw

    if ret is not None and ret > 3:
        direction = (
            " Baz senaryonun pozitif getiri üretmesi, haber akışında sert negatif bir baskı "
            "oluşmadığı sürece yukarı yönlü beklentiyi destekler."
        )
    elif ret is not None and ret < -3:
        direction = (
            " Baz senaryonun negatif bölgeye işaret etmesi, haber akışı veya piyasa koşullarında "
            "baskı ihtimalinin dikkatle izlenmesi gerektiğini gösterir."
        )
    else:
        direction = (
            " Baz senaryonun sınırlı bölgede kalması, haber etkisinin tek başına güçlü bir yön "
            "oluşturmadığını ve model sonucunun temkinli okunması gerektiğini gösterir."
        )

    return base + direction


def _pdf_model_comment(
    raw_text: Any,
    forecast_label: Any,
    base_return: Any,
    bad_return: Any,
    good_return: Any,
) -> str:
    raw = _safe_text(raw_text).strip()
    ret = _num(base_return)

    if ret is not None and ret > 3:
        direction = "pozitif"
    elif ret is not None and ret < -3:
        direction = "negatif"
    else:
        direction = "dengeli"

    return (
        f"Model konsensüsü seçili {forecast_label} vade için {direction} bir baz senaryo üretmektedir. "
        f"Baz getiri {_pct(base_return)}, kötümser getiri {_pct(bad_return)}, iyimser getiri {_pct(good_return)} "
        "olarak okunmaktadır. Senaryo aralığı genişledikçe belirsizlik artar; bu nedenle baz sonuç ana beklenti, "
        "kötümser sonuç risk sınırı, iyimser sonuç ise olumlu piyasa koşullarındaki potansiyel alan olarak değerlendirilmelidir. "
        f"{raw if raw else ''}"
    ).strip()


def _pdf_risk_comment(
    raw_text: Any,
    bad_return: Any,
    bad_capital: Any,
    good_capital: Any,
    currency_symbol: str,
) -> str:
    raw = _safe_text(raw_text).strip()

    base = (
        f"Kötümser senaryoda getiri {_pct(bad_return)} seviyesine gerileyebilir ve sermaye "
        f"{_money(bad_capital, currency_symbol)} düzeyine inebilir. İyimser senaryoda ise sermaye "
        f"{_money(good_capital, currency_symbol)} seviyesine çıkabilir. Bu fark, risk aralığının ve oynaklığın "
        "dikkatle izlenmesi gerektiğini gösterir."
    )

    if raw:
        return base + " " + raw

    return base


def build_pdf_report(payload: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> bytes:
    payload = dict(payload or {})
    payload.update(kwargs)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.25 * cm,
        bottomMargin=1.25 * cm,
        title="Fintech Alpha Pro Analiz Raporu",
    )

    title_style, section_style, body_style, small_style = _styles()

    asset_name = _get(payload, "asset_name", "Secili varlik")
    market_symbol = _get(payload, "market_symbol", _get(payload, "symbol", "-"))
    forecast_label = _get(payload, "forecast_label", _get(payload, "selected_horizon", "Secili vade"))
    currency_symbol = _safe_text(_get(payload, "currency_symbol", "TL"))

    investment_amount = _get(payload, "investment_amount", _get(payload, "invested_capital"))
    current_price = _get(payload, "current_price")
    past_price = _get(payload, "past_price")
    historical_return = _get(payload, "historical_return_percent")

    history_values = _history_from_payload(payload, forecast_label, current_price)

    if current_price is None and history_values.get("current_price") is not None:
        current_price = history_values.get("current_price")

    if past_price is None and history_values.get("past_price") is not None:
        past_price = history_values.get("past_price")

    if historical_return is None and history_values.get("historical_return_percent") is not None:
        historical_return = history_values.get("historical_return_percent")

    selected = _pick_row(payload, forecast_label)

    base_return = _num(_row(selected, "Nominal Getiri %", "Baz Getiri %", "Getiri %", "future_base_return_percent"))
    bad_return = _num(_row(selected, "Kötümser Getiri %"))
    good_return = _num(_row(selected, "İyimser Getiri %"))

    base_capital = _num(_row(selected, "Sermaye Karşılığı", "Baz Sermaye"))
    bad_capital = _num(_row(selected, "Kötümser Sermaye"))
    good_capital = _num(_row(selected, "İyimser Sermaye"))

    base_price = _num(_row(selected, "Baz Senaryo", "Tahmin"))
    bad_price = _num(_row(selected, "Kötümser Senaryo"))
    good_price = _num(_row(selected, "İyimser Senaryo"))

    invested = _num(investment_amount)

    if invested is not None:
        if base_capital is None and base_return is not None:
            base_capital = invested * (1 + base_return / 100.0)
        if bad_capital is None and bad_return is not None:
            bad_capital = invested * (1 + bad_return / 100.0)
        if good_capital is None and good_return is not None:
            good_capital = invested * (1 + good_return / 100.0)

    base_gain = base_capital - invested if base_capital is not None and invested is not None else None
    bad_gain = bad_capital - invested if bad_capital is not None and invested is not None else None
    good_gain = good_capital - invested if good_capital is not None and invested is not None else None

    story = []
    story.append(_p("Fintech Alpha Pro - Analiz Raporu", title_style))
    story.append(_p(f"{asset_name} | {market_symbol} | Vade: {forecast_label}", body_style))
    story.append(Spacer(1, 7))

    story.append(_p("Ozet Bilgiler", section_style))
    story.append(
        _table(
            [
                ["Alan", "Deger"],
                ["Varlik", asset_name],
                ["Sembol", market_symbol],
                ["Secili vade", forecast_label],
                ["Yatirim tutari", _money(investment_amount, currency_symbol)],
                ["Guncel fiyat", _money(current_price, currency_symbol)],
                ["Gecmis fiyat", _money(past_price, currency_symbol)],
                ["Gecmis getiri", _pct(historical_return)],
            ],
            widths=[5.0 * cm, 10.7 * cm],
        )
    )

    story.append(Spacer(1, 8))
    story.append(_p("Gelecek Senaryo Ozeti", section_style))
    story.append(
        _table(
            [
                ["Senaryo", "Hedef Fiyat", "Sermaye", "Getiri", "Fark"],
                ["Kotumser", _money(bad_price, currency_symbol), _money(bad_capital, currency_symbol), _pct(bad_return), _money(bad_gain, currency_symbol)],
                ["Baz konsensus", _money(base_price, currency_symbol), _money(base_capital, currency_symbol), _pct(base_return), _money(base_gain, currency_symbol)],
                ["Iyimser", _money(good_price, currency_symbol), _money(good_capital, currency_symbol), _pct(good_return), _money(good_gain, currency_symbol)],
            ],
            widths=[3.2 * cm, 3.2 * cm, 3.4 * cm, 2.7 * cm, 3.2 * cm],
        )
    )

    ai_bundle = _get(payload, "ai_bundle", {})
    if isinstance(ai_bundle, Mapping):
        technical_summary = _safe_text(_get(ai_bundle, "technical_summary", ""))
        market_synthesis = _safe_text(_get(ai_bundle, "market_synthesis", ""))
        risk_note = _safe_text(_get(ai_bundle, "risk_note", ""))
        news_effect_summary = _safe_text(_get(ai_bundle, "news_effect_summary", ""))

        market_synthesis = _pdf_news_comment(
            news_effect_summary or market_synthesis,
            asset_name,
            forecast_label,
            base_return,
        )
        news_effect_summary = ""

        technical_summary = _pdf_model_comment(
            technical_summary,
            forecast_label,
            base_return,
            bad_return,
            good_return,
        )

        risk_note = _pdf_risk_comment(
            risk_note,
            bad_return,
            bad_capital,
            good_capital,
            currency_symbol,
        )

        story.append(Spacer(1, 8))
        story.append(_p("AI Degerlendirme Ozeti", section_style))

        scenario_text = (
            f"Secili {forecast_label} vadede { _money(investment_amount, currency_symbol) } yatirim icin "
            f"baz senaryo { _money(base_capital, currency_symbol) } sermaye ve { _pct(base_return) } getiri uretmektedir. "
            f"Kotumser senaryo { _money(bad_capital, currency_symbol) }, iyimser senaryo { _money(good_capital, currency_symbol) } seviyesindedir."
        )
        story.append(_p(scenario_text, body_style))
        story.append(Spacer(1, 4))

        if news_effect_summary or market_synthesis:
            story.append(_rich(f"<b>Haber yorumu:</b> {xml_escape(news_effect_summary or market_synthesis)}", body_style))
            story.append(Spacer(1, 4))

        if technical_summary:
            story.append(_rich(f"<b>Model / teknik yorum:</b> {xml_escape(technical_summary)}", body_style))
            story.append(Spacer(1, 4))

        if risk_note:
            story.append(_rich(f"<b>Risk notu:</b> {xml_escape(risk_note)}", body_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))
    story.append(
        _p(
            "Bu rapor bilgilendirme ve karar destek amaclidir. Yatirim tavsiyesi degildir. Gecmis performans gelecek sonuclari garanti etmez.",
            small_style,
        )
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


generate_pdf_report = build_pdf_report
create_pdf_report = build_pdf_report
render_pdf_report = build_pdf_report
build_analysis_pdf_report = build_pdf_report
generate_analysis_pdf_report = build_pdf_report
create_analysis_pdf_report = build_pdf_report
build_analysis_report_pdf = build_pdf_report
generate_analysis_report_pdf = build_pdf_report
create_analysis_report_pdf = build_pdf_report
build_pdf_report_bytes = build_pdf_report
generate_pdf_report_bytes = build_pdf_report
create_pdf_report_bytes = build_pdf_report
