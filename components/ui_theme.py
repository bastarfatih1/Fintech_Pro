"""
Global premium UI theme.

Bu modül uygulamanın genel görsel dilini tek yerden yönetir:
- Kayan piyasa bandı
- Analiz butonu
- Input ve select kutuları
- Metric kartları
- Expander / bilgi kutuları
- Tab görünümü
- Dataframe / tablo çevresi
- Alt işlem menüsü

Amaç:
Bloomberg terminali ciddiyeti + modern fintech dashboard hissi.
"""

import streamlit as st


def inject_global_premium_theme() -> None:
    """Uygulama genelinde premium CSS temasını uygular."""
    st.markdown(
        """
        <style>
        :root {
            --fp-bg: #020617;
            --fp-panel: rgba(15, 23, 42, 0.84);
            --fp-panel-soft: rgba(30, 41, 59, 0.64);
            --fp-border: rgba(148, 163, 184, 0.24);
            --fp-border-strong: rgba(56, 189, 248, 0.34);
            --fp-text: #f8fafc;
            --fp-muted: #94a3b8;
            --fp-soft: #cbd5e1;
            --fp-blue: #38bdf8;
            --fp-green: #86efac;
            --fp-gold: #fde68a;
            --fp-red: #fca5a5;
            --fp-shadow: 0 18px 48px rgba(2, 6, 23, 0.28);
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 12% 0%, rgba(56, 189, 248, 0.10), transparent 30%),
                radial-gradient(circle at 88% 8%, rgba(34, 197, 94, 0.08), transparent 26%),
                linear-gradient(180deg, #020617 0%, #0f172a 48%, #020617 100%) !important;
        }

        [data-testid="stHeader"] {
            background: rgba(2, 6, 23, 0.52) !important;
            backdrop-filter: blur(14px);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.98)) !important;
            border-right: 1px solid var(--fp-border);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--fp-text) !important;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label {
            color: var(--fp-soft) !important;
        }

        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 8.5rem;
            max-width: 1420px;
        }

        h1, h2, h3, h4 {
            letter-spacing: -0.02em;
        }

        /* Kayan piyasa bandı */
        .ticker-bar {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 18px;
            padding: 10px 14px;
            margin: 0 0 16px 0;
            background:
                linear-gradient(90deg, rgba(2, 6, 23, 0.95), rgba(15, 23, 42, 0.92)),
                radial-gradient(circle at left, rgba(56, 189, 248, 0.18), transparent 35%);
            box-shadow: var(--fp-shadow);
        }

        .ticker-bar::before {
            content: "LIVE MARKET";
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            border: 1px solid rgba(134, 239, 172, 0.32);
            border-radius: 999px;
            padding: 3px 8px;
            background: rgba(22, 163, 74, 0.12);
            color: var(--fp-green);
            font-size: 0.68rem;
            font-weight: 850;
            letter-spacing: 0.12em;
            z-index: 2;
        }

        .ticker-bar marquee {
            color: #e0f2fe;
            font-size: 0.92rem;
            font-weight: 650;
            letter-spacing: 0.02em;
            padding-left: 115px;
            text-shadow: 0 0 18px rgba(56, 189, 248, 0.26);
        }

        /* Ana aksiyon butonu */
        div.stButton > button {
            border: 1px solid rgba(56, 189, 248, 0.38) !important;
            border-radius: 18px !important;
            padding: 0.88rem 1.1rem !important;
            background:
                radial-gradient(circle at 20% 20%, rgba(255,255,255,0.22), transparent 18%),
                linear-gradient(135deg, #0284c7 0%, #2563eb 48%, #0f172a 100%) !important;
            color: white !important;
            font-weight: 850 !important;
            letter-spacing: 0.01em !important;
            box-shadow:
                0 16px 36px rgba(37, 99, 235, 0.28),
                inset 0 1px 0 rgba(255,255,255,0.18) !important;
            transition: transform 160ms ease, box-shadow 160ms ease, border 160ms ease !important;
        }

        div.stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(134, 239, 172, 0.52) !important;
            box-shadow:
                0 20px 45px rgba(56, 189, 248, 0.30),
                inset 0 1px 0 rgba(255,255,255,0.22) !important;
        }

        div.stButton > button:active {
            transform: translateY(0px) scale(0.995);
        }

        /* Primary button custom signal mark */
        div.stButton > button::before {
            content: "";
            width: 18px;
            height: 18px;
            display: inline-block;
            margin-right: 8px;
            border: 1.7px solid rgba(255, 255, 255, 0.82);
            border-radius: 50%;
            background:
                radial-gradient(circle at 50% 50%, rgba(134, 239, 172, 0.95) 0 18%, transparent 20%),
                radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.34) 0 52%, transparent 54%);
            box-shadow:
                0 0 0 3px rgba(56, 189, 248, 0.11),
                0 0 18px rgba(56, 189, 248, 0.30);
            vertical-align: -3px;
        }


        /* Input / select alanları */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        input,
        textarea {
            border-radius: 16px !important;
            border-color: rgba(148, 163, 184, 0.30) !important;
            background: rgba(15, 23, 42, 0.72) !important;
            color: var(--fp-text) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }

        div[data-baseweb="select"] > div:hover,
        div[data-baseweb="input"] > div:hover,
        input:hover,
        textarea:hover {
            border-color: rgba(56, 189, 248, 0.42) !important;
        }

        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="input"] > div:focus-within {
            border-color: rgba(134, 239, 172, 0.54) !important;
            box-shadow: 0 0 0 1px rgba(134, 239, 172, 0.18) !important;
        }

        label,
        [data-testid="stWidgetLabel"] {
            color: var(--fp-soft) !important;
            font-weight: 700 !important;
        }

        /* Metric kartları */
        [data-testid="stMetric"] {
            border: 1px solid var(--fp-border);
            border-radius: 18px;
            padding: 14px 16px;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
            box-shadow: 0 10px 30px rgba(2, 6, 23, 0.16);
        }

        [data-testid="stMetricLabel"] {
            color: var(--fp-muted) !important;
            font-weight: 750;
        }

        [data-testid="stMetricValue"] {
            color: var(--fp-text) !important;
            font-weight: 850;
        }

        [data-testid="stMetricDelta"] {
            font-weight: 800;
        }

        /* Tabs */
        div[data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.16);
            padding-bottom: 6px;
        }

        button[data-baseweb="tab"] {
            display: inline-flex !important;
            align-items: center !important;
            border-radius: 999px !important;
            margin-right: 0 !important;
            padding: 8px 12px !important;
            color: var(--fp-soft) !important;
            background: rgba(15, 23, 42, 0.48) !important;
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.035);
            transition: all 160ms ease;
        }

        button[data-baseweb="tab"]::before {
            content: "";
            width: 15px;
            height: 15px;
            display: inline-block;
            margin-right: 7px;
            border-radius: 6px;
            border: 1px solid rgba(226, 232, 240, 0.28);
            background:
                linear-gradient(135deg, rgba(56, 189, 248, 0.72), rgba(99, 102, 241, 0.30));
            box-shadow: 0 0 14px rgba(56, 189, 248, 0.18);
        }

        div[data-baseweb="tab-list"] button:nth-child(1)::before {
            border-radius: 4px;
            background:
                linear-gradient(180deg, rgba(134, 239, 172, 0.90), rgba(14, 165, 233, 0.28));
        }

        div[data-baseweb="tab-list"] button:nth-child(2)::before {
            border-radius: 50%;
            background:
                radial-gradient(circle at 50% 50%, rgba(134, 239, 172, 0.95) 0 20%, transparent 22%),
                radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.50) 0 56%, transparent 58%);
        }

        div[data-baseweb="tab-list"] button:nth-child(3)::before {
            border-radius: 5px;
            background:
                linear-gradient(135deg, rgba(56, 189, 248, 0.88), rgba(14, 165, 233, 0.18)),
                linear-gradient(90deg, transparent 0 38%, rgba(255,255,255,0.55) 39% 43%, transparent 44%);
        }

        div[data-baseweb="tab-list"] button:nth-child(4)::before {
            border-radius: 5px;
            background:
                linear-gradient(135deg, rgba(253, 230, 138, 0.92), rgba(56, 189, 248, 0.22));
        }

        button[data-baseweb="tab"]:hover {
            color: white !important;
            border-color: rgba(56, 189, 248, 0.34) !important;
            transform: translateY(-1px);
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: white !important;
            border-color: rgba(56, 189, 248, 0.44) !important;
            background:
                linear-gradient(135deg, rgba(14, 165, 233, 0.30), rgba(99, 102, 241, 0.23)) !important;
            box-shadow:
                0 10px 30px rgba(14, 165, 233, 0.12),
                inset 0 1px 0 rgba(255,255,255,0.08);
        }

        /* Expander / alerts / captions */
        [data-testid="stExpander"] {
            border: 1px solid var(--fp-border) !important;
            border-radius: 16px !important;
            background: rgba(15, 23, 42, 0.40) !important;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--fp-muted) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 16px !important;
            border: 1px solid rgba(148, 163, 184, 0.20) !important;
        }

        /* Dataframe ve tablo çevresi */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid var(--fp-border);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 12px 32px rgba(2, 6, 23, 0.16);
        }

        /* Alt işlem menüsü */
        .floating-action-bar {
            position: fixed;
            left: 50%;
            bottom: 10px;
            transform: translateX(-50%);
            z-index: 999;
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: center;
            padding: 8px 10px;
            border: 1px solid rgba(56, 189, 248, 0.28);
            border-radius: 999px;
            background:
                linear-gradient(135deg, rgba(2, 6, 23, 0.88), rgba(15, 23, 42, 0.82));
            backdrop-filter: blur(16px);
            box-shadow: 0 14px 38px rgba(2, 6, 23, 0.34);
        }

        .fp-action-btn {
            border: 1px solid rgba(226, 232, 240, 0.12);
            border-radius: 999px;
            padding: 7px 11px;
            color: var(--fp-soft);
            font-size: 0.82rem;
            font-weight: 750;
            background: rgba(15, 23, 42, 0.55);
            transition: all 150ms ease;
            cursor: pointer;
        }

        .fp-action-btn:hover {
            color: white;
            border-color: rgba(56, 189, 248, 0.40);
            transform: translateY(-1px);
            background: rgba(14, 165, 233, 0.18);
        }

        .fp-action-btn-primary {
            color: white;
            border-color: rgba(134, 239, 172, 0.36);
            background:
                linear-gradient(135deg, rgba(14, 165, 233, 0.35), rgba(34, 197, 94, 0.18));
        }


        /* Custom inline SVG icon system */
        .fp-icon,
        .fp-icon-small,
        .fp-icon-tiny {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            vertical-align: middle;
            color: currentColor;
            flex: 0 0 auto;
        }

        .fp-icon svg,
        .fp-icon-small svg,
        .fp-icon-tiny svg {
            display: block;
        }

        .fp-icon {
            width: 24px;
            height: 24px;
            margin-right: 8px;
        }

        .fp-icon svg {
            width: 24px;
            height: 24px;
        }

        .fp-icon-small {
            width: 18px;
            height: 18px;
            margin-right: 6px;
        }

        .fp-icon-small svg {
            width: 18px;
            height: 18px;
        }

        .fp-icon-tiny {
            width: 15px;
            height: 15px;
            margin-right: 5px;
        }

        .fp-icon-tiny svg {
            width: 15px;
            height: 15px;
        }

        .fp-title-with-icon,
        .fp-pill-with-icon,
        .fp-action-content {
            display: inline-flex;
            align-items: center;
            gap: 0;
        }

        .fp-title-with-icon .fp-icon {
            color: var(--fp-blue);
            filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.32));
        }

        .fp-pill-with-icon .fp-icon-small {
            color: var(--fp-green);
        }

        .fp-action-content .fp-icon-small {
            color: currentColor;
        }

        /* Footer compact icon sizing */
        .floating-action-bar .fp-icon-small {
            width: 15px;
            height: 15px;
            margin-right: 5px;
        }

        .floating-action-bar .fp-icon-small svg {
            width: 15px;
            height: 15px;
        }



        /* Küçük ekranlar */
        @media (max-width: 760px) {
            .floating-action-bar {
                width: calc(100% - 22px);
                overflow-x: auto;
                justify-content: flex-start;
                border-radius: 22px;
            }

            .fp-action-btn {
                white-space: nowrap;
            }

            .ticker-bar::before {
                display: none;
            }

            .ticker-bar marquee {
                padding-left: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
