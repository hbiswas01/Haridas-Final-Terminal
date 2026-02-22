import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import time
import urllib.request
import xml.etree.ElementTree as ET

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="Haridas Master Terminal v41.0", initial_sidebar_state="expanded")

# --- 2. Live Market Data & PURE LIVE Engines ---
FNO_SECTORS = {
    "MIXED WATCHLIST": ["HINDALCO.NS", "NTPC.NS", "WIPRO.NS", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS"],
    "NIFTY METAL": ["HINDALCO.NS", "TATASTEEL.NS", "VEDL.NS", "JSWSTEEL.NS", "NMDC.NS", "COALINDIA.NS"],
    "NIFTY BANK": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "INDUSINDBK.NS"],
    "NIFTY IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS"],
    "NIFTY ENERGY": ["RELIANCE.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "TATAPOWER.NS"],
    "NIFTY AUTO": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
    "NIFTY PHARMA": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "NIFTY FMCG": ["ITC.NS", "HUL.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "NIFTY PSU BANK": ["SBIN.NS", "PNB.NS", "BOB.NS", "CANBK.NS"]
}

ALL_STOCKS = list(set([stock for slist in FNO_SECTORS.values() for stock in slist]))

# --- Data Fetching Functions ---
@st.cache_data(ttl=30)
def get_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period='2d')
        if not df.empty:
            ltp = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change = ltp - prev_close
            pct_change = (change / prev_close) * 100
            return round(ltp, 2), round(change, 2), round(pct_change, 2)
    except: pass
    return 0.0, 0.0, 0.0

@st.cache_data(ttl=300)
def get_market_news():
    try:
        url = "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        headlines = [item.find('title').text.strip() for item in root.findall('.//item')[:5]]
        return "📰 LIVE NEWS: " + " 🔹 ".join(headlines) + " 🔹"
    except: return "📰 LIVE MARKET NEWS: Fetching latest feeds... 🔹"

# --- 🧠 REAL STRATEGY ENGINE (Train Emptying Out) ---
def exhaustion_scanner(stock_list, market_sentiment):
    signals = []
    for stock_symbol in stock_list:
        try:
            df = yf.Ticker(stock_symbol).history(period="5d", interval="5m")
            if df.empty or len(df) < 15: continue
            
            # EMA 10 Engine
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            today_df = df[df.index.date == df.index[-1].date()].copy()
            
            # 9:15 - 9:30 Ignore (First 3 candles)
            if len(today_df) < 4: continue 
            
            completed_candle = today_df.iloc[-2] # Last closed candle
            min_vol_today = today_df.iloc[:-1]['Volume'].min()
            
            is_lowest_vol = (completed_candle['Volume'] <= min_vol_today)
            is_green = completed_candle['Close'] > completed_candle['Open']
            is_red = completed_candle['Close'] < completed_candle['Open']
            
            signal = None
            if market_sentiment == "BULLISH" and is_red and is_lowest_vol:
                signal = "BUY"
                entry = completed_candle['High'] + 0.50
                sl = completed_candle['Low'] - 0.50
            elif market_sentiment == "BEARISH" and is_green and is_lowest_vol:
                signal = "SHORT"
                entry = completed_candle['Low'] - 0.50
                sl = completed_candle['High'] + 0.50
            
            if signal:
                risk = abs(entry - sl)
                signals.append({
                    "Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(completed_candle['Close'], 2),
                    "Signal": signal, "SL": round(sl, 2), "T1": round(entry + (risk*2 if signal=="BUY" else -risk*2), 2),
                    "T2(1:3)": round(entry + (risk*3 if signal=="BUY" else -risk*3), 2),
                    "EMA_10": round(completed_candle['EMA10'], 2), "Action": "Book 50% @ 1:3 & Trail",
                    "Time": completed_candle.name.strftime('%H:%M')
                })
        except: continue
    return signals

