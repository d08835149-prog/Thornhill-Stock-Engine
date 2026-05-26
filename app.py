import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client
import requests
from datetime import datetime, timedelta

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(page_title="Thornhill Stock League", layout="wide")

# ── Supabase Connection ───────────────────────────────────────
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# ── Language Toggle ───────────────────────────────────────────
lang = st.radio(
    "🌐",
    ["English", "Français", "فارسی", "中文", "한국어"],
    horizontal=True,
    label_visibility="collapsed"
)

TRANSLATIONS = {
    "settings":          {"English": "⚙️ Settings",         "Français": "⚙️ Paramètres",      "فارسی": "⚙️ تنظیمات",          "中文": "⚙️ 设置",       "한국어": "⚙️ 설정"},
    "select_period":     {"English": "📅 Select Period",     "Français": "📅 Période",          "فارسی": "📅 انتخاب دوره",       "中文": "📅 选择周期",    "한국어": "📅 기간 선택"},
    "enter_tickers":     {"English": "🏢 Enter Tickers (up to 10)", "Français": "🏢 Titres (max 10)", "فارسی": "🏢 نماد (حداکثر ۱۰)", "中文": "🏢 输入股票代码（最多10个）", "한국어": "🏢 티커 입력 (최대 10개)"},
    "caption":           {"English": "Enter tickers and quantity, then click Analyze.", "Français": "Entrez les titres et cliquez sur Analyser.", "فارسی": "نماد و تعداد را وارد کنید، سپس تحلیل را بزنید.", "中文": "输入代码和数量，然后点击分析。", "한국어": "티커와 수량을 입력한 뒤 분석하기를 눌러주세요."},
    "ticker":            {"English": "Ticker",               "Français": "Titre",               "فارسی": "نماد",                 "中文": "代码",          "한국어": "티커"},
    "qty":               {"English": "Qty",                  "Français": "Qté",                 "فارسی": "تعداد",                "中文": "数量",          "한국어": "수량"},
    "analyze":           {"English": "🔍 Analyze",           "Français": "🔍 Analyser",         "فارسی": "🔍 تحلیل",             "中文": "🔍 分析",       "한국어": "🔍 분석하기"},
    "loading":           {"English": "Loading data...",      "Français": "Chargement...",        "فارسی": "در حال بارگذاری...",   "中文": "加载数据中...", "한국어": "데이터 불러오는 중..."},
    "no_data":           {"English": "Could not find data for", "Français": "Données introuvables pour", "فارسی": "داده‌ای یافت نشد برای", "中文": "找不到数据：", "한국어": "데이터를 찾을 수 없어요:"},
    "no_valid":          {"English": "No valid ticker data found.", "Français": "Aucune donnée valide.", "فارسی": "هیچ داده‌ای یافت نشد.", "中文": "未找到有效数据。", "한국어": "유효한 종목 데이터가 없어요."},
    "saved":             {"English": "✅ Saved to Supabase!", "Français": "✅ Sauvegardé!",      "فارسی": "✅ ذخیره شد!",          "中文": "✅ 已保存！",   "한국어": "✅ Supabase에 저장 완료!"},
    "save_failed":       {"English": "Save failed",          "Français": "Échec sauvegarde",    "فارسی": "ذخیره ناموفق",         "中文": "保存失败",      "한국어": "저장 실패"},
    "portfolio":         {"English": "📋 Portfolio Summary", "Français": "📋 Résumé portefeuille","فارسی": "📋 خلاصه پرتفوی",      "中文": "📋 投资组合摘要","한국어": "📋 포트폴리오 요약"},
    "start_price":       {"English": "Start Price",          "Français": "Prix initial",        "فارسی": "قیمت ابتدایی",         "中文": "起始价格",      "한국어": "시작가"},
    "current_price":     {"English": "Current Price",        "Français": "Prix actuel",         "فارسی": "قیمت فعلی",            "中文": "当前价格",      "한국어": "현재가"},
    "return":            {"English": "Return",               "Français": "Rendement",           "فارسی": "بازده",                "中文": "收益率",        "한국어": "수익률"},
    "market_value":      {"English": "Market Value",         "Français": "Valeur marchande",    "فارسی": "ارزش بازار",           "中文": "市值",          "한국어": "평가금액"},
    "combined_chart":    {"English": "📊 Combined Close Price Chart", "Français": "📊 Graphique comparatif", "فارسی": "📊 نمودار مقایسه‌ای", "中文": "📊 综合收盘价图", "한국어": "📊 통합 종가 비교 차트"},
    "date":              {"English": "Date",                 "Français": "Date",                "فارسی": "تاریخ",                "中文": "日期",          "한국어": "날짜"},
    "close_price":       {"English": "Close Price (USD)",    "Français": "Prix clôture (USD)",  "فارسی": "قیمت بسته (USD)",      "中文": "收盘价 (USD)",  "한국어": "종가 (USD)"},
    "individual":        {"English": "🔬 Individual Stock Analysis", "Français": "🔬 Analyse individuelle", "فارسی": "🔬 تحلیل انفرادی", "中文": "🔬 个股详细分析", "한국어": "🔬 개별 종목 상세 분석"},
    "prev_close":        {"English": "Prev Close",           "Français": "Clôture préc.",       "فارسی": "بسته قبلی",            "中文": "前收盘价",      "한국어": "전일 종가"},
    "market_cap":        {"English": "Market Cap",           "Français": "Capitalisation",      "فارسی": "ارزش بازار",           "中文": "市值",          "한국어": "시가총액"},
    "open":              {"English": "Open",                 "Français": "Ouverture",           "فارسی": "باز",                  "中文": "开盘价",        "한국어": "시가"},
    "close":             {"English": "Close",                "Français": "Clôture",             "فارسی": "بسته",                 "中文": "收盘价",        "한국어": "종가"},
    "high":              {"English": "High",                 "Français": "Haut",                "فارسی": "بالاترین",             "中文": "最高价",        "한국어": "고가"},
    "low":               {"English": "Low",                  "Français": "Bas",                 "فارسی": "پایین‌ترین",           "中文": "最低价",        "한국어": "저가"},
    "candlestick":       {"English": "Candlestick + Indicators", "Français": "Chandeliers + Indicateurs", "فارسی": "شمع + شاخص‌ها", "中文": "K线图 + 指标", "한국어": "캔들 차트 + 보조지표"},
    "volume":            {"English": "Volume",               "Français": "Volume",              "فارسی": "حجم",                  "中文": "成交量",        "한국어": "거래량"},
    "latest_news":       {"English": "📰 Latest News",       "Français": "📰 Dernières nouvelles","فارسی": "📰 آخرین اخبار",       "中文": "📰 最新新闻",   "한국어": "📰 최신 뉴스"},
    "no_news":           {"English": "No news in the last 7 days.", "Français": "Aucune nouvelle (7j).", "فارسی": "خبری در ۷ روز گذشته نیست.", "中文": "过去7天无新闻。", "한국어": "최근 7일간 뉴스가 없어요."},
    "no_key":            {"English": "🔑 Add FINNHUB_API_KEY to secrets.", "Français": "🔑 Ajoutez FINNHUB_API_KEY.", "فارسی": "🔑 کلید FINNHUB_API_KEY را اضافه کنید.", "中文": "🔑 请添加 FINNHUB_API_KEY。", "한국어": "🔑 FINNHUB_API_KEY를 secrets에 추가해주세요."},
    "enter_one":         {"English": "Please enter at least one ticker.", "Français": "Entrez au moins un titre.", "فارسی": "حداقل یک نماد وارد کنید.", "中文": "请至少输入一个股票代码。", "한국어": "최소 1개 이상의 티커를 입력해주세요."},
    "info":              {"English": "👈 Enter a period and tickers on the left, then click Analyze.", "Français": "👈 Entrez une période et des titres, puis cliquez sur Analyser.", "فارسی": "👈 دوره و نماد را وارد کنید، سپس تحلیل را بزنید.", "中文": "👈 在左侧输入周期和代码，然后点击分析。", "한국어": "👈 왼쪽에서 기간과 종목을 입력하고 분석하기를 눌러주세요."},
}

