import streamlit as st
import datetime
import yfinance as yf
import pandas as pd
import time

# --- ১. পেজ কনফিগারেশন ---
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

# --- ৩. দ্য মাস্টার স্ক্যানার (EMA 10 ইন্টিগ্রেটেড) ---
@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            stock = yf.Ticker(stock_symbol)
            # EMA 10 এর জন্য ২ দিনের ৫-মিনিট ডেটা নেওয়া হচ্ছে
            df = stock.history(period="2d", interval="5m")
            if df.empty or len(df) < 15: continue
            
            # EMA 10 ক্যালকুলেশন
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            
            today_date = df.index[-1].date()
            df_today = df[df.index.date == today_date].copy()
            if len(df_today) < 5: continue
            
            comp_idx = len(df_today) - 2
            comp_candle = df_today.iloc[comp_idx]
            
            # রুল ১: ৯:৩০ পর্যন্ত ইগনোর [cite: 2026-02-06]
            if comp_idx < 3: continue
                
            min_vol_so_far = df_today.iloc[:comp_idx + 1]['Volume'].min()
            is_lowest_vol = (comp_candle['Volume'] <= min_vol_so_far)
            
            is_green = comp_candle['Close'] > comp_candle['Open']
            is_red = comp_candle['Close'] < comp_candle['Open']
            
            signal = None
            entry = sl = 0.0
            
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
                    "Signal": signal, "SL": round(sl, 2), "T1": round(t1, 2), "T2": round(t2, 2),
                    "EMA10": round(comp_candle['EMA10'], 2), "Time": comp_candle.name.strftime('%H:%M')
                })
        except: continue
    return signals

# --- ৪. রেসপনসিভ CSS (Mobile & Cloud Fix) ---
st.markdown("""
    <style>
    header { visibility: hidden !important; }
    .main .block-container { padding-top: 5rem !important; }
    .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; }
    
    .top-nav { 
        background-color: #002b36; 
        padding: 15px 25px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-bottom: 4px solid #00ffd0; 
        border-radius: 12px;
        box-shadow: 0px 8px 15px rgba(0,0,0,0.3);
    }
    
    /* মোবাইল অটো-রোটেট ফিক্স */
    @media (max-width: 768px) {
        .top-nav { flex-direction: column; gap: 10px; text-align: center; }
        .main .block-container { padding-top: 6rem !important; }
    }
    
    .v38-table-container { overflow-x: auto; width: 100%; }
    .v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; background: white; border: 1px solid #b0c4de; }
    .v38-table th { background-color: #4f81bd; color: white; padding: 12px; border: 1px solid #b0c4de; white-space: nowrap; }
    .v38-table td { padding: 10px; border: 1px solid #b0c4de; white-space: nowrap; }
    </style>
    """, unsafe_allow_html=True)

# --- ৫. UI রেন্ডারিং ---
# (তোর বাকি UI কোড আগের মতোই আছে ভাই)
st.markdown(f'<div class="top-nav"><div style="color:#00ffd0; font-size:20px; font-weight:bold;">🚀 HARIDAS MASTER TERMINAL v38.0</div><div style="color:#ffeb3b; font-weight:bold;">🕒 {datetime.datetime.now().strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)

# কলাম তৈরি
col1, col2, col3 = st.columns([1, 2.8, 1])

# মধ্যম কলামে সিগন্যাল দেখানো
with col2:
    fo_list = ["HINDALCO.NS", "NTPC.NS", "WIPRO.NS", "RELIANCE.NS", "SBIN.NS", "TCS.NS"]
    signals = exhaustion_scanner(fo_list)
    if signals:
        st.dataframe(pd.DataFrame(signals), use_container_width=True)
    else:
        st.info("⏳ কন্ডিশন ম্যাচ করলে এখানে অটোমেটিক সিগন্যাল আসবে।")
