import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client
import requests
from datetime import datetime, timedelta

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(page_title="Thornhill Quant League", layout="wide")

# ── Supabase Connection ───────────────────────────────────────
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# ── Language Toggle ───────────────────────────────────────────
lang = st.radio("🌐 Language / Langue", ["English", "Français"], horizontal=True, label_visibility="collapsed")
FR = lang == "Français"

def t(en, fr):
    return fr if FR else en

# ── Title ─────────────────────────────────────────────────────
st.title("📈 Thornhill Quant League Engine")

# ════════════════════════════════════════════════════════════
# Sidebar: Period + Ticker + Quantity Input
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.header(t("⚙️ Settings", "⚙️ Paramètres"))

    period_map_en = {
        "1 Day":    "1d",
        "3 Days":   "5d",
        "1 Week":   "1wk",
        "1 Month":  "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year":   "1y",
        "2 Years":  "2y",
        "5 Years":  "5y",
    }
    period_map_fr = {
        "1 jour":   "1d",
        "3 jours":  "5d",
        "1 semaine":"1wk",
        "1 mois":   "1mo",
        "3 mois":   "3mo",
        "6 mois":   "6mo",
        "1 an":     "1y",
        "2 ans":    "2y",
        "5 ans":    "5y",
    }
    period_map = period_map_fr if FR else period_map_en
    period_label = st.selectbox(t("📅 Select Period", "📅 Sélectionner la période"), list(period_map.keys()), index=6)
    period = period_map[period_label]

    st.divider()
    st.subheader(t("🏢 Enter Tickers (up to 10)", "🏢 Entrer les titres (jusqu'à 10)"))
    st.caption(t("Enter tickers and quantity, then click Analyze.", "Entrez les titres et la quantité, puis cliquez sur Analyser."))

    ticker_qty_list = []
    for i in range(10):
        col_t, col_q = st.columns([2, 1])
        t_label = t(f"Ticker {i+1}", f"Titre {i+1}")
        q_label = t("Qty", "Qté")
        tk_val = col_t.text_input(t_label, key=f"ticker_{i}", placeholder="AAPL")
        q_val  = col_q.number_input(q_label, min_value=1, value=1, key=f"qty_{i}", label_visibility="visible")
        if tk_val.strip():
            ticker_qty_list.append({"ticker": tk_val.strip().upper(), "qty": int(q_val)})

    st.divider()
    analyze = st.button(t("🔍 Analyze", "🔍 Analyser"), use_container_width=True)

