import yfinance as yf

# 종목 설정 (애플 AAPL)
ticker = yf.Ticker("AAPL")
data = ticker.history(period="1y")

# 핵심 지표 가져오기
info = ticker.info
current_price = data['Close'].iloc[-1]
market_cap = info.get('marketCap', 'N/A')
prev_close = info.get('previousClose', 'N/A')
high_52 = info.get('fiftyTwoWeekHigh', 'N/A')
low_52 = info.get('fiftyTwoWeekLow', 'N/A')

print(f"--- 쏜힐 퀀트 엔진: AAPL 분석 ---")
print(f"현재가: {current_price:.2f}")
print(f"전일 종가: {prev_close}")
print(f"시가총액: {market_cap}")
print(f"52주 최고가: {high_52}")
print(f"52주 최저가: {low_52}")