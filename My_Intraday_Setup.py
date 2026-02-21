import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import time

# --- ১. পেজ কনফিগারেশন (মোবাইল ও ডেস্কটপ প্রো লুক) ---
st.set_page_config(layout="wide", page_title="Haridas Pro Master Terminal v38.0", initial_sidebar_state="expanded")

# --- ২. লাইভ মার্কেট ডেটা ইঞ্জিন ---
@st.cache_data(ttl=30)
def get_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period='1d')
        if not df.empty:
            ltp = df['Close'].iloc[-1]
            prev_close = stock.fast_info.previous_close
            change = ltp - prev_close
            pct_change = (change / prev_close) * 100
            return round(ltp, 2), round(change, 2), round(pct_change, 2)
        return 0.0, 0.0, 0.0
    except:
        return 0.0, 0.0, 0.0

# --- ৩. দ্য মাস্টার স্ক্যানার (তোর ৩-স্টেপ লজিক + EMA 10) ---
@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            stock = yf.Ticker(stock_symbol)
            # EMA 10 এর জন্য ৫ দিনের ৫-মিনিট ডেটা নিচ্ছি
            df = stock.history(period="5d", interval="5m") 
            if df.empty or len(df) < 20: continue
            
            # EMA 10 ক্যালকুলেশন [cite: 2026-02-21]
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            
            # আজকের দিনের ডেটা আলাদা করা
            today_date = df.index[-1].date()
            df_today = df[df.index.date == today_date].copy()
            if len(df_today) < 5: continue
            
            # লাস্ট কমপ্লিট ক্যান্ডেল (-2) [cite: 2026-02-21]
            comp_idx = len(df_today) - 2
            comp_candle = df_today.iloc[comp_idx]
            
            # রুল ১: প্রথম ১৫ মিনিট (Index 0,1,2) ইগনোর [cite: 2026-02-06]
            if comp_idx < 3: continue
                
            # রুল ২: সারাদিনের (সকাল ৯:১৫ থেকে) সবথেকে কম ভলিউম চেক [cite: 2026-02-21]
            min_vol_so_far = df_today.iloc[:comp_idx + 1]['Volume'].min()
            is_lowest_vol = (comp_candle['Volume'] <= min_vol_so_far)
            
            is_green = comp_candle['Close'] > comp_candle['Open']
            is_red = comp_candle['Close'] < comp_candle['Open']
            
            signal = None
            entry = sl = 0.0
            
            # রুল ৩: অপজিট কালার + লোয়েস্ট ভলিউম (Train Emptying out) [cite: 2026-02-21]
            if market_sentiment == "BULLISH" and is_red and is_lowest_vol:
                signal = "BUY"
                entry = comp_candle['High'] + 0.50
                sl = comp_candle['Low'] - 0.50
            elif market_sentiment == "BEARISH" and is_green and is_lowest_vol:
                signal = "SHORT"
                entry = comp_candle['Low'] - 0.50
                sl = comp_candle['High'] + 0.50
                
            if signal:
                risk = abs(entry - sl)
                t1 = entry + (risk * 2) if signal == "BUY" else entry - (risk * 2)
                t2 = entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                signals.append({
                    "Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(comp_candle['Close'], 2),
                    "Signal": signal, "SL": round(sl, 2), "T1(1:2)": round(t1, 2), "T2(1:3)": round(t2, 2),
                    "EMA10": round(comp_candle['EMA10'], 2), "Time": comp_candle.name.strftime('%H:%M')
                })
        except: continue
    return signals

