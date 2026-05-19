import streamlit as st
import yfinance as yf

st.title("Thornhill Quant League Engine")
st.write("실시간 데이터를 분석하는 쏜힐 고교 공식 퀀트 대시보드입니다.")

ticker_input = st.text_input("분석할 티커를 입력하세요 (예: AAPL, NVDA):", "AAPL")

if st.button("분석 시작"):
    ticker = yf.Ticker(ticker_input)
    hist = ticker.history(period="1y")
    info = ticker.info
    
    st.write(f"### {ticker_input} 분석 결과")
    st.line_chart(hist['Close'])
    
    col1, col2 = st.columns(2)
    col1.metric("현재가", f"${hist['Close'].iloc[-1]:.2f}")
    col2.metric("시가총액", info.get('marketCap', 'N/A'))