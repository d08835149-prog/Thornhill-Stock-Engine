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

st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 420px; max-width: 420px; }
</style>
""", unsafe_allow_html=True)

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
    "last_updated":      {"English": "Data as of",            "Français": "Données au",          "فارسی": "داده‌ها تا",            "中文": "数据更新于",    "한국어": "데이터 기준"},
    "cache_note":        {"English": "refreshes every 10 min","Français": "actualisation 10 min","فارسی": "بروزرسانی هر ۱۰ دقیقه","中文": "每10分钟刷新",  "한국어": "10분마다 갱신"},
    "info":              {"English": "👈 Enter a period and tickers on the left, then click Analyze.", "Français": "👈 Entrez une période et des titres, puis cliquez sur Analyser.", "فارسی": "👈 دوره و نماد را وارد کنید، سپس تحلیل را بزنید.", "中文": "👈 在左侧输入周期和代码，然后点击分析。", "한국어": "👈 왼쪽에서 기간과 종목을 입력하고 분석하기를 눌러주세요."},
    "login":             {"English": "🔐 Login",               "Français": "🔐 Connexion",        "فارسی": "🔐 ورود",               "中文": "🔐 登录",       "한국어": "🔐 로그인"},
    "signup":            {"English": "📝 Sign Up",             "Français": "📝 Inscription",      "فارسی": "📝 ثبت‌نام",            "中文": "📝 注册",       "한국어": "📝 회원가입"},
    "nickname":          {"English": "Nickname",               "Français": "Pseudonyme",          "فارسی": "نام کاربری",            "中文": "昵称",          "한국어": "닉네임"},
    "password":          {"English": "Password",               "Français": "Mot de passe",        "فارسی": "رمز عبور",              "中文": "密码",          "한국어": "비밀번호"},
    "login_btn":         {"English": "Login",                  "Français": "Se connecter",        "فارسی": "ورود",                  "中文": "登录",          "한국어": "로그인"},
    "signup_btn":        {"English": "Create Account",         "Français": "Créer un compte",     "فارسی": "ایجاد حساب",            "中文": "创建账户",      "한국어": "계정 만들기"},
    "logout_btn":        {"English": "Logout",                 "Français": "Déconnexion",         "فارسی": "خروج",                  "中文": "退出",          "한국어": "로그아웃"},
    "welcome":           {"English": "Welcome",                "Français": "Bienvenue",           "فارسی": "خوش آمدید",             "中文": "欢迎",          "한국어": "환영해요"},
    "wrong_pw":          {"English": "❌ Wrong password.",     "Français": "❌ Mot de passe incorrect.", "فارسی": "❌ رمز اشتباه است.", "中文": "❌ 密码错误。", "한국어": "❌ 비밀번호가 틀렸어요."},
    "no_user":           {"English": "❌ Nickname not found.", "Français": "❌ Pseudonyme introuvable.", "فارسی": "❌ نام کاربری یافت نشد.", "中文": "❌ 未找到该昵称。", "한국어": "❌ 닉네임을 찾을 수 없어요."},
    "nick_taken":        {"English": "❌ Nickname already taken.", "Français": "❌ Pseudonyme déjà pris.", "فارسی": "❌ این نام قبلاً گرفته شده.", "中文": "❌ 昵称已被使用。", "한국어": "❌ 이미 사용 중인 닉네임이에요."},
    "account_created":   {"English": "✅ Account created! Please login.", "Français": "✅ Compte créé! Connectez-vous.", "فارسی": "✅ حساب ایجاد شد! وارد شوید.", "中文": "✅ 账户已创建！请登录。", "한국어": "✅ 계정이 만들어졌어요! 로그인해주세요."},
    "history":           {"English": "📂 My Analysis History", "Français": "📂 Mon historique",   "فارسی": "📂 تاریخچه تحلیل‌ها",   "中文": "📂 我的分析记录","한국어": "📂 내 분석 내역"},
    "no_history":        {"English": "No analysis history yet.", "Français": "Aucun historique.", "فارسی": "هنوز تاریخچه‌ای وجود ندارد.", "中文": "暂无分析记录。", "한국어": "아직 분석 내역이 없어요."},
    "load_history":      {"English": "Load",                   "Français": "Charger",             "فارسی": "بارگذاری",              "中文": "加载",          "한국어": "불러오기"},
    "login_required":    {"English": "👈 Please login or sign up to use the app.", "Français": "👈 Connectez-vous pour utiliser l'app.", "فارسی": "👈 برای استفاده وارد شوید.", "中文": "👈 请登录或注册以使用应用。", "한국어": "👈 로그인 또는 회원가입 후 이용해주세요."},
    "session_name":      {"English": "📁 Analysis Name (optional)", "Français": "📁 Nom de l'analyse (optionnel)", "فارسی": "📁 نام تحلیل (اختیاری)", "中文": "📁 分析名称（可选）", "한국어": "📁 분석 이름 (선택)"},
    "session_placeholder":{"English": "e.g. Tech Portfolio Q2", "Français": "ex: Portefeuille Tech", "فارسی": "مثال: پرتفوی فناوری", "中文": "例：科技股Q2", "한국어": "예: 테크 포트폴리오 Q2"},
    "change_pw":         {"English": "🔑 Change Password",    "Français": "🔑 Changer le mot de passe", "فارسی": "🔑 تغییر رمز عبور", "中文": "🔑 修改密码", "한국어": "🔑 비밀번호 변경"},
    "current_pw":        {"English": "Current Password",      "Français": "Mot de passe actuel",  "فارسی": "رمز فعلی",       "中文": "当前密码",   "한국어": "현재 비밀번호"},
    "new_pw":            {"English": "New Password",          "Français": "Nouveau mot de passe", "فارسی": "رمز جدید",       "中文": "新密码",     "한국어": "새 비밀번호"},
    "confirm_pw":        {"English": "Confirm New Password",  "Français": "Confirmer le nouveau", "فارسی": "تأیید رمز جدید", "中文": "确认新密码", "한국어": "새 비밀번호 확인"},
    "pw_changed":        {"English": "✅ Password changed!",  "Français": "✅ Mot de passe modifié!", "فارسی": "✅ رمز تغییر کرد!", "中文": "✅ 密码已修改！", "한국어": "✅ 비밀번호가 변경됐어요!"},
    "pw_mismatch":       {"English": "❌ Passwords don't match.", "Français": "❌ Les mots de passe ne correspondent pas.", "فارسی": "❌ رمزها یکسان نیستند.", "中文": "❌ 密码不匹配。", "한국어": "❌ 비밀번호가 일치하지 않아요."},
    "admin_page":        {"English": "🛡️ Admin Panel",        "Français": "🛡️ Panneau Admin",     "فارسی": "🛡️ پنل مدیریت",  "中文": "🛡️ 管理面板", "한국어": "🛡️ 관리자 페이지"},
    "total_users":       {"English": "Total Users",           "Français": "Utilisateurs",         "فارسی": "کل کاربران",     "中文": "总用户数",   "한국어": "전체 유저"},
    "total_trades":      {"English": "Total Analyses",        "Français": "Analyses totales",     "فارسی": "کل تحلیل‌ها",    "中文": "总分析次数", "한국어": "전체 분석 수"},
    "all_users":         {"English": "👥 All Users",          "Français": "👥 Tous les utilisateurs", "فارسی": "👥 همه کاربران", "中文": "👥 所有用户", "한국어": "👥 전체 유저 목록"},
    "all_trades":        {"English": "📊 All Trade Records",  "Français": "📊 Tous les trades",   "فارسی": "📊 همه معاملات",  "中文": "📊 所有交易记录", "한국어": "📊 전체 거래 내역"},
    "delete_user":       {"English": "🗑️ Delete User",        "Français": "🗑️ Supprimer",         "فارسی": "🗑️ حذف کاربر",   "中文": "🗑️ 删除用户", "한국어": "🗑️ 유저 삭제"},
    "user_deleted":      {"English": "✅ User deleted.",       "Français": "✅ Utilisateur supprimé.", "فارسی": "✅ کاربر حذف شد.", "中文": "✅ 用户已删除。", "한국어": "✅ 유저가 삭제됐어요."},
}

def t(key):
    return TRANSLATIONS[key][lang]

PERIODS = {
    "English": {"1 Day":"1d","3 Days":"5d","1 Week":"1wk","2 Weeks":"2wk","1 Month":"1mo","3 Months":"3mo","6 Months":"6mo","1 Year":"1y","2 Years":"2y","5 Years":"5y"},
    "Français":{"1 jour":"1d","3 jours":"5d","1 semaine":"1wk","2 semaines":"2wk","1 mois":"1mo","3 mois":"3mo","6 mois":"6mo","1 an":"1y","2 ans":"2y","5 ans":"5y"},
    "فارسی":   {"۱ روز":"1d","۳ روز":"5d","۱ هفته":"1wk","۲ هفته":"2wk","۱ ماه":"1mo","۳ ماه":"3mo","۶ ماه":"6mo","۱ سال":"1y","۲ سال":"2y","۵ سال":"5y"},
    "中文":    {"1天":"1d","3天":"5d","1周":"1wk","2周":"2wk","1个月":"1mo","3个月":"3mo","6个月":"6mo","1年":"1y","2年":"2y","5年":"5y"},
    "한국어":  {"1일":"1d","3일":"5d","1주일":"1wk","2주일":"2wk","1개월":"1mo","3개월":"3mo","6개월":"6mo","1년":"1y","2년":"2y","5년":"5y"},
}

# ── Session State Init ────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in  = False
    st.session_state.nickname   = ""
    st.session_state.load_tickers = []

if "show_admin" not in st.session_state:
    st.session_state.show_admin       = False
    st.session_state.admin_verified   = False

ADMIN_NICKNAME = st.secrets.get("ADMIN_NICKNAME", "Ditto")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "")

import hashlib

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def do_login(nickname, password):
    res = supabase.table("users").select("*").eq("nickname", nickname).execute()
    if not res.data:
        return "no_user"
    if res.data[0]["password"] != hash_pw(password):
        return "wrong_pw"
    st.session_state.logged_in = True
    st.session_state.nickname  = nickname
    return "ok"

def do_signup(nickname, password):
    existing = supabase.table("users").select("id").eq("nickname", nickname).execute()
    if existing.data:
        return "nick_taken"
    supabase.table("users").insert({
        "nickname": nickname,
        "password": hash_pw(password),
    }).execute()
    return "ok"

def do_change_pw(nickname, current_pw, new_pw):
    res = supabase.table("users").select("*").eq("nickname", nickname).execute()
    if not res.data or res.data[0]["password"] != hash_pw(current_pw):
        return "wrong_pw"
    supabase.table("users").update({"password": hash_pw(new_pw)}).eq("nickname", nickname).execute()
    return "ok"

# ── Title ─────────────────────────────────────────────────────
st.title("📈 Thornhill Stock Engine")

# ════════════════════════════════════════════════════════════
# Sidebar: Period + Ticker + Quantity Input
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.header(t("settings"))

    # ── Login / User Section ──────────────────────────────
    st.divider()
    if not st.session_state.logged_in:
        tab_login, tab_signup = st.tabs([t("login"), t("signup")])

        with tab_login:
            nick = st.text_input(t("nickname"), key="login_nick")
            pw   = st.text_input(t("password"), type="password", key="login_pw")
            if st.button(t("login_btn"), use_container_width=True):
                result = do_login(nick, pw)
                if result == "ok":
                    st.rerun()
                else:
                    st.error(t(result))

        with tab_signup:
            nick2 = st.text_input(t("nickname"), key="signup_nick")
            pw2   = st.text_input(t("password"), type="password", key="signup_pw")
            if st.button(t("signup_btn"), use_container_width=True):
                result = do_signup(nick2, pw2)
                if result == "ok":
                    st.success(t("account_created"))
                else:
                    st.error(t(result))
    else:
        col_w, col_l = st.columns([3, 1])
        col_w.markdown(f"👤 **{st.session_state.nickname}**")
        if col_l.button(t("logout_btn")):
            st.session_state.logged_in      = False
            st.session_state.nickname       = ""
            st.session_state.load_tickers   = []
            st.session_state.show_admin     = False
            st.session_state.admin_verified = False
            st.rerun()

        # ── Admin Button (Ditto only) ─────────────────────
        if st.session_state.nickname == ADMIN_NICKNAME:
            st.divider()
            if not st.session_state.admin_verified:
                st.caption("🛡️ Admin Access")
                admin_pw_input = st.text_input("Admin Password", type="password", key="admin_pw_input")
                if st.button(t("admin_page"), use_container_width=True, type="primary"):
                    if hash_pw(admin_pw_input) == hash_pw(ADMIN_PASSWORD):
                        st.session_state.admin_verified = True
                        st.session_state.show_admin     = True
                        st.rerun()
                    else:
                        st.error(t("wrong_pw"))
            else:
                if st.button(t("admin_page"), use_container_width=True, type="primary"):
                    st.session_state.show_admin = not st.session_state.show_admin
                    st.rerun()
                if st.button("🔒 Lock Admin", use_container_width=True):
                    st.session_state.admin_verified = False
                    st.session_state.show_admin     = False
                    st.rerun()

        # ── Change Password ───────────────────────────────
        with st.expander(t("change_pw")):
            cur_pw  = st.text_input(t("current_pw"),  type="password", key="cur_pw")
            new_pw1 = st.text_input(t("new_pw"),      type="password", key="new_pw1")
            new_pw2 = st.text_input(t("confirm_pw"),  type="password", key="new_pw2")
            if st.button(t("change_pw"), key="change_pw_btn", use_container_width=True):
                if new_pw1 != new_pw2:
                    st.error(t("pw_mismatch"))
                else:
                    result = do_change_pw(st.session_state.nickname, cur_pw, new_pw1)
                    if result == "ok":
                        st.success(t("pw_changed"))
                    else:
                        st.error(t(result))

        # ── Analysis History ──────────────────────────────
        st.subheader(t("history"))
        try:
            history = supabase.table("trades") \
                .select("*") \
                .eq("nickname", st.session_state.nickname) \
                .order("created_at", desc=True) \
                .limit(20) \
                .execute()
            if history.data:
                hist_df = pd.DataFrame(history.data)
                cols = ["session_name","ticker", "quantity", "price", "created_at"]
                cols = [c for c in cols if c in hist_df.columns]
                hist_df = hist_df[cols]
                hist_df["created_at"] = pd.to_datetime(hist_df["created_at"]).dt.strftime("%m/%d %H:%M")
                st.dataframe(hist_df, hide_index=True, use_container_width=True)

                latest_time  = history.data[0]["created_at"]
                latest_batch = [r for r in history.data if r["created_at"] == latest_time]
                if st.button(t("load_history"), use_container_width=True):
                    st.session_state.load_tickers = [
                        {"ticker": r["ticker"], "qty": r["quantity"]} for r in latest_batch
                    ]
                    st.rerun()
            else:
                st.caption(t("no_history"))
        except Exception as e:
            st.caption(f"Error: {e}")

    st.divider()
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
        col_t, col_e = st.columns([2, 2])
        tk_val = col_t.text_input(f"{t('ticker')} {i+1}", key=f"ticker_{i}", placeholder="AAPL")
        ex_val = col_e.selectbox("🌍", list(EXCHANGE_SUFFIX.keys()), key=f"exchange_{i}", label_visibility="hidden")
        q_val  = st.number_input(t("qty"), min_value=1, value=1, key=f"qty_{i}")
        if i < 9:
            st.divider()
        if tk_val.strip():
            suffix      = EXCHANGE_SUFFIX[ex_val]
            full_ticker = tk_val.strip().upper() + suffix
            ticker_qty_list.append({"ticker": full_ticker, "qty": int(q_val)})

    st.divider()
    session_name = st.text_input(t("session_name"), placeholder=t("session_placeholder"), key="session_name")
    analyze = st.button(t("analyze"), use_container_width=True)

# ════════════════════════════════════════════════════════════
# Cached Data Fetcher (10 min TTL)
# ════════════════════════════════════════════════════════════
@st.cache_data(ttl=600, show_spinner=False)
def fetch_ticker_data(ticker: str, period: str):
    obj = yf.Ticker(ticker)
    # yfinance에 2wk 없으므로 1mo 받고 14일 필터링
    fetch_period = "1mo" if period == "2wk" else period
    hist = obj.history(period=fetch_period)
    if hist.empty:
        return None, None
    if period == "2wk":
        cutoff = pd.Timestamp.now(tz=hist.index.tz) - pd.Timedelta(days=14)
        hist = hist[hist.index >= cutoff]
    return hist, obj.info

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
            hist, info = fetch_ticker_data(tk, period)
            if hist is not None:
                all_close[tk]   = hist["Close"]
                ticker_data[tk] = {"hist": hist, "info": info}
            else:
                st.warning(f"⚠️ {t('no_data')} {tk}.")

    if ticker_data:
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.caption(f"🕒 {t('last_updated')} {last_updated} · {t('cache_note')}")

    if not all_close:
        st.error(t("no_valid"))
        st.stop()

    # ── Save to Supabase ──────────────────────────────────
    try:
        for tk in ticker_data:
            close = ticker_data[tk]["hist"]["Close"]
            current_price = float(close.iloc[-1])
            supabase.table("trades").insert({
                "user_id":      st.session_state.nickname,
                "nickname":     st.session_state.nickname,
                "ticker":       tk,
                "quantity":     qty_map[tk],
                "price":        current_price,
                "session_name": session_name.strip() if session_name.strip() else None,
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
elif not st.session_state.logged_in:
    st.info(t("login_required"))
else:
    st.info(t("info"))

# ════════════════════════════════════════════════════════════
# Admin Panel (Ditto only)
# ════════════════════════════════════════════════════════════
if st.session_state.logged_in and st.session_state.nickname == ADMIN_NICKNAME and st.session_state.show_admin:
    st.divider()
    st.header(t("admin_page"))

    try:
        all_users  = supabase.table("users").select("*").order("created_at", desc=True).execute()
        all_trades = supabase.table("trades").select("*").order("created_at", desc=True).execute()

        col1, col2 = st.columns(2)
        col1.metric(t("total_users"),  len(all_users.data))
        col2.metric(t("total_trades"), len(all_trades.data))

        st.subheader(t("all_users"))
        if all_users.data:
            users_df = pd.DataFrame(all_users.data)[["nickname", "created_at"]]
            users_df["created_at"] = pd.to_datetime(users_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(users_df, hide_index=True, use_container_width=True)

            # 유저 삭제
            del_nick = st.selectbox(t("delete_user"),
                                    [u["nickname"] for u in all_users.data if u["nickname"] != ADMIN_NICKNAME])
            if st.button(t("delete_user"), key="del_user_btn"):
                supabase.table("trades").delete().eq("nickname", del_nick).execute()
                supabase.table("users").delete().eq("nickname", del_nick).execute()
                st.success(t("user_deleted"))
                st.rerun()

        st.subheader(t("all_trades"))
        if all_trades.data:
            trades_df = pd.DataFrame(all_trades.data)
            cols = ["nickname", "session_name", "ticker", "quantity", "price", "created_at"]
            cols = [c for c in cols if c in trades_df.columns]
            trades_df = trades_df[cols]
            trades_df["created_at"] = pd.to_datetime(trades_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(trades_df, hide_index=True, use_container_width=True)

    except Exception as e:
        st.error(f"Admin error: {e}")