# --- 4. CSS (v38.0 UI Responsive) ---
st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; }
    .top-nav { background-color: #002b36; padding: 10px; border-bottom: 3px solid #00ffd0; color: white; display: flex; justify-content: space-between; border-radius: 8px; }
    .section-title { color: #003366; font-size: 14px; font-weight: bold; border-bottom: 2px solid #b0c4de; margin: 15px 0 10px 0; padding-bottom: 5px; }
    .v38-table { width: 100%; border-collapse: collapse; background: white; font-size: 11px; }
    .v38-table th { background: #4f81bd; color: white; padding: 8px; border: 1px solid #ddd; }
    .v38-table td { padding: 8px; border: 1px solid #ddd; text-align: center; }
    .ticker-bar { background: #fff3cd; color: #856404; padding: 8px; font-weight: bold; margin-bottom: 10px; border-radius: 5px; }
    @media (max-width: 768px) { .stTable { overflow-x: auto; } }
</style>
""", unsafe_allow_html=True)

# --- 5. Sidebar Navigation ---
with st.sidebar:
    st.markdown("### 🎛️ HARIDAS MASTER")
    page_selection = st.radio("Menu:", ["📈 MAIN TERMINAL", "📊 BACKTEST ENGINE", "🌅 9:10 AM GAP", "🚀 9:15 AM MOVERS", "🔥 9:20 AM OI"])
    st.divider()
    user_sentiment = st.radio("Market Sentiment:", ["BULLISH", "BEARISH"])
    selected_sector = st.selectbox("Select Watchlist:", list(FNO_SECTORS.keys()))
    auto_refresh = st.checkbox("Enable Auto-Refresh")
    refresh_time = st.selectbox("Interval (Min):", [1, 3, 5], index=0)
    if st.button("🔄 Force Refresh"): st.cache_data.clear(); st.rerun()

# --- 6. Top Nav & Ticker ---
curr_time = datetime.datetime.now().strftime('%H:%M:%S')
st.markdown(f"""
<div class='top-nav'>
    <div style='font-size: 18px; font-weight: bold;'>📊 HARIDAS NSE TERMINAL v41.0</div>
    <div style='color: #ffeb3b;'>🕒 {curr_time} | LIVE MARKET</div>
</div>
<div class='ticker-bar'><marquee scrollamount='5'>{get_market_news()}</marquee></div>
""", unsafe_allow_html=True)

# --- 7. Page Routing ---
if page_selection == "📈 MAIN TERMINAL":
    col1, col2, col3 = st.columns([1, 2.5, 1])
    
    with col1:
        st.markdown("<div class='section-title'>📊 SECTOR STATUS</div>", unsafe_allow_html=True)
        # Sector Performance logic
        sec_data = []
        for s, stocks in FNO_SECTORS.items():
            if s == "MIXED WATCHLIST": continue
            _, _, p = get_live_data(stocks[0])
            sec_data.append({"Sector": s, "Change": p})
        st.table(pd.DataFrame(sec_data))

    with col2:
        st.markdown(f"<div class='section-title'>🎯 LIVE SIGNALS: {selected_sector}</div>", unsafe_allow_html=True)
        signals = exhaustion_scanner(FNO_SECTORS[selected_sector], user_sentiment)
        if signals:
            df_sig = pd.DataFrame(signals)
            st.table(df_sig)
            st.download_button("📥 Download Excel", df_sig.to_csv(index=False), "signals.csv")
        else:
            st.info("⏳ Waiting for Lowest Volume + Opposite Color setup (Post 9:30 AM)...")

    with col3:
        st.markdown("<div class='section-title'>🚀 TOP MOVERS</div>", unsafe_allow_html=True)
        movers = []
        for s in FNO_SECTORS["MIXED WATCHLIST"]:
            ltp, chg, pct = get_live_data(s)
            movers.append({"Stock": s, "LTP": ltp, "%": pct})
        st.table(pd.DataFrame(movers))

elif page_selection == "📊 BACKTEST ENGINE":
    st.header("📊 Deep Backtest Engine (Last 5 Days)")
    bt_stock = st.selectbox("Select Stock:", ALL_STOCKS)
    if st.button("Analyze History"):
        hist = yf.download(bt_stock, period="5d", interval="5m")
        hist['EMA10'] = hist['Close'].ewm(span=10, adjust=False).mean()
        # Logic to find setup in history
        hits = []
        for i in range(10, len(hist)):
            if hist['Volume'].iloc[i] <= hist['Volume'].iloc[i-10:i].min():
                hits.append({"Time": hist.index[i], "Price": round(hist['Close'].iloc[i], 2), "EMA10": round(hist['EMA10'].iloc[i], 2)})
        st.write(pd.DataFrame(hits))

# --- Auto Refresh ---
if auto_refresh:
    time.sleep(refresh_time * 60)
    st.rerun()
