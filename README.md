# 📈 Thornhill Stock League Engine

A multi-language stock analysis platform built for the Thornhill Stock League community in Canada.

---

## 🚀 Features

### 📊 Analysis
- Analyze up to **10 tickers simultaneously**
- Supported exchanges: 🇺🇸 US, 🇨🇦 CA, 🇬🇧 UK, 🇩🇪 DE, 🇯🇵 JP, 🇰🇷 KR
- Time periods: 1 Day → 5 Years (including exact 2-week window)
- **Combined price chart** for side-by-side comparison
- **Individual stock charts** with:
  - Candlestick (OHLC)
  - MA20 / MA50
  - Bollinger Bands (Upper / Lower)
  - Volume bars
- Key metrics: Current Price, Prev Close, Market Cap, Bid/Ask, Open, Close, High, Low
- **Latest news** per ticker via Finnhub API

### 💼 Portfolio
- Quantity input per ticker
- Portfolio summary table: Start Price, Current Price, Return %, Market Value, P&L
- Name and save each analysis session
- Load previous analysis sessions from history

### 👤 User System
- Nickname + Password authentication (SHA-256 hashed)
- Sign up / Login / Logout
- Change password
- Personal analysis history (last 20 records)

### 🛡️ Admin Panel (Ditto only)
- Secured with a separate admin password
- View all users and total analysis count
- View all trade records
- Delete users and their data

### 🌐 Multilingual Support
- 🇬🇧 English
- 🇫🇷 Français
- 🇮🇷 فارسی (Persian)
- 🇨🇳 中文
- 🇰🇷 한국어

### ⚡ Performance
- Data cached for **10 minutes** to prevent API rate limiting
- Cache timestamp displayed on screen

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Charts | Plotly |
| Market Data | yfinance |
| News | Finnhub API |
| Database | Supabase (PostgreSQL) |
| Hosting | Streamlit Community Cloud |

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/Thornhill-Stock-Engine.git
cd Thornhill-Stock-Engine
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure secrets
Create `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
FINNHUB_API_KEY = "your_finnhub_key"
ADMIN_NICKNAME = "Ditto"
ADMIN_PASSWORD = "your_admin_password"
```

### 4. Set up Supabase tables
Run in Supabase SQL Editor:
```sql
create table users (
  id uuid default gen_random_uuid() primary key,
  nickname text unique not null,
  password text not null,
  created_at timestamptz default now()
);

create table trades (
  id bigint primary key generated always as identity,
  user_id text,
  nickname text,
  ticker text,
  quantity integer,
  price numeric,
  session_name text,
  analysis_style text,
  created_at timestamptz default now()
);
```

### 5. Run locally
```bash
streamlit run app.py
```

---

## 🌐 Deployment

Deployed on **Streamlit Community Cloud**.  
Add all secrets under **App Settings → Secrets** in the Streamlit Cloud dashboard.

---

## 📌 Notes

- This app is for **analysis purposes only**
- Actual mock trading is done via **MooMoo Trade**
- Stock data refreshes every **10 minutes** to avoid API rate limits

---

## 🍁 Made for Thornhill Stock League — Canada

---

## 👨‍💻 Credits

| Role | Name |
|---|---|
| Developer | Ditto A. |
| AI Assistant | Claude (Anthropic) |
