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

@st.cache_data(ttl=300)
def get_market_news():
    try:
        url = "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        headlines = [item.find('title').text.strip() for item in root.findall('.//item')[:5] if item.find('title') is not None]
        if headlines: return "📰 LIVE ET NEWS: " + " 🔹 ".join(headlines) + " 🔹"
    except: pass
    return "📰 LIVE MARKET NEWS: Fetching latest feeds... 🔹"

@st.cache_data(ttl=60)
def get_real_sector_performance():
    results = []
    for sector, stocks in FNO_SECTORS.items():
        if sector == "MIXED WATCHLIST": continue
        total_pct, valid = 0, 0
        for ticker in stocks:
            _, _, pct = get_live_data(ticker)
            if pct != 0.0:
                total_pct += pct
                valid += 1
        if valid > 0:
            avg_pct = round(total_pct / valid, 2)
            bw = min(abs(avg_pct) * 20, 100) 
            results.append({"Sector": sector, "Pct": avg_pct, "Width": max(bw, 5)})
    return sorted(results, key=lambda x: x['Pct'], reverse=True)

@st.cache_data(ttl=60)
def get_adv_dec(stock_list):
    adv, dec = 0, 0
    for ticker in stock_list:
        _, change, _ = get_live_data(ticker)
        if change > 0: adv += 1
        elif change < 0: dec += 1
    return adv, dec

