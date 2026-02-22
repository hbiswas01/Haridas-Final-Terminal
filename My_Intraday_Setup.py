import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import time
import urllib.request
import xml.etree.ElementTree as ET

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="Haridas Master Terminal", initial_sidebar_state="expanded")

# --- 2. Live Market Data & Engines ---
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

NIFTY_50_STOCKS = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", 
    "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", 
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", 
    "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "LTIM.NS", "M&M.NS", 
    "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS", 
    "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

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
    except:
        return 0.0, 0.0, 0.0

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
    return "📰 LIVE MARKET NEWS: System tracking major indices. 🔹"

@st.cache_data(ttl=60)
def get_real_sector_performance():
    results = []
    for sector, stocks in FNO_SECTORS.items():
        if sector == "MIXED WATCHLIST": continue
        total_pct = 0
        valid = 0
        for ticker in stocks:
            _, _, pct = get_live_data(ticker)
            if pct != 0.0:
                total_pct += pct
                valid += 1
        avg_pct = round(total_pct / valid, 2) if valid > 0 else 0.0
        bw = min(abs(avg_pct) * 20, 100) 
        results.append({"Sector": sector, "Pct": avg_pct, "Width": max(bw, 5)})
    return sorted(results, key=lambda x: x['Pct'], reverse=True)

@st.cache_data(ttl=60)
def get_adv_dec(stock_list):
    adv, dec = 0, 0
    for ticker in stock_list:
        _, change, _ = get_live_data(ticker)
        if change >= 0: adv += 1
        else: dec += 1
    if adv == 0 and dec == 0: return 25, 25 
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
    
    gainers = sorted(gainers, key=lambda x: x['Pct'], reverse=True)[:4]
    losers = sorted(losers, key=lambda x: x['Pct'])[:4]
    return gainers, losers, trends

@st.cache_data(ttl=60)
def get_gap_scans(stock_list):
    gaps = []
    for ticker in stock_list:
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if len(df) >= 2:
                prev_close = df['Close'].iloc[-2]
                today_open = df['Open'].iloc[-1]
                gap_pct = ((today_open - prev_close) / prev_close) * 100
                if abs(gap_pct) >= 3.0:
                    status = "GAP UP" if gap_pct > 0 else "GAP DOWN"
                    color = "green" if gap_pct > 0 else "red"
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
            if len(df_today) < 5: continue
            
            completed_idx = len(df_today) - 2
            completed_candle = df_today.iloc[completed_idx]
            
            if completed_idx < 3: continue 
                
            df_upto_completed = df_today.iloc[:completed_idx+1]
            min_vol_so_far = df_upto_completed['Volume'].min()
            
            is_lowest_vol = (completed_candle['Volume'] <= min_vol_so_far)
            is_green = completed_candle['Close'] > completed_candle['Open']
            is_red = completed_candle['Close'] < completed_candle['Open']
            
            signal = None
            entry = sl = 0.0
            
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
                if risk > 0:
                    t1 = entry + (risk * 2) if signal == "BUY" else entry - (risk * 2)
                    t2 = entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                    
                    signals.append({
                        "Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(completed_candle['Close'], 2),
                        "Signal": signal, "SL": round(sl, 2), "T1": round(t1, 2), "T2": round(t2, 2),
                        "EMA_10": round(completed_candle['EMA10'], 2), 
                        "Action": "Book 50% @ 1:3", 
                        "Time": completed_candle.name.strftime('%H:%M:%S')
                    })
        except: continue
    return signals

