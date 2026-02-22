import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import time

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(layout="wide", page_title="Haridas Pro Master Terminal v38.1", initial_sidebar_state="expanded")

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

# --- ৩. দ্য মাস্টার স্ক্যানার ইঞ্জিন (EMA 10 আপডেটেড) ---
@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            stock = yf.Ticker(stock_symbol)
            df = stock.history(period="2d", interval="5m")
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
                    pivot = round((completed_candle['High'] + completed_candle['Low'] + completed_candle['Close']) / 3, 2)
                    
                    signals.append({
                        "Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(completed_candle['Close'], 2),
                        "Signal": signal, "SL": round(sl, 2), "T1(1:2)": round(t1, 2), "T2": round(t2, 2),
                        "EMA 10": round(completed_candle['EMA10'], 2),
                        "Pivot": pivot, "Time": completed_candle.name.strftime('%H:%M:%S')
                    })
        except: continue
    return signals

# --- ৪. কাস্টম CSS (Visuals + Mobile Fix) ---
st.markdown("""
    <style>
    header { visibility: hidden !important; }
    .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; }
    .block-container { padding: 3.5rem 1rem 1rem 1rem !important; }
    
    .top-nav { background-color: #002b36; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #00ffd0; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.2); }
    
    @media (max-width: 768px) {
        .top-nav { flex-direction: column; text-align: center; gap: 8px; }
        .block-container { padding-top: 5.5rem !important; }
        .idx-box { width: 48% !important; margin-bottom: 8px; }
    }
    
    .section-title { color: #003366; font-size: 13px; font-weight: bold; padding: 4px 5px; text-transform: uppercase; margin-top: 5px; border-bottom: 2px solid #b0c4de; margin-bottom: 10px; }
    
    .table-container { overflow-x: auto; width: 100%; border-radius: 5px; }
    .v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; color: black; background: white; border: 1px solid #b0c4de; margin-bottom: 10px; white-space: nowrap; }
    .v38-table th { background-color: #4f81bd; color: white; padding: 8px; border: 1px solid #b0c4de; font-weight: bold; }
    .v38-table td { padding: 8px; border: 1px solid #b0c4de; }
    
    .idx-container { display: flex; justify-content: space-between; background: white; border: 1px solid #b0c4de; padding: 5px; margin-bottom: 10px; flex-wrap: wrap; border-radius: 5px; }
    .idx-box { text-align: center; width: 23%; border-right: 1px solid #eee; padding: 5px; min-width: 100px; }
    .idx-box:last-child { border-right: none; }
    
    .adv-dec-container { background: white; border: 1px solid #b0c4de; padding: 10px; margin-bottom: 10px; text-align: center; border-radius: 5px; }
    .adv-dec-bar { display: flex; height: 14px; border-radius: 4px; overflow: hidden; margin: 8px 0; }
    .bar-green { background-color: #2e7d32; }
    .bar-red { background-color: #d32f2f; }
    .bar-bg { background: #e0e0e0; width: 100%; height: 14px; min-width: 50px; border-radius: 3px; }
    .bar-fg-green { background: #276a44; height: 100%; border-radius: 3px; }
    .bar-fg-red { background: #8b0000; height: 100%; border-radius: 3px; }
    .ticker { background: #fff3cd; color: #856404; padding: 6px 15px; font-size: 13px; font-weight: bold; border-bottom: 1px solid #ffeeba; border-radius: 5px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- ৫. সাইডবার (Full Dashboard Control) ---
with st.sidebar:
    st.markdown("### 🎛️ MAIN MENU")
    page_selection = st.radio("Navigate to:", ["📈 Live Terminal", "⚙️ Scanner Settings", "📊 Backtest Engine"])
    st.divider()
    
    # 🚨 কাস্টম অটো-রিফ্রেশ ইঞ্জিন
    st.markdown("### ⏱️ SYSTEM CONTROLS")
    if st.button("🔄 Force Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    auto_refresh = st.checkbox("Enable Auto-Refresh", value=False)
    refresh_time = st.selectbox("Refresh Interval:", [1, 3, 5, 10], index=0, format_func=lambda x: f"{x} Minutes")
    st.divider()
    
    # 🚨 ডায়নামিক মার্কেট সেন্টিমেন্ট
    st.markdown("### 💡 STRATEGY SETTINGS")
    user_sentiment = st.selectbox("Market Sentiment (Scanner):", ["BULLISH", "BEARISH"])
    st.info("EMA 10 Trailing: Enabled")

# --- ৬. টপ নেভিগেশন ---
curr_time = datetime.datetime.now()
session = "LIVE MARKET" if 9 <= curr_time.hour < 15 else "POST MARKET"

st.markdown(f"""
    <div class="top-nav">
        <div style="color:#00ffd0; font-weight:bold; font-size:18px;">HARIDAS NSE TERMINAL</div>
        <div style="font-size: 14px; color: #ffeb3b; font-weight: bold; display: flex; align-items: center;">
            <span style="background: #ffeb3b; color: black; padding: 2px 8px; border-radius: 4px; margin-right: 10px;">{session}</span> 
            🕒 {curr_time.strftime('%H:%M:%S')}
        </div>
        <div>
            <span style="background:#1a73e8; padding:5px 15px; font-size:11px; color:white; font-weight:bold; border-radius:4px;">SCAN MARKET</span>
        </div>
    </div>
    <div class="ticker">
        <marquee direction="left" scrollamount="5">
            🔥 <b>SYSTEM READY:</b> Real-time 5m Exhaustion Scanner | 🎯 Trend: {user_sentiment} | 📱 Custom Refresh & Excel Export Ready.
        </marquee>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 🚨 PAGE ROUTING LOGIC (ড্যাশবোর্ড চেঞ্জার)
# ==========================================

if page_selection == "📈 Live Terminal":
    col1, col2, col3 = st.columns([1, 2.8, 1])

    # --- LEFT COLUMN ---
    with col1:
        st.markdown('<div class="section-title">📊 SECTOR PERFORMANCE</div>', unsafe_allow_html=True)
        sectors = [("NIFTY METAL", "+1.57%", 95), ("NIFTY ENERGY", "+1.20%", 80), ("NIFTY FMCG", "+0.72%", 70), ("NIFTY FIN SRV", "+0.70%", 65), ("NIFTY BANK", "+0.58%", 50), ("NIFTY IT", "-0.81%", 75)]
        sec_html = '<div class="table-container"><table class="v38-table"><tr><th>Sector</th><th>%</th><th style="width:40%;">Trend</th></tr>'
        for n, v, bw in sectors:
            c, bc = ("green", "bar-fg-green") if "+" in v else ("red", "bar-fg-red")
            sec_html += f'<tr><td style="text-align:left; font-weight:bold; color:#003366;">{n}</td><td style="color:{c}; font-weight:bold;">{v}</td><td style="padding:4px 8px;"><div class="bar-bg"><div class="{bc}" style="width:{bw}%;"></div></div></td></tr>'
        sec_html += '</table></div>'
        st.markdown(sec_html, unsafe_allow_html=True)

    # --- MIDDLE COLUMN ---
    with col2:
        st.markdown('<div class="section-title">📉 MARKET INDICES (LIVE)</div>', unsafe_allow_html=True)
        nifty_ltp, nifty_chg, nifty_pct = get_live_data("^NSEI")
        bank_ltp, bank_chg, bank_pct = get_live_data("^NSEBANK")
        
        st.markdown(f"""
            <div class="idx-container">
                <div class="idx-box"><b>NIFTY 50</b><br><span style="font-size:15px; color:black; font-weight:bold;">{nifty_ltp}</span><br><span style="color:{"green" if nifty_chg >= 0 else "red"}; font-size:11px; font-weight:bold;">{nifty_chg} ({nifty_pct}%)</span></div>
                <div class="idx-box"><b>NIFTY BANK</b><br><span style="font-size:15px; color:black; font-weight:bold;">{bank_ltp}</span><br><span style="color:{"green" if bank_chg >= 0 else "red"}; font-size:11px; font-weight:bold;">{bank_chg} ({bank_pct}%)</span></div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="section-title">🎯 TRADING SIGNALS (Trend: {user_sentiment} + EMA 10)</div>', unsafe_allow_html=True)
        
        fo_watchlist = ["HINDALCO.NS", "NTPC.NS", "WIPRO.NS", "RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS"]
        
        with st.spinner('Scanning Live F&O Charts (5m)...'):
            live_signals = exhaustion_scanner(fo_watchlist, market_sentiment=user_sentiment)
        
        if len(live_signals) > 0:
            df_signals = pd.DataFrame(live_signals)
            
            sig_html = '<div class="table-container"><table class="v38-table"><tr><th>Stock</th><th>Entry</th><th>LTP</th><th>Signal</th><th>SL</th><th>T1(1:2)</th><th>T2</th><th>EMA 10</th><th>Pivot</th><th>Time</th></tr>'
            for _, row in df_signals.iterrows():
                sig_clr = "green" if row["Signal"] == "BUY" else "red"
                sig_html += f'<tr><td style="color:{sig_clr}; font-weight:bold;">{row["Stock"]}</td><td>{row["Entry"]}</td><td>{row["LTP"]}</td><td style="color:white; background:{sig_clr}; font-weight:bold;">{row["Signal"]}</td><td>{row["SL"]}</td><td>{row["T1(1:2)"]}</td><td>{row["T2"]}</td><td style="font-weight:bold; color:#003366;">{row["EMA 10"]}</td><td>{row["Pivot"]}</td><td>{row["Time"]}</td></tr>'
            sig_html += '</table></div>'
            st.markdown(sig_html, unsafe_allow_html=True)
            
            # 🚨 আসল EXCEL EXPORT বাটন
            csv = df_signals.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Export Signals to Excel (CSV)", data=csv, file_name=f"Haridas_Signals_{curr_time.strftime('%H%M')}.csv", mime="text/csv")
        else:
            st.info("⏳ Waiting for setup... No stocks currently match the condition.")

    # --- RIGHT COLUMN ---
    with col3:
        st.markdown('<div class="section-title">🚀 TOP GAINERS</div>', unsafe_allow_html=True)
        st.markdown("""<div class="table-container"><table class="v38-table"><tr><th>Stock</th><th>LTP</th><th>%</th></tr><tr><td style="text-align:left; color:#003366; font-weight:bold;">HINDALCO.NS</td><td>935.70</td><td style="color:green; font-weight:bold;">+3.32%</td></tr></table></div>""", unsafe_allow_html=True)

elif page_selection == "⚙️ Scanner Settings":
    st.header("⚙️ Scanner Customization")
    st.info("এখানে তুই স্ক্যানারের লজিক নিজের মতো সাজাতে পারবি (Development in progress).")
    st.slider("Select EMA Period", min_value=5, max_value=50, value=10)
    st.selectbox("Risk to Reward Target 1", ["1:1", "1:1.5", "1:2", "1:3"], index=2)

elif page_selection == "📊 Backtest Engine":
    st.header("📊 Backtesting Dashboard")
    st.warning("Backtest Engine is currently offline. Historical data sync required.")

# 🚨 কাস্টম অটো-রিফ্রেশ লজিক
if auto_refresh:
    time.sleep(refresh_time * 60)
    st.rerun()