# ════════════════════════════════════════════════════════════
# Analysis
# ════════════════════════════════════════════════════════════
if analyze and ticker_qty_list:

    tickers_input = [item["ticker"] for item in ticker_qty_list]
    qty_map       = {item["ticker"]: item["qty"] for item in ticker_qty_list}

    # ── Load Data ─────────────────────────────────────────
    all_close   = {}
    ticker_data = {}

    with st.spinner(t("Loading data...", "Chargement des données...")):
        for tk in tickers_input:
            obj  = yf.Ticker(tk)
            hist = obj.history(period=period)
            if not hist.empty:
                all_close[tk]   = hist["Close"]
                ticker_data[tk] = {"hist": hist, "info": obj.info}
            else:
                st.warning(t(f"⚠️ Could not find data for {tk}.", f"⚠️ Données introuvables pour {tk}."))

    if not all_close:
        st.error(t("No valid ticker data found.", "Aucune donnée valide trouvée."))
        st.stop()

    # ── Save to Supabase ──────────────────────────────────
    try:
        for tk in ticker_data:
            close = ticker_data[tk]["hist"]["Close"]
            current_price = float(close.iloc[-1])
            supabase.table("trades").insert({
                "user_id":  "Ditto",
                "ticker":   tk,
                "quantity": qty_map[tk],
                "price":    current_price,
            }).execute()
        st.toast(t("✅ Saved to Supabase!", "✅ Sauvegardé dans Supabase!"), icon="💾")
    except Exception as e:
        st.warning(t(f"Save failed: {e}", f"Échec de la sauvegarde: {e}"))

    # ── 1. Portfolio Summary Table ────────────────────────
    st.subheader(t("📋 Portfolio Summary", "📋 Résumé du portefeuille"))

    summary_rows = []
    for tk in tickers_input:
        if tk not in ticker_data:
            continue
        hist          = ticker_data[tk]["hist"]
        close         = hist["Close"]
        qty           = qty_map[tk]
        start_price   = close.iloc[0]
        current_price = close.iloc[-1]
        ret_pct       = (current_price - start_price) / start_price * 100
        hold_value    = current_price * qty
        profit        = (current_price - start_price) * qty

        summary_rows.append({
            t("Ticker", "Titre"):                                      tk,
            t("Qty", "Qté"):                                           qty,
            t(f"Start Price ({period_label})", f"Prix initial ({period_label})"): f"${start_price:.2f}",
            t("Current Price", "Prix actuel"):                         f"${current_price:.2f}",
            t("Return", "Rendement"):                                  f"{ret_pct:+.2f}%",
            t("Market Value", "Valeur marchande"):                     f"${hold_value:,.2f}",
            "P&L":                                                     f"${profit:+,.2f}",
        })

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    # ── 2. Combined Price Chart ───────────────────────────
    st.divider()
    st.subheader(t("📊 Combined Close Price Chart", "📊 Graphique comparatif des prix"))
    fig_combined = go.Figure()
    for tk, close_series in all_close.items():
        fig_combined.add_trace(go.Scatter(
            x=close_series.index,
            y=close_series.values,
            mode="lines",
            name=tk,
            line=dict(width=2),
        ))
    fig_combined.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=t("Date", "Date"),
        yaxis_title=t("Close Price (USD)", "Prix de clôture (USD)"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_combined, use_container_width=True, config={"displayModeBar": False})

    # ── 3. Individual Stock Detail ────────────────────────
    st.divider()
    st.subheader("🔬 Individual Stock Analysis")

    for tk in tickers_input:
        if tk not in ticker_data:
            continue

        hist = ticker_data[tk]["hist"]
        info = ticker_data[tk]["info"]
        close = hist["Close"]

        # Indicators
        ma20        = close.rolling(20).mean()
        ma50        = close.rolling(50).mean()
        rolling_std = close.rolling(20).std()
        bb_upper    = ma20 + 2 * rolling_std
        bb_lower    = ma20 - 2 * rolling_std

        # Meta info
        current_price = info.get("currentPrice") or close.iloc[-1]
        prev_close    = info.get("previousClose", "N/A")
        open_price    = info.get("open", "N/A")
        day_high      = info.get("dayHigh", "N/A")
        day_low       = info.get("dayLow", "N/A")
        bid           = info.get("bid", "N/A")
        ask           = info.get("ask", "N/A")
        mkt_cap       = info.get("marketCap", None)
        mkt_cap_str   = f"${mkt_cap:,.0f}" if mkt_cap else "N/A"

        start_price = close.iloc[0]
        ret_pct     = (current_price - start_price) / start_price * 100
        ret_str     = f"{ret_pct:+.2f}%"

        with st.expander(f"📌 {tk}  |  {t('Current Price', 'Prix actuel')} ${current_price:.2f}  |  {t('Return', 'Rendement')} {ret_str}", expanded=True):

            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("Current Price", "Prix actuel"),  f"${current_price:.2f}" if isinstance(current_price, float) else current_price, delta=ret_str)
            col2.metric(t("Prev Close", "Clôture préc."),   f"${prev_close:.2f}"    if isinstance(prev_close, float)    else prev_close)
            col3.metric(t("Market Cap", "Capitalisation"),  mkt_cap_str)
            col4.metric("Bid / Ask",                        f"${bid} / ${ask}"      if bid != "N/A"                    else "N/A")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric(t("Open", "Ouverture"), f"${open_price:.2f}" if isinstance(open_price, float) else open_price)
            col6.metric(t("Close", "Clôture"),  f"${close.iloc[-1]:.2f}")
            col7.metric(t("High", "Haut"),      f"${day_high:.2f}"   if isinstance(day_high, float)   else day_high)
            col8.metric(t("Low", "Bas"),        f"${day_low:.2f}"    if isinstance(day_low, float)    else day_low)

            # Candlestick + Indicators Chart
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                row_heights=[0.75, 0.25],
                vertical_spacing=0.03,
                subplot_titles=(
                    t(f"{tk} Candlestick + Indicators", f"{tk} Chandeliers + Indicateurs"),
                    t("Volume", "Volume"),
                ),
            )

            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist["Open"], high=hist["High"],
                low=hist["Low"],   close=hist["Close"],
                name="OHLC",
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=hist.index, y=ma20, name="MA20",
                                     line=dict(color="#FFA726", width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=ma50, name="MA50",
                                     line=dict(color="#42A5F5", width=1.5)), row=1, col=1)

            fig.add_trace(go.Scatter(
                x=pd.concat([hist.index.to_series(), hist.index.to_series()[::-1]]),
                y=pd.concat([bb_upper, bb_lower[::-1]]),
                fill="toself", fillcolor="rgba(144,202,249,0.15)",
                line=dict(color="rgba(0,0,0,0)"), name="Bollinger Band",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=bb_upper, name="BB Upper",
                                     line=dict(color="#90CAF9", width=1, dash="dash")), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=bb_lower, name="BB Lower",
                                     line=dict(color="#90CAF9", width=1, dash="dash")), row=1, col=1)

            colors = ["#26a69a" if c >= o else "#ef5350"
                      for c, o in zip(hist["Close"], hist["Open"])]
            fig.add_trace(go.Bar(
                x=hist.index, y=hist["Volume"],
                marker_color=colors, name=t("Volume", "Volume"), showlegend=False,
            ), row=2, col=1)

            fig.update_layout(
                height=580,
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # ── News Section ──────────────────────────────
            st.subheader(t(f"📰 Latest News — {tk}", f"📰 Dernières nouvelles — {tk}"))
            finnhub_key = st.secrets.get("FINNHUB_API_KEY", "")
            if finnhub_key:
                try:
                    date_to   = datetime.now().strftime("%Y-%m-%d")
                    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                    url = (
                        f"https://finnhub.io/api/v1/company-news"
                        f"?symbol={tk}&from={date_from}&to={date_to}&token={finnhub_key}"
                    )
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        news = resp.json()
                        filtered = [n for n in news if tk in n.get("headline", "").upper()][:5]
                        if not filtered:
                            filtered = news[:5]
                        if filtered:
                            for item in filtered:
                                headline = item.get("headline", t("No Title", "Sans titre"))
                                news_url = item.get("url", "#")
                                source   = item.get("source", "")
                                dt       = datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d") if item.get("datetime") else ""
                                st.markdown(f"- **[{headline}]({news_url})** `{source}` {dt}")
                        else:
                            st.caption(t("No news found in the last 7 days.", "Aucune nouvelle trouvée dans les 7 derniers jours."))
                    else:
                        st.caption(t("Could not load news.", "Impossible de charger les nouvelles."))
                except Exception as e:
                    st.caption(t(f"News error: {e}", f"Erreur de nouvelles: {e}"))
            else:
                st.caption(t("🔑 Add `FINNHUB_API_KEY` to Streamlit secrets to enable news.",
                             "🔑 Ajoutez `FINNHUB_API_KEY` aux secrets Streamlit pour activer les nouvelles."))

elif analyze and not ticker_qty_list:
    st.warning(t("Please enter at least one ticker.", "Veuillez entrer au moins un titre."))
else:
    st.info(t("👈 Enter a period and tickers on the left sidebar, then click **Analyze**.",
              "👈 Entrez une période et des titres dans la barre latérale, puis cliquez sur **Analyser**."))