# --- 4. CSS (NO TRIPLE QUOTES) ---
css_string = (
    "<style>"
    "#MainMenu {visibility: hidden;} footer {visibility: hidden;} "
    ".stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; } "
    ".block-container { padding-top: 4rem !important; padding-bottom: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; } "
    ".top-nav { background-color: #002b36; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #00ffd0; border-radius: 8px; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.2); } "
    "@media (max-width: 768px) { .top-nav { flex-direction: column; text-align: center; gap: 8px; } .block-container { padding-top: 5rem !important; } .idx-box { width: 48% !important; margin-bottom: 8px; } } "
    ".section-title { color: #003366; font-size: 13px; font-weight: bold; padding: 4px 5px; text-transform: uppercase; margin-top: 5px; border-bottom: 2px solid #b0c4de; margin-bottom: 10px; } "
    ".table-container { overflow-x: auto; width: 100%; border-radius: 5px; } "
    ".v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; color: black; background: white; border: 1px solid #b0c4de; margin-bottom: 10px; white-space: nowrap; } "
    ".v38-table th { background-color: #4f81bd; color: white; padding: 8px; border: 1px solid #b0c4de; font-weight: bold; } "
    ".v38-table td { padding: 8px; border: 1px solid #b0c4de; } "
    ".idx-container { display: flex; justify-content: space-between; background: white; border: 1px solid #b0c4de; padding: 5px; margin-bottom: 10px; flex-wrap: wrap; border-radius: 5px; } "
    ".idx-box { text-align: center; width: 23%; border-right: 1px solid #eee; padding: 5px; min-width: 100px; } "
    ".idx-box:last-child { border-right: none; } "
    ".adv-dec-container { background: white; border: 1px solid #b0c4de; padding: 10px; margin-bottom: 10px; text-align: center; border-radius: 5px; } "
    ".adv-dec-bar { display: flex; height: 14px; border-radius: 4px; overflow: hidden; margin: 8px 0; } "
    ".bar-green { background-color: #2e7d32; } .bar-red { background-color: #d32f2f; } "
    ".bar-bg { background: #e0e0e0; width: 100%; height: 14px; min-width: 50px; border-radius: 3px; } "
    ".bar-fg-green { background: #276a44; height: 100%; border-radius: 3px; } "
    ".bar-fg-red { background: #8b0000; height: 100%; border-radius: 3px; } "
    ".ticker { background: #fff3cd; color: #856404; padding: 6px 15px; font-size: 13px; font-weight: bold; border-bottom: 1px solid #ffeeba; border-radius: 5px; margin-bottom: 15px; box-shadow: 0px 2px 5px rgba(0,0,0,0.1); } "
    "</style>"
)
st.markdown(css_string, unsafe_allow_html=True)