@st.cache_data(ttl=120)
def get_dynamic_market_data(stock_list):
    gainers, losers, trends = [], [], []
    for ticker in stock_list:
        try:
            df = yf.Ticker(ticker).history(period="10d")
            if len(df) >= 3:
                c1, o1 = df['Close'].iloc[-1], df['Open'].iloc[-1]
                c2, o2 = df['Close'].iloc[-2], df['Open'].iloc[-2]
                c3, o3 = df['Close'].iloc[-3], df['Open'].iloc[-3]
                pct_chg = ((c1 - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                obj = {"Stock": ticker, "LTP": round(c1, 2), "Pct": round(pct_chg, 2)}
                if pct_chg > 0: gainers.append(obj)
                elif pct_chg < 0: losers.append(obj)
                if c1 > o1 and c2 > o2 and c3 > o3:
                    trends.append({"Stock": ticker, "Status": "৩ দিন উত্থান", "Color": "green"})
                elif c1 < o1 and c2 < o2 and c3 < o3:
                    trends.append({"Stock": ticker, "Status": "৩ দিন পতন", "Color": "red"})
        except: pass
    return sorted(gainers, key=lambda x: x['Pct'], reverse=True)[:4], sorted(losers, key=lambda x: x['Pct'])[:4], trends

@st.cache_data(ttl=60)
def get_gap_scans(stock_list):
    gaps = []
    for ticker in stock_list:
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if len(df) >= 2:
                prev_close, today_open = df['Close'].iloc[-2], df['Open'].iloc[-1]
                gap_pct = ((today_open - prev_close) / prev_close) * 100
                if abs(gap_pct) >= 3.0:
                    status, color = ("GAP UP", "green") if gap_pct > 0 else ("GAP DOWN", "red")
                    gaps.append({"Stock": ticker, "Open": round(today_open,2), "Pct": round(gap_pct,2), "Status": status, "Color": color})
        except: pass
    return sorted(gaps, key=lambda x: abs(x['Pct']), reverse=True)

@st.cache_data(ttl=60)
def get_opening_movers(stock_list):
    movers = []
    for ticker in stock_list:
        ltp, _, pct = get_live_data(ticker)
        if abs(pct) >= 2.0:
            movers.append({"Stock": ticker, "LTP": ltp, "Pct": pct})
    return sorted(movers, key=lambda x: abs(x['Pct']), reverse=True)

@st.cache_data(ttl=60)
def get_oi_simulation(stock_list):
    setups = []
    for ticker in stock_list:
        try:
            df = yf.Ticker(ticker).history(period="2d", interval="15m")
            if len(df) >= 2:
                c1, v1 = df['Close'].iloc[-1], df['Volume'].iloc[-1]
                c2, v2 = df['Close'].iloc[-2], df['Volume'].iloc[-2]
                if v1 > (v2 * 1.5): 
                    if c1 > c2: setups.append({"Stock": ticker, "Signal": "Long Buildup", "Vol": "High", "Color": "green"})
                    else: setups.append({"Stock": ticker, "Signal": "Short Buildup", "Vol": "High", "Color": "red"})
        except: pass
    return setups

@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            stock = yf.Ticker(stock_symbol)
            df = stock.history(period="5d", interval="5m") 
            if df.empty or len(df) < 15: continue
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            today_date = df.index[-1].date()
            df_today = df[df.index.date == today_date].copy()
            if len(df_today) < 4: continue # Skip first 3 candles (9:15-9:30)
            
            # Master Logic: Lowest Vol + Opposite Color
            completed_idx = len(df_today) - 2
            completed_candle = df_today.iloc[completed_idx]
            min_vol_so_far = df_today.iloc[:completed_idx+1]['Volume'].min()
            
            is_lowest_vol = (completed_candle['Volume'] <= min_vol_so_far)
            is_green, is_red = completed_candle['Close'] > completed_candle['Open'], completed_candle['Close'] < completed_candle['Open']
            
            signal = None
            if market_sentiment == "BULLISH" and is_red and is_lowest_vol: signal = "BUY"
            elif market_sentiment == "BEARISH" and is_green and is_lowest_vol: signal = "SHORT"
            
            if signal:
                entry = (completed_candle['High'] + 0.50) if signal == "BUY" else (completed_candle['Low'] - 0.50)
                sl = (completed_candle['Low'] - 0.50) if signal == "BUY" else (completed_candle['High'] + 0.50)
                risk = abs(entry - sl)
                t1, t2 = entry + (risk * 2) if signal == "BUY" else entry - (risk * 2), entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                signals.append({"Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(completed_candle['Close'], 2), "Signal": signal, "SL": round(sl, 2), "T1": round(t1, 2), "T2(1:3)": round(t2, 2), "EMA_10": round(completed_candle['EMA10'], 2), "Action": "Book 50% @ 1:3", "Time": completed_candle.name.strftime('%H:%M:%S')})
        except: continue
    return signals

# --- 4. CSS (Titled v38.0 and Responsive) ---
css_string = (
    "<style>"
    "#MainMenu {visibility: hidden;} footer {visibility: hidden;} "
    ".stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; } "
    ".top-nav { background-color: #002b36; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #00ffd0; border-radius: 8px; margin-bottom: 10px; } "
    ".section-title { color: #003366; font-size: 13px; font-weight: bold; padding: 4px 5px; text-transform: uppercase; border-bottom: 2px solid #b0c4de; margin-bottom: 10px; } "
    ".v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; background: white; border: 1px solid #b0c4de; margin-bottom: 10px; } "
    ".v38-table th { background-color: #4f81bd; color: white; padding: 8px; } "
    ".v38-table td { padding: 8px; border: 1px solid #b0c4de; } "
    ".idx-container { display: flex; justify-content: space-between; background: white; border: 1px solid #b0c4de; padding: 5px; margin-bottom: 10px; flex-wrap: wrap; border-radius: 5px; } "
    ".idx-box { text-align: center; width: 23%; padding: 5px; } "
    ".adv-dec-bar { display: flex; height: 14px; border-radius: 4px; overflow: hidden; margin: 8px 0; } "
    ".bar-green { background-color: #2e7d32; } .bar-red { background-color: #d32f2f; } "
    ".ticker { background: #fff3cd; color: #856404; padding: 6px 15px; font-size: 13px; font-weight: bold; border-radius: 5px; margin-bottom: 15px; } "
    ".table-container { overflow-x: auto; width: 100%; } "
    "</style>"
)
st.markdown(css_string, unsafe_allow_html=True)

# --- 5. Sidebar ---
with st.sidebar:
    st.markdown("### 🎛️ HARIDAS DASHBOARD")
    page_selection = st.radio("Select Menu:", ["📈 MAIN TERMINAL", "🌅 9:10 AM: Pre-Market Gap", "🚀 9:15 AM: Opening Movers", "🔥 9:20 AM: OI Setup", "📊 Backtest Engine"])
    st.divider()
    user_sentiment = st.radio("Market Sentiment:", ["BULLISH", "BEARISH"])
    selected_sector = st.selectbox("Select Watchlist:", list(FNO_SECTORS.keys()))
    auto_refresh = st.checkbox("Enable Auto-Refresh")
    refresh_time = st.selectbox("Interval:", [1, 3, 5, 15], index=0)
    if st.button("🔄 Force Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 6. Top Navigation ---
curr_time = datetime.datetime.now()
nav_html = f"<div class='top-nav'><div style='color:#00ffd0; font-weight:bold; font-size:20px;'>📊 HARIDAS NSE TERMINAL</div><div style='color:white;'>🕒 {curr_time.strftime('%H:%M:%S')}</div></div><div class='ticker'><marquee>{get_market_news()}</marquee></div>"
st.markdown(nav_html, unsafe_allow_html=True)

# --- 7. Pages ---
if page_selection == "📈 MAIN TERMINAL":
    col1, col2, col3 = st.columns([1, 2.8, 1])
    
    with col1:
        st.markdown("<div class='section-title'>📊 SECTOR PERFORMANCE</div>", unsafe_allow_html=True)
        real_sectors = get_real_sector_performance()
        if real_sectors:
            sec_html = "<div class='table-container'><table class='v38-table'><tr><th>Sector</th><th>Avg %</th></tr>"
            for s in real_sectors:
                c = "green" if s['Pct'] >= 0 else "red"
                sec_html += f"<tr><td>{s['Sector']}</td><td style='color:{c}; font-weight:bold;'>{s['Pct']}%</td></tr>"
            sec_html += "</table></div>"
            st.markdown(sec_html, unsafe_allow_html=True)

    with col2:
        # Indices and Adv/Dec
        n_ltp, n_chg, n_pct = get_live_data("^NSEI")
        bn_ltp, bn_chg, bn_pct = get_live_data("^NSEBANK")
        indices_html = f"<div class='idx-container'><div class='idx-box'>NIFTY 50<br><b>{n_ltp}</b><br><small>{n_pct}%</small></div><div class='idx-box'>BANK NIFTY<br><b>{bn_ltp}</b><br><small>{bn_pct}%</small></div></div>"
        st.markdown(indices_html, unsafe_allow_html=True)
        
        adv, dec = get_adv_dec(ALL_STOCKS)
        adv_p = (adv/(adv+dec))*100 if (adv+dec)>0 else 50
        st.markdown(f"<div class='adv-dec-bar'><div class='bar-green' style='width:{adv_p}%'></div><div class='bar-red' style='width:{100-adv_p}%'></div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'>🎯 LIVE SIGNALS: {selected_sector}</div>", unsafe_allow_html=True)
        live_signals = exhaustion_scanner(FNO_SECTORS[selected_sector], user_sentiment)
        if live_signals:
            st.table(pd.DataFrame(live_signals))
            st.download_button("📥 Export CSV", pd.DataFrame(live_signals).to_csv(index=False), "signals.csv")
        else: st.info("⏳ Waiting for setup (Opposite Color + Low Vol)...")

    with col3:
        st.markdown("<div class='section-title'>🚀 TOP GAINERS</div>", unsafe_allow_html=True)
        g, l, _ = get_dynamic_market_data(ALL_STOCKS)
        if g: st.table(pd.DataFrame(g))

elif page_selection == "📊 Backtest Engine":
    st.header("📊 Backtest Engine (Last 5 Days)")
    test_stock = st.selectbox("Stock:", ALL_STOCKS)
    back_sent = st.radio("Sentiment:", ["BULLISH", "BEARISH"], horizontal=True)
    if st.button("Run Analysis"):
        df = yf.download(test_stock, period="5d", interval="5m")
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        results = []
        for i in range(10, len(df)):
            candle = df.iloc[i]
            prev_v = df['Volume'].iloc[i-10:i].min() # Look back 10 candles for min vol
            is_low_vol = candle['Volume'] <= prev_v
            is_red, is_green = candle['Close'] < candle['Open'], candle['Close'] > candle['Open']
            
            sig = None
            if back_sent == "BULLISH" and is_red and is_low_vol: sig = "BUY"
            elif back_sent == "BEARISH" and is_green and is_low_vol: sig = "SHORT"
            
            if sig:
                risk = (candle['High'] - candle['Low']) + 1.0
                t2 = candle['High'] + (risk*3) if sig == "BUY" else candle['Low'] - (risk*3)
                results.append({"Time": df.index[i], "Price": round(candle['Close'],2), "Signal": sig, "Target(1:3)": round(t2,2), "EMA10": round(candle['EMA10'],2)})
        st.dataframe(pd.DataFrame(results), use_container_width=True)

elif page_selection == "🌅 9:10 AM: Pre-Market Gap":
    st.table(pd.DataFrame(get_gap_scans(ALL_STOCKS)))

elif page_selection == "🚀 9:15 AM: Opening Movers":
    st.table(pd.DataFrame(get_opening_movers(ALL_STOCKS)))

elif page_selection == "🔥 9:20 AM: OI Setup":
    st.table(pd.DataFrame(get_oi_simulation(ALL_STOCKS)))

if auto_refresh:
    time.sleep(refresh_time * 60)
    st.rerun()