def t(key):
    return TRANSLATIONS[key][lang]

PERIODS = {
    "English": {"1 Day":"1d","3 Days":"5d","1 Week":"1wk","1 Month":"1mo","3 Months":"3mo","6 Months":"6mo","1 Year":"1y","2 Years":"2y","5 Years":"5y"},
    "Français":{"1 jour":"1d","3 jours":"5d","1 semaine":"1wk","1 mois":"1mo","3 mois":"3mo","6 mois":"6mo","1 an":"1y","2 ans":"2y","5 ans":"5y"},
    "فارسی":   {"۱ روز":"1d","۳ روز":"5d","۱ هفته":"1wk","۱ ماه":"1mo","۳ ماه":"3mo","۶ ماه":"6mo","۱ سال":"1y","۲ سال":"2y","۵ سال":"5y"},
    "中文":    {"1天":"1d","3天":"5d","1周":"1wk","1个月":"1mo","3个月":"3mo","6个月":"6mo","1年":"1y","2年":"2y","5年":"5y"},
    "한국어":  {"1일":"1d","3일":"5d","1주일":"1wk","1개월":"1mo","3개월":"3mo","6개월":"6mo","1년":"1y","2년":"2y","5년":"5y"},
}

# ── Title ─────────────────────────────────────────────────────
st.title("📈 Thornhill Stock League Engine")