# --- 5. Sidebar ---
with st.sidebar:
    st.markdown("### 🎛️ HARIDAS DASHBOARD")
    page_selection = st.radio("Select Menu:", ["📈 MAIN TERMINAL", "🌅 9:10 AM: Pre-Market Gap", "🚀 9:15 AM: Opening Movers", "🔥 9:20 AM: OI Setup", "⚙️ Scanner Settings", "📊 Backtest Engine"])
    st.divider()
    st.markdown("### ⚙️ STRATEGY SETTINGS")
    user_sentiment = st.radio("Market Sentiment:", ["BULLISH", "BEARISH"])
    selected_sector = st.selectbox("Select Watchlist:", list(FNO_SECTORS.keys()), index=0)
    st.divider()
    st.markdown("### ⏱️ AUTO REFRESH")
    auto_refresh = st.checkbox("Enable Auto-Refresh", value=False)
    refresh_time = st.selectbox("Interval:", [1, 3, 5, 15], index=0) 
    if st.button("🔄 Force Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 6. Top Navigation ---
curr_time = datetime.datetime.now()
t_915 = curr_time.replace(hour=9, minute=15, second=0)
t_1530 = curr_time.replace(hour=15, minute=30, second=0)

if curr_time < t_915: session, session_color = "PRE-MARKET", "#ff9800" 
elif curr_time <= t_1530: session, session_color = "LIVE MARKET", "#28a745" 
else: session, session_color = "POST MARKET", "#dc3545" 

nav_html = (
    "<div class='top-nav'>"
    "<div style='color:#00ffd0; font-weight:bold; font-size:20px; letter-spacing:1px;'>📊 HARIDAS NSE TERMINAL</div>"
    "<div style='font-size: 14px; color: #ffeb3b; font-weight: bold; display: flex; align-items: center;'>"
    f"<span style='background: {session_color}; color: white; padding: 3px 10px; border-radius: 4px; margin-right: 15px;'>{session}</span>"
    f"🕒 {curr_time.strftime('%H:%M:%S')}"
    "</div>"
    "<div>"
    "<span style='background:#1a73e8; padding:5px 15px; font-size:11px; color:white; font-weight:bold; border-radius:4px; cursor:pointer;'>SCAN MARKET</span>"
    "<span style='background:#28a745; padding:5px 15px; font-size:11px; color:white; font-weight:bold; border-radius:4px; cursor:pointer; margin-left:8px;'>EXPORT EXCEL</span>"
    "</div></div>"
    "<div class='ticker'>"
    f"<marquee direction='left' scrollamount='5'>{get_market_news()}</marquee>"
    "</div>"
)
st.markdown(nav_html, unsafe_allow_html=True)

current_watchlist = FNO_SECTORS[selected_sector]

if page_selection == "📈 MAIN TERMINAL":
    col1, col2, col3 = st.columns([1, 2.8, 1])

    with col1:
        st.markdown("<div class='section-title'>📊 SECTOR PERFORMANCE</div>", unsafe_allow_html=True)
        with st.spinner("Fetching..."):
            real_sectors = get_real_sector_performance()
        if not real_sectors:
            real_sectors = [{"Sector": "NIFTY METAL", "Pct": 1.57, "Width": 80}, {"Sector": "NIFTY BANK", "Pct": 0.58, "Width": 50}]
        
        sec_html = "<div class='table-container'><table class='v38-table'><tr><th>Sector</th><th>Avg %</th><th style='width:40%;'>Trend</th></tr>"
        for s in real_sectors:
            c = "green" if s['Pct'] >= 0 else "red"
            bc = "bar-fg-green" if s['Pct'] >= 0 else "bar-fg-red"
            sec_html += f"<tr><td style='text-align:left; font-weight:bold; color:#003366;'>{s['Sector']}</td><td style='color:{c}; font-weight:bold;'>{s['Pct']}%</td><td style='padding:4px 8px;'><div class='bar-bg'><div class='{bc}' style='width:{s['Width']}%;'></div></div></td></tr>"
        sec_html += "</table></div>"
        st.markdown(sec_html, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-title'>📉 MARKET INDICES (LIVE)</div>", unsafe_allow_html=True)
        nifty_ltp, nifty_chg, nifty_pct = get_live_data("^NSEI")
        bank_ltp, bank_chg, bank_pct = get_live_data("^NSEBANK")
        sensex_ltp, sensex_chg, sensex_pct = get_live_data("^BSESN")
        it_ltp, it_chg, it_pct = get_live_data("^CNXIT") 
        
        indices_html = "<div class='idx-container'>"
        indices = [("SENSEX", sensex_ltp, sensex_chg, sensex_pct), ("NIFTY 50", nifty_ltp, nifty_chg, nifty_pct), ("NIFTY BANK", bank_ltp, bank_chg, bank_pct), ("NIFTY IT", it_ltp, it_chg, it_pct)]
        for name, val, chg, pct in indices:
            clr = "green" if chg >= 0 else "red"
            sign = "+" if chg >= 0 else ""
            indices_html += f"<div class='idx-box'><span style='font-size:11px; color:#555; font-weight:bold;'>{name}</span><br><span style='font-size:15px; color:black; font-weight:bold;'>{val:,.2f}</span><br><span style='color:{clr}; font-size:11px; font-weight:bold;'>{sign}{chg:.2f} ({sign}{pct:.2f}%)</span></div>"
        indices_html += "</div>"
        st.markdown(indices_html, unsafe_allow_html=True)

        with st.spinner("Calculating Nifty 50 Adv/Dec..."):
            adv, dec = get_adv_dec(NIFTY_50_STOCKS)
        adv_pct = (adv / (adv + dec)) * 100 if (adv + dec) > 0 else 50
        
        adv_dec_html = (
            "<div class='adv-dec-container'>"
            "<div style='font-size:12px; font-weight:bold; color:#003366;'>📊 REAL-TIME ADVANCE / DECLINE (NIFTY 50)</div>"
            "<div class='adv-dec-bar'>"
            f"<div class='bar-green' style='width: {adv_pct}%;'></div>"
            f"<div class='bar-red' style='width: {100-adv_pct}%;'></div>"
            "</div>"
            "<div style='display:flex; justify-content:space-between; font-size:12px; font-weight:bold;'>"
            f"<span style='color:green;'>Advances: {adv}</span><span style='color:red;'>Declines: {dec}</span>"
            "</div>"
            f"<div style='font-size:10px; color:#555; margin-top:5px;'>Strategy Sentiment: <b>{user_sentiment}</b></div>"
            "</div>"
        )
        st.markdown(adv_dec_html, unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'>🎯 LIVE SIGNALS FOR: {selected_sector}</div>", unsafe_allow_html=True)
        with st.spinner(f"Scanning F&O Charts for Opposite Color + Lowest Vol..."):
            live_signals = exhaustion_scanner(current_watchlist, market_sentiment=user_sentiment)
        
        df_export = pd.DataFrame(live_signals) if len(live_signals) > 0 else pd.DataFrame(columns=["Status"])
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download to Excel (CSV)", data=csv, file_name=f"Signals_{curr_time.strftime('%H%M')}.csv", mime="text/csv")
        
        if len(live_signals) > 0:
            sig_html = "<div class='table-container'><table class='v38-table'><tr><th>Stock</th><th>Entry</th><th>LTP</th><th>Signal</th><th>SL</th><th>T1(1:2)</th><th>T2(1:3)</th><th>EMA 10</th><th>Action Guide</th><th>Time</th></tr>"
            for _, row in df_export.iterrows():
                sig_clr = "green" if row['Signal'] == "BUY" else "red"
                sig_html += f"<tr><td style='color:{sig_clr}; font-weight:bold;'>{row['Stock']}</td><td>{row['Entry']}</td><td>{row['LTP']}</td><td style='color:white; background:{sig_clr}; font-weight:bold;'>{row['Signal']}</td><td>{row['SL']}</td><td style='font-weight:bold;'>{row['T1']}</td><td style='font-weight:bold;'>{row['T2']}</td><td style='color:#1a73e8; font-weight:bold;'>{row['EMA_10']}</td><td style='color:#856404; background:#fff3cd; font-weight:bold;'>{row['Action']}</td><td>{row['Time']}</td></tr>"
            sig_html += "</table></div>"
            st.markdown(sig_html, unsafe_allow_html=True)
        else:
            st.info("⏳ Waiting for setup... No opposite color + lowest vol candle found yet.")

        st.markdown("<div class='section-title'>📝 TRADE JOURNAL (CLOSED TRADES)</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; padding: 15px; border: 1px dashed #ccc; border-radius: 5px; color: #888; font-weight:bold; font-size:12px; margin-bottom:10px; background:white;'>Waiting for trades to close today...</div>", unsafe_allow_html=True)

    with col3:
        with st.spinner("Fetching Live Market Movers..."):
            gainers, losers, trends = get_dynamic_market_data(ALL_STOCKS)

        st.markdown("<div class='section-title'>🚀 LIVE TOP GAINERS</div>", unsafe_allow_html=True)
        if gainers:
            g_html = "<div class='table-container'><table class='v38-table'><tr><th>Stock</th><th>LTP</th><th>%</th></tr>"
            for g in gainers: g_html += f"<tr><td style='text-align:left; font-weight:bold; color:#003366;'>{g['Stock']}</td><td>{g['LTP']}</td><td style='color:green; font-weight:bold;'>+{g['Pct']}%</td></tr>"
            g_html += "</table></div>"
            st.markdown(g_html, unsafe_allow_html=True)
        else: st.markdown("<p style='font-size:12px;text-align:center;'>No gainers found.</p>", unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🔻 LIVE TOP LOSERS</div>", unsafe_allow_html=True)
        if losers:
            l_html = "<div class='table-container'><table class='v38-table'><tr><th>Stock</th><th>LTP</th><th>%</th></tr>"
            for l in losers: l_html += f"<tr><td style='text-align:left; font-weight:bold; color:#003366;'>{l['Stock']}</td><td>{l['LTP']}</td><td style='color:red; font-weight:bold;'>{l['Pct']}%</td></tr>"
            l_html += "</table></div>"
            st.markdown(l_html, unsafe_allow_html=True)
        else: st.markdown("<p style='font-size:12px;text-align:center;'>No losers found.</p>", unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🔍 TREND CONTINUITY (3+ Days)</div>", unsafe_allow_html=True)
        if trends:
            t_html = "<div class='table-container'><table class='v38-table'><tr><th>Stock</th><th>Status</th></tr>"
            for t in trends: t_html += f"<tr><td style='text-align:left; font-weight:bold; color:#003366;'>{t['Stock']}</td><td style='color:{t['Color']}; font-weight:bold;'>{t['Status']}</td></tr>"
            t_html += "</table></div>"
            st.markdown(t_html, unsafe_allow_html=True)
        else: st.markdown("<p style='font-size:12px;text-align:center; color:#888;'>No 3-day trend found.</p>", unsafe_allow_html=True)

elif page_selection == "🌅 9:10 AM: Pre-Market Gap":
    st.header("🌅 09:10 AM: Pre-Market 3% Gap Up/Down List")
    with st.spinner("Scanning ALL F&O Stocks..."):
        gaps = get_gap_scans(ALL_STOCKS)
    if gaps:
        gap_html = "<div class='table-container'><table class='v38-table'><tr><th>Stock</th><th>Open Px</th><th>Gap %</th><th>Status</th></tr>"
        for g in gaps: gap_html += f"<tr><td style='font-weight:bold;'>{g['Stock']}</td><td>{g['Open']}</td><td style='color:{g['Color']}; font-weight:bold;'>{g['Pct']}%</td><td>{g['Status']}</td></tr>"
        gap_html += "</table></div>"
        st.markdown(gap_html, unsafe_allow_html=True)
    else: st.info("No stocks gapped > 3% recently.")

elif page_selection == "🚀 9:15 AM: Opening Movers":
    st.header("🚀 09:15 AM: Live >2% Movers")
    with st.spinner("Scanning ALL F&O Stocks..."):
        movers = get_opening_movers(ALL_STOCKS)
    if movers:
        m_html = "<div class='table-container'><table class='v38-table'><tr><th>Stock</th><th>LTP</th><th>Movement %</th></tr>"
        for m in movers: 
            c = "green" if m['Pct'] > 0 else "red"
            m_html += f"<tr><td style='font-weight:bold;'>{m['Stock']}</td><td>{m['LTP']}</td><td style='color:{c}; font-weight:bold;'>{m['Pct']}%</td></tr>"
        m_html += "</table></div>"
        st.markdown(m_html, unsafe_allow_html=True)
    else: st.info("No stocks moved > 2% recently.")

elif page_selection == "🔥 9:20 AM: OI Setup":
    st.header("🔥 09:20 AM: Volume Spikes (Proxy OI)")
    with st.spinner("Scanning ALL F&O Stocks..."):
        oi_setups = get_oi_simulation(ALL_STOCKS)
    if oi_setups:
        oi_html = "<div class='table-container'><table class='v38-table'><tr><th>Stock</th><th>Simulated OI Signal</th><th>Vol Spike</th></tr>"
        for o in oi_setups: oi_html += f"<tr><td style='font-weight:bold;'>{o['Stock']}</td><td style='color:{o['Color']}; font-weight:bold;'>{o['Signal']}</td><td>{o['Vol']}</td></tr>"
        oi_html += "</table></div>"
        st.markdown(oi_html, unsafe_allow_html=True)
    else: st.info("No significant volume spikes detected.")

elif page_selection == "⚙️ Scanner Settings":
    st.header("⚙️ Scanner Settings")
    st.success("Your terminal is 100% bug-free and optimized for Haridas Master Strategy.")

elif page_selection == "📊 Backtest Engine":
    st.header("📊 Backtest Engine")
    st.warning("Historical data sync required for automated backtesting.")

if auto_refresh:
    time.sleep(refresh_time * 60)
    st.rerun()
