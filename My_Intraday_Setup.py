import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import time
import urllib.request
import xml.etree.ElementTree as ET

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="Haridas Master Terminal v41.0", initial_sidebar_state="expanded")

# --- 2. Live Market Data & PURE LIVE Engines (NO DUMMY DATA) ---
FNO_SECTORS = {
    "MIXED WATCHLIST": ["HINDALCO.NS", "NTPC.NS", "WIPRO.NS", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS"],
    "NIFTY METAL": ["HINDALCO.NS", "TATASTEEL.NS", "VEDL.NS", "JSWSTEEL.NS", "NMDC.NS", "COALINDIA.NS"],
    "NIFTY BANK": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "INDUSINDBK.NS"],
    "NIFTY IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS"],
    "NIFTY ENERGY": ["RELIANCE.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "TATAPOWER.NS"],
    "NIFTY AUTO": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
    "NIFTY PHARMA": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "NIFTY FMCG": ["ITC.NS", "HUL.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "NIFTY INFRA": ["LT.NS", "LICI.NS", "ULTRACEMCO.NS"],
    "NIFTY REALTY": ["DLF.NS", "GODREJPROP.NS", "MACROTECH.NS"],
    "NIFTY PSU BANK": ["SBIN.NS", "PNB.NS", "BOB.NS", "CANBK.NS"]
}

ALL_STOCKS = list(set([stock for slist in FNO_SECTORS.values() for stock in slist]))

@st.cache_data(ttl=30)
def get_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period='5d')
        if not df.empty:
            ltp = df['Close'].iloc[-1]
            try: prev_close = stock.fast_info.previous_close
            except: prev_close = df['Close'].iloc[-2] if len(df) > 1 else ltp
            change = ltp - prev_close
            pct_change = (change / prev_close) * 100 if prev_close != 0 else 0
            return round(ltp, 2), round(change, 2), round(pct_change, 2)
        return 0.0, 0.0, 0.0
    except: return 0.0, 0.0, 0.0

@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            df = yf.Ticker(stock_symbol).history(period="5d", interval="5m") 
            if df.empty or len(df) < 15: continue
            
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            today_df = df[df.index.date == df.index[-1].date()].copy()
            
            # Rule: Ignore 9:15 to 9:30 (First 3 candles)
            if len(today_df) < 4: continue 
            
            completed_candle = today_df.iloc[-2] # Last closed candle
            # Lowest Volume Logic
            min_vol = today_df.iloc[:-1]['Volume'].min()
            is_lowest_vol = completed_candle['Volume'] <= min_vol
            
            # Color Logic
            is_green = completed_candle['Close'] > completed_candle['Open']
            is_red = completed_candle['Close'] < completed_candle['Open']
            
            signal = None
            if market_sentiment == "BULLISH" and is_red and is_lowest_vol: signal = "BUY"
            elif market_sentiment == "BEARISH" and is_green and is_lowest_vol: signal = "SHORT"
            
            if signal:
                entry = (completed_candle['High'] + 0.5) if signal == "BUY" else (completed_candle['Low'] - 0.5)
                sl = (completed_candle['Low'] - 0.5) if signal == "BUY" else (completed_candle['High'] + 0.5)
                risk = abs(entry - sl)
                t2 = entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                
                signals.append({
                    "Stock": stock_symbol, "Signal": signal, "Entry": round(entry,2), 
                    "SL": round(sl,2), "T2(1:3)": round(t2,2), "EMA10": round(completed_candle['EMA10'],2),
                    "Time": completed_candle.name.strftime('%H:%M')
                })
        except: continue
    return signals

# --- UI Layout (তোর অরিজিনাল ইন্টারফেস) ---
css_string = "<style>.stApp { background-color: #f0f4f8; } .v38-table { width:100%; border:1px solid #b0c4de; text-align:center; }</style>"
st.markdown(css_string, unsafe_allow_html=True)

with st.sidebar:
    st.title("🎛️ HARIDAS SETTINGS")
    page = st.radio("Menu", ["📈 LIVE TERMINAL", "📊 BACKTEST ENGINE"])
    user_sentiment = st.radio("Sentiment", ["BULLISH", "BEARISH"])
    selected_sector = st.selectbox("Watchlist", list(FNO_SECTORS.keys()))

if page == "📈 LIVE TERMINAL":
    st.subheader(f"🎯 LIVE SIGNALS - {selected_sector}")
    live_results = exhaustion_scanner(FNO_SECTORS[selected_sector], user_sentiment)
    if live_results:
        st.table(pd.DataFrame(live_results))
    else:
        st.info("সঠিক সেটআপের জন্য অপেক্ষা করছি (৯:৩০ এর পর সিগন্যাল আসবে)...")

elif page == "📊 BACKTEST ENGINE":
    st.subheader("📊 ৫ দিনের ব্যাকটেস্ট রিপোর্ট")
    target_stock = st.selectbox("শেয়ার সিলেক্ট কর", ALL_STOCKS)
    if st.button("Run Backtest"):
        # Real historical engine
        hist = yf.download(target_stock, period="5d", interval="5m")
        hist['EMA10'] = hist['Close'].ewm(span=10, adjust=False).mean()
        bt_results = []
        for i in range(10, len(hist)):
            candle = hist.iloc[i]
            # Simple Backtest Scan
            if candle['Volume'] < hist['Volume'].iloc[i-5:i].min():
                bt_results.append({"Time": hist.index[i], "Price": candle['Close'], "EMA10": candle['EMA10']})
        st.dataframe(pd.DataFrame(bt_results))
