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

# --- ৩. দ্য মাস্টার স্ক্যানার ইঞ্জিন (EMA 10 ও লজিক সহ) ---
@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            stock = yf.Ticker(stock_symbol)
            # EMA 10 এর সঠিক হিসেবের জন্য ৫ দিনের ডেটা নিচ্ছি
            df = stock.history(period="5d", interval="5m")
            if df.empty or len(df) < 15: continue
            
            # EMA 10 ক্যালকুলেশন
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            
            # আজকের ডেটা আলাদা করা
            today_date = df.index[-1].date()
            df_today = df[df.index.date == today_date].copy()
            
            if len(df_today) < 5: continue
            
            completed_idx = len(df_today) - 2
            completed_candle = df_today.iloc[-2]
            
            if completed_idx < 3: continue # প্রথম ১৫ মিনিট ইগনোর
                
            df_upto_completed = df_today.iloc[:completed_idx+1]
            min_vol_so_far = df_upto_completed['Volume'].min()
            is_lowest_vol = (completed_candle['Volume'] <= min_vol_so_far)
            
            is_green = completed_candle['Close'] > completed_candle['Open']
            is_red = completed_candle['Close'] < completed_candle['Open']
            
            signal = None
            entry = sl = 0.0
            
            # ট্রেন খালি হওয়ার লজিক (Train Emptying out)
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
                t1 = entry + (risk * 2) if signal == "BUY" else entry - (risk * 2)
                t2 = entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                
                signals.append({
                    "Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(completed_candle['Close'], 2),
                    "Signal": signal, "SL": round(sl, 2), "T1(1:2)": round(t1, 2), "T2(1:3)": round(t2, 2),
                    "EMA10": round(completed_candle['EMA10'], 2), "Time": completed_candle.name.strftime('%H:%M:%S')
                })
        except: continue
    return signals

# --- ৪. রেসপনসিভ CSS (Mobile Auto-Rotate & Cloud Fix) ---
st.markdown("""
    <style>
    /* স্ট্রিমলিট ক্লাউডের হেডার যাতে ঢাকা না পড়ে তার জন্য প্যাডিং ফিক্স */
    header { visibility: hidden !important; }
    .main .block-container { 
        padding-top: 5rem !important; 
        padding-bottom: 0rem !important; 
    }
    .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; }
    
    /* টপ বার ডিজাইন (Auto-Rotate Ready) */
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

    /* মোবাইল অটো-রোটেট ফিক্স */
    @media (max-width: 768px) {
        .top-nav { flex-direction: column; gap: 10px; text-align: center; }
        .nav-title { font-size: 16px; }
        .main .block-container { padding-top: 6rem !important; }
    }
    
    .v38-table-container { overflow-x: auto; width: 100%; border-radius: 8px; }
    .v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; background: white; border: 1px solid #b0c4de; }
    .v38-table th { background-color: #4f81bd; color: white; padding: 12px; border: 1px solid #b0c4de; white-space: nowrap; }
    .v38-table td { padding: 10px; border: 1px solid #b0c4de; white-space: nowrap; }
    
    .idx-container { display: flex; flex-wrap: wrap; justify-content: space-around; gap: 10px; margin-bottom: 10px; }
    .idx-box { background: white; border: 1px solid #b0c4de; padding: 12px; min-width: 140px; text-align: center; border-radius: 8px; flex-grow: 1; }
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
    st.success("✅ Strategy: BULLISH")
    st.info("EMA 10 Trailing: Active")

# --- ৬. টপ নেভিগেশন ---
curr_time = datetime.datetime.now()
session_label = "LIVE MARKET" if 9 <= curr_time.hour < 15 else "POST MARKET"
session_color = "#28a745" if session_label == "LIVE MARKET" else "#dc3545"

st.markdown(f"""
    <div class="top-nav">
        <div class="nav-title">🚀 HARIDAS MASTER TERMINAL v38.0</div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <span style="background: {session_color}; color: white; padding: 5px 12px; border-radius: 6px; font-size: 11px; font-weight: bold;">
                {session_label}
            </span>
            <div class="nav-clock">🕒 {curr_time.strftime('%H:%M:%S')}</div>
        </div>
    </div>
    <div style="background: #fff3cd; color: #856404; padding: 10px 15px; font-size: 12px; font-weight: bold; border-radius: 6px; margin-bottom: 20px; border: 1px solid #ffeeba;">
        <marquee scrollamount="5">🔥 <b>SYSTEM READY:</b> Real-time 5m Exhaustion Scanner | 🎯 EMA 10 Strategy Integrated | 📱 Mobile Auto-Rotate Active.</marquee>
    </div>
""", unsafe_allow_html=True)

# কলাম তৈরি
col1, col2, col3 = st.columns([1, 2.8, 1])

# --- LEFT COLUMN (SECTOR) ---
with col1:
    st.markdown('<div class="section-title" style="color:#003366; font-weight:bold;">📊 SECTOR TREND</div>', unsafe_allow_html=True)
    sectors = [("NIFTY METAL", "+1.57%"), ("NIFTY ENERGY", "+1.20%"), ("NIFTY IT", "-0.81%")]
    for n, v in sectors:
        clr = "green" if "+" in v else "red"
        st.write(f"**{n}**: :{clr}[{v}]")

# --- MIDDLE COLUMN (MAIN DATA) ---
with col2:
    n_ltp, n_chg, n_pct = get_live_data("^NSEI")
    b_ltp, b_chg, b_pct = get_live_data("^NSEBANK")
    
    st.markdown(f"""
        <div class="idx-container">
            <div class="idx-box"><b>NIFTY 50</b><br><span style="font-size:16px; font-weight:bold