# ════════════════════════════════════════════════════════════
# Sidebar: Period + Ticker + Quantity Input
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.header(t("settings"))

    period_map   = PERIODS[lang]
    period_label = st.selectbox(t("select_period"), list(period_map.keys()), index=6)
    period       = period_map[period_label]

    st.divider()
    st.subheader(t("enter_tickers"))
    st.caption(t("caption"))

    EXCHANGE_SUFFIX = {
        "🇺🇸 US":  "",
        "🇨🇦 CA":  ".TO",
        "🇬🇧 UK":  ".L",
        "🇩🇪 DE":  ".DE",
        "🇯🇵 JP":  ".T",
        "🇰🇷 KR":  ".KS",
    }

    ticker_qty_list = []
    for i in range(10):
        col_t, col_e, col_q = st.columns([3, 2, 1])
        tk_val  = col_t.text_input(f"{t('ticker')} {i+1}", key=f"ticker_{i}", placeholder="AAPL")
        ex_val  = col_e.selectbox("Exchange", list(EXCHANGE_SUFFIX.keys()), key=f"exchange_{i}", label_visibility="collapsed")
        q_val   = col_q.number_input(t("qty"), min_value=1, value=1, key=f"qty_{i}", label_visibility="collapsed")
        if tk_val.strip():
            suffix     = EXCHANGE_SUFFIX[ex_val]
            full_ticker = tk_val.strip().upper() + suffix
            ticker_qty_list.append({"ticker": full_ticker, "qty": int(q_val)})

    st.divider()
    analyze = st.button(t("analyze"), use_container_width=True)

# ════════════════════════════════════════════════════════════
# Analysis
# ════════════════════════════════════════════════════════════
if analyze and ticker_qty_list:

    tickers_input = [item["ticker"] for item in ticker_qty_list]
    qty_map       = {item["ticker"]: item["qty"] for item in ticker_qty_list}

    # ── Load Data ─────────────────────────────────────────
    all_close   = {}
    ticker_data = {}

    with st.spinner(t("loading")):
        for tk in tickers_input:
            obj  = yf.Ticker(tk)
            hist = obj.history(period=period)
            if not hist.empty:
                all_close[tk]   = hist["Close"]
                ticker_data[tk] = {"hist": hist, "info": obj.info}
            else:
                st.warning(f"⚠️ {t('no_data')} {tk}.")

    if not all_close:
        st.error(t("no_valid"))
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
        st.toast(t("saved"), icon="💾")
    except Exception as e:
        st.warning(f"{t('save_failed')}: {e}")

    # ── 1. Portfolio Summary Table ────────────────────────
    st.subheader(t("portfolio"))

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
            t("ticker"):                               tk,
            t("qty"):                                  qty,
            f"{t('start_price')} ({period_label})":   f"${start_price:.2f}",
            t("current_price"):                        f"${current_price:.2f}",
            t("return"):                               f"{ret_pct:+.2f}%",
            t("market_value"):                         f"${hold_value:,.2f}",
            "P&L":                                     f"${profit:+,.2f}",
        })

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    # ── 2. Combined Price Chart ───────────────────────────
    st.divider()
    st.subheader(t("combined_chart"))
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
        xaxis_title=t("date"),
        yaxis_title=t("close_price"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_combined, use_container_width=True, config={"displayModeBar": False})

    # ── 3. Individual Stock Detail ────────────────────────
    st.divider()
    st.subheader(t("individual"))

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

        with st.expander(f"📌 {tk}  |  {t('current_price')} ${current_price:.2f}  |  {t('return')} {ret_str}", expanded=True):

            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("current_price"), f"${current_price:.2f}" if isinstance(current_price, float) else current_price, delta=ret_str)
            col2.metric(t("prev_close"),    f"${prev_close:.2f}"    if isinstance(prev_close, float)    else prev_close)
            col3.metric(t("market_cap"),    mkt_cap_str)
            col4.metric("Bid / Ask",        f"${bid} / ${ask}"      if bid != "N/A"                    else "N/A")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric(t("open"),  f"${open_price:.2f}" if isinstance(open_price, float) else open_price)
            col6.metric(t("close"), f"${close.iloc[-1]:.2f}")
            col7.metric(t("high"),  f"${day_high:.2f}"   if isinstance(day_high, float)   else day_high)
            col8.metric(t("low"),   f"${day_low:.2f}"    if isinstance(day_low, float)    else day_low)

            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                row_heights=[0.75, 0.25],
                vertical_spacing=0.03,
                subplot_titles=(f"{tk} {t('candlestick')}", t("volume")),
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
                marker_color=colors, name=t("volume"), showlegend=False,
            ), row=2, col=1)

            fig.update_layout(
                height=580,
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # ── News Section ──────────────────────────────
            st.subheader(f"{t('latest_news')} — {tk}")
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
                                headline = item.get("headline", "—")
                                news_url = item.get("url", "#")
                                source   = item.get("source", "")
                                dt       = datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d") if item.get("datetime") else ""
                                st.markdown(f"- **[{headline}]({news_url})** `{source}` {dt}")
                        else:
                            st.caption(t("no_news"))
                    else:
                        st.caption(t("no_news"))
                except Exception as e:
                    st.caption(f"Error: {e}")
            else:
                st.caption(t("no_key"))

elif analyze and not ticker_qty_list:
    st.warning(t("enter_one"))
else:
    st.info(t("info"))
