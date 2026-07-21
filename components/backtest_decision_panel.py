import pandas as pd
import streamlit as st

from components.premium_ui import render_premium_table, render_plain_guide


def _clean_cell(value):
    text = str(value)

    if text.lower() in {"none", "nan", "nat", ""}:
        return "—"

    return value


def _num(value):
    try:
        return float(value)
    except Exception:
        return None


def _build_decision_table(backtest_df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(backtest_df, pd.DataFrame) or backtest_df.empty:
        return pd.DataFrame()

    df = backtest_df.copy()

    output = pd.DataFrame()

    def pick(source_col, target_col):
        if source_col in df.columns:
            output[target_col] = df[source_col]

    pick("Model", "Model")
    pick("Teknik Durum", "Teknik")
    pick("Referansı Geçti", "Benchmark")
    pick("Konsensüse Katılıyor", "Konsensüs")
    pick("Konsensüs Ağırlığı %", "Ağırlık %")
    pick("RMSE", "RMSE")
    pick("Referans RMSE", "Benchmark RMSE")
    pick("RMSE İyileşme %", "İyileşme %")
    pick("RMSE / Referans RMSE", "RMSE Oranı")
    pick("RMSE Skoru", "RMSE Skoru")
    pick("Yön Doğruluğu %", "Yön Doğruluğu %")
    pick("Stabilite Skoru", "Stabilite")
    pick("Backtest Türü", "Test Türü")
    pick("Konsensüse Girememe Nedeni", "Karar Nedeni")

    if "Teknik" not in output.columns:
        output["Teknik"] = "—"

    if "Karar Nedeni" not in output.columns:
        output["Karar Nedeni"] = "—"

    for col in output.columns:
        output[col] = output[col].map(_clean_cell)

    number_cols = [
        "Ağırlık %",
        "RMSE",
        "Benchmark RMSE",
        "İyileşme %",
        "RMSE Oranı",
        "RMSE Skoru",
        "Yön Doğruluğu %",
        "Stabilite",
    ]

    for col in number_cols:
        if col in output.columns:
            output[col] = pd.to_numeric(output[col], errors="coerce").round(2)

    preferred = [
        "Model",
        "Teknik",
        "Benchmark",
        "Konsensüs",
        "Ağırlık %",
        "RMSE",
        "Benchmark RMSE",
        "İyileşme %",
        "RMSE Oranı",
        "RMSE Skoru",
        "Yön Doğruluğu %",
        "Stabilite",
        "Test Türü",
        "Karar Nedeni",
    ]

    visible = [col for col in preferred if col in output.columns]
    return output[visible]


def render_backtest_decision_panel(forecast_data: dict) -> None:
    backtest_df = forecast_data.get("backtest_df")

    if not isinstance(backtest_df, pd.DataFrame) or backtest_df.empty:
        st.warning("Backtest karar tablosu üretilemedi.")
        return

    decision_df = _build_decision_table(backtest_df)

    if decision_df.empty:
        st.warning("Backtest karar tablosu boş geldi.")
        return

    passed_count = 0
    consensus_count = 0
    best_rmse = None

    if "Benchmark" in decision_df.columns:
        passed_count = int(
            decision_df["Benchmark"].astype(str).str.lower().eq("evet").sum()
        )

    if "Konsensüs" in decision_df.columns:
        consensus_count = int(
            decision_df["Konsensüs"].astype(str).str.lower().eq("evet").sum()
        )

    if "RMSE" in decision_df.columns:
        rmse_series = pd.to_numeric(decision_df["RMSE"], errors="coerce").dropna()
        if not rmse_series.empty:
            best_rmse = float(rmse_series.min())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Benchmark Geçen Model", passed_count)

    with col2:
        st.metric("Konsensüse Giren Model", consensus_count)

    with col3:
        st.metric(
            "En Düşük RMSE",
            f"{best_rmse:.2f}" if best_rmse is not None else "—",
        )

    st.markdown("### Model Doğrulama ve Konsensüs Karar Tablosu")

    render_premium_table(
        decision_df,
        title="Model Karar Tablosu",
        subtitle=(
            "Bu tablo her modelin geçmiş test sonucunu, ortak tahmine girip girmediğini "
            "ve karar gerekçesini sade biçimde gösterir."
        ),
    )

    glossary = pd.DataFrame(
        [
            {
                "Terim": "Benchmark",
                "Sade anlamı": "Modelin kendini karşılaştırdığı basit kontrol çizgisi.",
            },
            {
                "Terim": "RMSE",
                "Sade anlamı": "Tahmin hatası. Düşük olması daha iyidir.",
            },
            {
                "Terim": "Yön doğruluğu",
                "Sade anlamı": "Model fiyatın yukarı mı aşağı mı gideceğini ne kadar doğru bilmiş.",
            },
            {
                "Terim": "Konsensüs",
                "Sade anlamı": "Ortak tahmine katılan modellerin ağırlıklı birleşimi.",
            },
            {
                "Terim": "Ağırlık",
                "Sade anlamı": "Modelin ortak tahminde ne kadar söz sahibi olduğu.",
            },
            {
                "Terim": "Karar nedeni",
                "Sade anlamı": "Modelin neden içeri alındığı veya dışarıda bırakıldığı.",
            },
        ]
    )

    render_premium_table(
        glossary,
        title="Bu Sayfadaki Terimler Ne Anlama Geliyor?",
        subtitle="Teknik terimlerin kullanıcı dostu karşılığı.",
    )