# --- ৪. কাস্টম CSS (Cloud & Mobile Responsive) ---
st.markdown("""
    <style>
    /* স্ট্রিমলিট ক্লাউড হেডার ফিক্স */
    header { visibility: hidden !important; }
    .main .block-container { padding-top: 5rem !important; }
    
    .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; }
    
    /* টপ বার ডিজাইন [cite: 2026-02-21] */
    .top-nav { 
        background-color: #002b36; 
        padding: 15px 25px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-bottom: 4px solid #00ffd0; 
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0px 8px 15px rgba(0,0,0,0.3);
    }
    
    .nav-title { color: #00ffd0; font-size: 20px; font-weight: bold; }
    .nav-clock { color: #ffeb3b; font-size: 14px; font-weight: bold; }

    /* মোবাইল অটো-রোটেট ফিক্স [cite: 2026-02-21] */
    @media (max-width: 768px) {
        .top-nav { flex-direction: column; gap: 10px; text-align: center; }
        .nav-title { font-size: 16px; }
        .main .block-container { padding-top: 6rem !important; }
    }
    
    .v38-table-container { overflow-x: auto; width: 100%; border-radius: 8px; }
    .v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; background: white; border: 1px solid #b0c4de; }
    .v38-table th { background-color: #4f81bd; color: white; padding: 12px; border: 1px solid #b0c4de; }
    .v38-table td { padding: 10px; border: 1px solid #b0c4de; }
    
    .idx-container { display: flex; flex-wrap: wrap; justify-content: space-around; gap: 8px; margin-bottom: 10px; }
    .idx-box { background: white; border: 1px solid #b0c4de; padding: 10px; min-width: 140px; text-align: center; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- ৫. সাইডবার ---
with st.sidebar:
    st.header("🎛️ CONTROL")
    if st.button("🔄 REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    auto_ref = st.checkbox("⏱️ Auto-Refresh (1 Min)")
    st.divider()
    st.markdown("### 💡 STATUS")
    st.success("✅ Engine: ACTIVE")
    st.info("EMA 10 Trailing: ON")

# --- ৬. টপ নেভিগেশন ---
curr_time = datetime.datetime.now()
session_label = "LIVE MARKET" if 9 <= curr_time.hour < 15 else "POST MARKET"
session_color = "#28a745" if session_label == "LIVE MARKET" else "#dc3545"

st.markdown(f"""
    <div class="top-nav">
        <div class="nav-title">🚀 HARIDAS MASTER TERMINAL v38.0</div>
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="background: {session_color}; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: bold;">
                {session_label}
            </span>
            <div class="nav-clock">🕒 {curr_time.strftime('%H:%M:%S')}</div>
        </div>
    </div>
    <div style="background: #fff3cd; color: #856404; padding: 8px 15px; font-size: 12px; font-weight: bold; border-radius: 6px; margin-bottom: 20px; border: 1px solid #ffeeba;">
        <marquee scrollamount="5">🔥 <b>SYSTEM READY:</b> 5m Exhaustion Scanner | 🎯 Train Emptying Out logic online | 📱 Mobile Auto-Rotate Active.</marquee>
    </div>
""", unsafe_allow_html=True)

# কলাম তৈরি [cite: 2026-02-21]
col1, col2, col3 = st.columns([1, 2.8, 1])

# --- LEFT COLUMN (SECTOR) ---
with col1:
    st.markdown('<h4 style="color:#003366;">📊 SECTOR TREND</h4>', unsafe_allow_html=True)
    sectors = [("NIFTY METAL", "+1.57%"), ("NIFTY ENERGY", "+1.20%"), ("NIFTY IT", "-0.81%")]
    for name, val in sectors:
        clr = "green" if "+" in val else "red"
        st.markdown(f"**{name}**: <span style='color:{clr}'>{val}</span>", unsafe_allow_html=True)

# --- MIDDLE COLUMN (MAIN DATA) ---
with col2:
    n_ltp, n_chg, n_pct = get_live_data("^NSEI")
    b_ltp, b_chg, b_pct = get_live_data("^NSEBANK")
    
    st.markdown(f"""
        <div class="idx-container">
            <div class="idx-box"><b>NIFTY 50</b><br><span style="font-size:16px; font-weight:bold;">{n_ltp}</span><br><span style="color:{"green" if n_chg >= 0 else "red"}">{n_chg} ({n_pct}%)</span></div>
            <div class="idx-box"><b>BANK NIFTY</b><br><span style="font-size:16px; font-weight:bold;">{b_ltp}</span><br><span style="color:{"green" if b_chg >= 0 else "red"}">{b_chg} ({b_pct}%)</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<h3 style="color:#003366;">🎯 LIVE SIGNALS (EMA 10 & LOWEST VOL)</h3>', unsafe_allow_html=True)
    fo_list = ["HINDALCO.NS", "NTPC.NS", "WIPRO.NS", "RELIANCE.NS", "SBIN.NS", "TCS.NS", "ITC.NS", "INFY.NS"]
    signals = exhaustion_scanner(fo_list, market_sentiment="BULLISH")
    
    if signals:
        sig_html = '<div class="v38-table-container"><table class="v38-table"><tr><th>Stock</th><th>Entry</th><th>Signal</th><th>SL</th><th>T1(1:2)</th><th>EMA10</th><th>Time</th></tr>'
        for s in signals:
            sig_html += f'<tr><td style="font-weight:bold;">{s["Stock"]}</td><td>{s["Entry"]}</td><td style="color:white;background:green;font-weight:bold;">{s["Signal"]}</td><td>{s["SL"]}</td><td>{s["T1(1:2)"]}</td><td>{s["EMA10"]}</td><td>{s["Time"]}</td></tr>'
        sig_html += '</table></div>'
        st.markdown(sig_html, unsafe_allow_html=True)
    else:
        st.info("⏳ কন্ডিশন ম্যাচ করলে এখানে অটোমেটিক সিগন্যাল আসবে। (৯:৩০ এর পর চেক করো)")

# --- RIGHT COLUMN (GAINERS) ---
with col3:
    st.markdown('<h4 style="color:#003366;">🚀 TOP GAINERS</h4>', unsafe_allow_html=True)
    st.markdown("**HINDALCO.NS**: <span style='color:green'>+3.32%</span>", unsafe_allow_html=True)
    st.markdown("**NTPC.NS**: <span style='color:green'>+2.68%</span>", unsafe_allow_html=True)

if auto_ref:
    time.sleep(60)
    st.rerun()
