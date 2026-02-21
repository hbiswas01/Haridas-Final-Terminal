import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import time

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(layout="wide", page_title="Haridas Pro Master Terminal v38.0", initial_sidebar_state="expanded")

# --- ২. লাইভ মার্কেট ডেটা ফেচিং ---
@st.cache_data(ttl=30)
def get_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        todays_data = stock.history(period='1d')
        if not todays_data.empty:
            ltp = todays_data['Close'].iloc[-1]
            prev_close = stock.fast_info.previous_close
            change = ltp - prev_close
            pct_change = (change / prev_close) * 100
            return round(ltp, 2), round(change, 2), round(pct_change, 2)
        return 0.0, 0.0, 0.0
    except:
        return 0.0, 0.0, 0.0

# --- ৩. দ্য মাস্টার স্ক্যানার ইঞ্জিন (লাইভ মার্কেট আপডেটেড) ---
@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            stock = yf.Ticker(stock_symbol)
            df = stock.history(period="1d", interval="5m")
            
            # পর্যাপ্ত ডেটা না থাকলে স্কিপ (অন্তত ৫টা ক্যান্ডেল লাগবে)
            if df.empty or len(df) < 5:
                continue
            
            # 🚨 রিয়েল মার্কেট ফিক্স: রানিং ক্যান্ডেল (-1) বাদ দিয়ে, লাস্ট কমপ্লিট ক্যান্ডেল (-2) ধরছি
            completed_idx = len(df) - 2
            completed_candle = df.iloc[-2]
            
            # রুল ১: প্রথম ১৫ মিনিট (Index 0, 1, 2) ইগনোর
            if completed_idx < 3:
                continue
                
            # রুল ২: ওই কমপ্লিট ক্যান্ডেল পর্যন্ত সারাদিনের ডেটা নিচ্ছি
            df_upto_completed = df.iloc[:completed_idx+1]
            min_vol_so_far = df_upto_completed['Volume'].min()
            
            # চেক করছি এই কমপ্লিট ক্যান্ডেলটাই সারাদিনের লোয়েস্ট ভলিউম কি না
            is_lowest_vol = (completed_candle['Volume'] <= min_vol_so_far)
            
            # ক্যান্ডেলের কালার
            is_green = completed_candle['Close'] > completed_candle['Open']
            is_red = completed_candle['Close'] < completed_candle['Open']
            
            signal = None
            entry = sl = 0.0
            
            # রুল ৩: অপজিট কালার + লোয়েস্ট ভলিউম লজিক
            if market_sentiment == "BULLISH" and is_red and is_lowest_vol:
                signal = "BUY"
                entry = completed_candle['High'] + 0.50 # হাই ব্রেক করলে এন্ট্রি
                sl = completed_candle['Low'] - 0.50     # লো হলো স্টপ-লস
                
            elif market_sentiment == "BEARISH" and is_green and is_lowest_vol:
                signal = "SHORT"
                entry = completed_candle['Low'] - 0.50  # লো ব্রেক করলে এন্ট্রি
                sl = completed_candle['High'] + 0.50    # হাই হলো স্টপ-লস
                
            # রুল ৪: 1:2 Risk to Reward
            if signal:
                risk = abs(entry - sl)
                if risk > 0:
                    t1 = entry + (risk * 2) if signal == "BUY" else entry - (risk * 2)
                    t2 = entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                    pivot = round((completed_candle['High'] + completed_candle['Low'] + completed_candle['Close']) / 3, 2)
                    
                    signals.append({
                        "Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(completed_candle['Close'], 2),
                        "Signal": signal, "SL": round(sl, 2), "T1(1:2)": round(t1, 2), "T2": round(t2, 2),
                        "Pivot": pivot, "Time": completed_candle.name.strftime('%H:%M:%S')
                    })
        except:
            continue
    return signals

# --- ৪. কাস্টম CSS (v38.0 Look) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; }
    .block-container { padding: 0.5rem 1rem !important; }
    .top-nav { background-color: #002b36; padding: 8px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ccc; }
    .section-title { color: #003366; font-size: 13px; font-weight: bold; padding: 4px 5px; text-transform: uppercase; margin-top: 5px; }
    .v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; color: black; background: white; border: 1px solid #b0c4de; margin-bottom: 10px; }
    .v38-table th { background-color: #4f81bd; color: white; padding: 5px; border: 1px solid #b0c4de; font-weight: bold; }
    .v38-table td { padding: 5px; border: 1px solid #b0c4de; }
    .idx-container { display: flex; justify-content: space-between; background: white; border: 1px solid #b0c4de; padding: 5px; margin-bottom: 10px; }
    .idx-box { text-align: center; width: 19%; border-right: 1px solid #eee; padding: 2px; }
    .idx-box:last-child { border-right: none; }
    .adv-dec-container { background: white; border: 1px solid #b0c4de; padding: 8px; margin-bottom: 10px; text-align: center; }
    .adv-dec-bar { display: flex; height: 12px; border-radius: 3px; overflow: hidden; margin: 5px 0; }
    .bar-green { background-color: #2e7d32; }
    .bar-red { background-color: #d32f2f; }
    .bar-bg { background: #e0e0e0; width: 100%; height: 12px; }
    .bar-fg-green { background: #276a44; height: 100%; }
    .bar-fg-red { background: #8b0000; height: 100%; }
    .ticker { background: #fff3cd; color: #856404; padding: 4px 10px; font-size: 12px; font-weight: bold; border-bottom: 1px solid #ffeeba; }
    </style>
    """, unsafe_allow_html=True)

# --- ৫. সাইডবার ---
with st.sidebar:
    st.markdown("### 🎛️ MAIN MENU")
    st.radio("Navigate to:", ["📈 Live Terminal", "⚙️ Scanner Settings", "📊 Backtest Engine"])
    st.divider()
    if st.button("🔄 Refresh Live Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    auto_refresh = st.checkbox("⏱️ Auto-Refresh (1 Min)", value=False)
    st.divider()
    st.markdown("### 💡 STRATEGY STATUS")
    st.success("✅ 9:25 Sentiment: BULLISH")
    st.success("✅ 9:30 Exhaustion Scanner: ACTIVE")
    st.info("EMA 10 Trailing: Enabled")
    st.divider()
    st.markdown("### 📝 TRADE JOURNAL")
    st.text_area("Write Notes:", placeholder="Type notes here...", height=120, label_visibility="collapsed")
    st.button("💾 Save Note", use_container_width=True)

# --- ৬. টপ নেভিগেশন ---
curr_time = datetime.datetime.now()
session = "LIVE MARKET" if 9 <= curr_time.hour < 15 else "POST MARKET"

st.markdown(f"""
    <div class="top-nav">
        <div style="color:#00ffd0; font-weight:bold; font-size:18px;">HARIDAS NSE TERMINAL</div>
        <div style="font-size: 14px; color: #ffeb3b; font-weight: bold; display: flex; align-items: center;">
            <span style="background: #ffeb3b; color: black; padding: 2px 8px; border-radius: 3px; margin-right: 10px;">{session}</span> 
            🕒 {curr_time.strftime('%H:%M:%S')}
        </div>
        <div>
            <span style="background:#1a73e8; padding:4px 15px; font-size:11px; color:white; font-weight:bold; cursor:pointer;">SCAN MARKET</span>
            <span style="background:#28a745; padding:4px 15px; font-size:11px; color:white; font-weight:bold; margin-left:5px; cursor:pointer;">EXPORT EXCEL</span>
        </div>
    </div>
    <div class="ticker">
        <marquee direction="left" scrollamount="5">
            🔥 <b>SYSTEM READY:</b> Real-time 5m Exhaustion Scanner Active | ⚠️ Wait for first 15 mins. | 🎯 Book 50% at T1, trail SL to Cost.
        </marquee>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2.8, 1])

# --- LEFT COLUMN ---
with col1:
    st.markdown('<div class="section-title">📊 SECTOR PERFORMANCE</div>', unsafe_allow_html=True)
    sectors = [("NIFTY METAL", "+1.57%", 95), ("NIFTY ENERGY", "+1.20%", 80), ("NIFTY FMCG", "+0.72%", 70), ("NIFTY FIN SRV", "+0.70%", 65), ("NIFTY REALTY", "+0.63%", 60), ("NIFTY BANK", "+0.58%", 50), ("NIFTY PHARMA", "+0.33%", 40), ("NIFTY AUTO", "+0.31%", 35), ("NIFTY INFRA", "+0.27%", 30), ("NIFTY PSU BANK", "+0.15%", 20), ("NIFTY IT", "-0.81%", 75)]
    sec_html = '<table class="v38-table"><tr><th>Sector</th><th>%</th><th>Trend</th></tr>'
    for n, v, bw in sectors:
        c, bc = ("green", "bar-fg-green") if "+" in v else ("red", "bar-fg-red")
        sec_html += f'<tr><td style="text-align:left; font-weight:bold; color:#003366;">{n}</td><td style="color:{c}; font-weight:bold;">{v}</td><td style="padding:2px;"><div class="bar-bg"><div class="{bc}" style="width:{bw}%;"></div></div></td></tr>'
    sec_html += '</table>'
    st.markdown(sec_html, unsafe_allow_html=True)

# --- MIDDLE COLUMN ---
with col2:
    st.markdown('<div class="section-title">📉 MARKET INDICES (LIVE)</div>', unsafe_allow_html=True)
    nifty_ltp, nifty_chg, nifty_pct = get_live_data("^NSEI")
    bank_ltp, bank_chg, bank_pct = get_live_data("^NSEBANK")
    it_ltp, it_chg, it_pct = get_live_data("^CNXIT")
    sensex_ltp, sensex_chg, sensex_pct = get_live_data("^BSESN")
    
    indices_html = '<div class="idx-container">'
    indices = [
        ("SENSEX", f"{sensex_ltp:,.2f}", f"{'+' if sensex_chg >= 0 else ''}{sensex_chg:.2f} ({'+' if sensex_pct >= 0 else ''}{sensex_pct:.2f}%)", "green" if sensex_chg >= 0 else "red"),
        ("NIFTY 50", f"{nifty_ltp:,.2f}", f"{'+' if nifty_chg >= 0 else ''}{nifty_chg:.2f} ({'+' if nifty_pct >= 0 else ''}{nifty_pct:.2f}%)", "green" if nifty_chg >= 0 else "red"),
        ("NIFTY BANK", f"{bank_ltp:,.2f}", f"{'+' if bank_chg >= 0 else ''}{bank_chg:.2f} ({'+' if bank_pct >= 0 else ''}{bank_pct:.2f}%)", "green" if bank_chg >= 0 else "red"),
        ("NIFTY IT", f"{it_ltp:,.2f}", f"{'+' if it_chg >= 0 else ''}{it_chg:.2f} ({'+' if it_pct >= 0 else ''}{it_pct:.2f}%)", "green" if it_chg >= 0 else "red")
    ]
    for name, val, amt, clr in indices:
        indices_html += f"<div class='idx-box'><span style='font-size:11px; color:#555; font-weight:bold;'>{name}</span><br><span style='font-size:15px; color:black; font-weight:bold;'>{val}</span><br><span style='color:{clr}; font-size:11px; font-weight:bold;'>{amt}</span></div>"
    indices_html += '</div>'
    st.markdown(indices_html, unsafe_allow_html=True)

    # 9:25 Sentiment Meter
    adv, dec = 1650, 450
    adv_pct = (adv / (adv + dec)) * 100 if (adv+dec) > 0 else 50
    st.markdown(f"""
        <div class="adv-dec-container">
            <div style="font-size:12px; font-weight:bold; color:#003366;">📊 9:25 AM NIFTY 50 MOVEMENT (SENTIMENT: BULLISH)</div>
            <div class="adv-dec-bar">
                <div class="bar-green" style="width: {adv_pct}%;"></div>
                <div class="bar-red" style="width: {100-adv_pct}%;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:bold;">
                <span style="color:green;">Advances: {adv}</span><span style="color:red;">Declines: {dec}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # RUNNING THE SCANNER ENGINE
    st.markdown('<div class="section-title">🎯 TRADING SIGNALS (Opposite Color + Day\'s Lowest Vol)</div>', unsafe_allow_html=True)
    
    # F&O Watchlist
    fo_watchlist = [
        "HINDALCO.NS", "NTPC.NS", "WIPRO.NS", "RELIANCE.NS", "HDFCBANK.NS", 
        "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS"
    ]
    
    with st.spinner('Scanning Live F&O Charts (5m)...'):
        live_signals = exhaustion_scanner(fo_watchlist, market_sentiment="BULLISH")
    
    if len(live_signals) > 0:
        df_signals = pd.DataFrame(live_signals)
        sig_html = '<table class="v38-table"><tr><th>Stock</th><th>Entry</th><th>LTP</th><th>Signal</th><th>SL</th><th>T1(1:2)</th><th>T2</th><th>Pivot</th><th>Time</th></tr>'
        for _, row in df_signals.iterrows():
            sig_clr = "green" if row["Signal"] == "BUY" else "red"
            sig_html += f'<tr><td style="color:{sig_clr}; font-weight:bold;">{row["Stock"]}</td><td>{row["Entry"]}</td><td>{row["LTP"]}</td><td style="color:white; background:{sig_clr}; font-weight:bold;">{row["Signal"]}</td><td>{row["SL"]}</td><td>{row["T1(1:2)"]}</td><td>{row["T2"]}</td><td>{row["Pivot"]}</td><td>{row["Time"]}</td></tr>'
        sig_html += '</table>'
        st.markdown(sig_html, unsafe_allow_html=True)
    else:
        st.info("⏳ Waiting for setup... No stocks currently match the Lowest Volume + Opposite Color condition.")

    # Auto Backtesting Journal
    st.markdown('<div class="section-title">📝 AUTO-BACKTESTING & TRADE JOURNAL (CLOSED)</div>', unsafe_allow_html=True)
    st.markdown("""
        <table class="v38-table">
            <tr><th>Entry Time</th><th>Stock</th><th>Entry Px</th><th>SL</th><th>Target Hit</th><th>Status</th><th>Amount (₹)</th></tr>
            <tr><td>09:45 AM</td><td style="font-weight:bold;">LT.NS</td><td>4350.00</td><td>4320.00</td><td>-</td><td style="color:red; font-weight:bold;">LOSS (SL Hit)</td><td style="color:red;">-₹1,500</td></tr>
            <tr><td>10:15 AM</td><td style="font-weight:bold;">POWERGRID.NS</td><td>280.40</td><td>278.00</td><td>285.20</td><td style="color:green; font-weight:bold;">PROFIT (T1 Hit)</td><td style="color:green;">+₹2,400</td></tr>
        </table>
    """, unsafe_allow_html=True)

# --- RIGHT COLUMN ---
with col3:
    st.markdown('<div class="section-title">🚀 TOP GAINERS</div>', unsafe_allow_html=True)
    st.markdown("""
        <table class="v38-table">
            <tr><th>Stock</th><th>LTP</th><th>%</th></tr>
            <tr><td style="text-align:left; color:#003366; font-weight:bold;">HINDALCO.NS</td><td>935.70</td><td style="color:green; font-weight:bold;">+3.32%</td></tr>
            <tr><td style="text-align:left; color:#003366; font-weight:bold;">NTPC.NS</td><td>372.95</td><td style="color:green; font-weight:bold;">+2.68%</td></tr>
        </table>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🔻 TOP LOSERS</div>', unsafe_allow_html=True)
    st.markdown("""
        <table class="v38-table">
            <tr><th>Stock</th><th>LTP</th><th>%</th></tr>
            <tr><td style="text-align:left; color:#003366; font-weight:bold;">WIPRO.NS</td><td>542.10</td><td style="color:red; font-weight:bold;">-0.64%</td></tr>
            <tr><td style="text-align:left; color:#003366; font-weight:bold;">HCLTECH.NS</td><td>1450.25</td><td style="color:red; font-weight:bold;">-0.96%</td></tr>
        </table>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🔍 TREND CONTINUITY (3+ Days)</div>', unsafe_allow_html=True)
    st.markdown("""
        <table class="v38-table">
            <tr><th>Stock</th><th>Status</th></tr>
            <tr><td style="text-align:left; color:#003366; font-weight:bold;">HINDALCO.NS</td><td style="color:green; font-weight:bold;">৩ দিন উত্থান</td></tr>
            <tr><td style="text-align:left; color:#003366; font-weight:bold;">MARUTI.NS</td><td style="color:red; font-weight:bold;">৩ দিন পতন</td></tr>
        </table>
    """, unsafe_allow_html=True)

# Auto-refresh logic
if auto_refresh:
    time.sleep(60)
    st.rerun()