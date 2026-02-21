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

# --- ৩. দ্য মাস্টার স্ক্যানার ইঞ্জিন (EMA 10 ইন্টিগ্রেটেড) ---
@st.cache_data(ttl=60)
def exhaustion_scanner(stock_list, market_sentiment="BULLISH"):
    signals = []
    for stock_symbol in stock_list:
        try:
            stock = yf.Ticker(stock_symbol)
            # EMA 10 ক্যালকুলেশনের জন্য ২ দিনের ডেটা লাগবে
            df = stock.history(period="2d", interval="5m")
            
            if df.empty or len(df) < 15:
                continue
            
            # EMA 10 ক্যালকুলেশন
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            
            # আজকের ডেটা আলাদা করা
            today_date = df.index[-1].date()
            df_today = df[df.index.date == today_date].copy()
            
            if len(df_today) < 5:
                continue
            
            completed_idx = len(df_today) - 2
            completed_candle = df_today.iloc[-2]
            
            if completed_idx < 3:
                continue
                
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
                t1 = entry + (risk * 2) if signal == "BUY" else entry - (risk * 2)
                t2 = entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                pivot = round((completed_candle['High'] + completed_candle['Low'] + completed_candle['Close']) / 3, 2)
                
                signals.append({
                    "Stock": stock_symbol, "Entry": round(entry, 2), "LTP": round(completed_candle['Close'], 2),
                    "Signal": signal, "SL": round(sl, 2), "T1(1:2)": round(t1, 2), "T2": round(t2, 2),
                    "EMA10": round(completed_candle['EMA10'], 2), # EMA ভ্যালু অ্যাড হলো
                    "Pivot": pivot, "Time": completed_candle.name.strftime('%H:%M:%S')
                })
        except:
            continue
    return signals

# --- ৪. আপডেট করা রেসপনসিভ CSS (Mobile Auto-Rotate Fix) ---
st.markdown("""
    <style>
    /* ১. স্ট্রিমলিট ক্লাউডের হেডার যাতে মোবাইল স্ক্রিন না ঢাকে তার জন্য প্যাডিং ফিক্স */
    header { visibility: hidden !important; }
    .main .block-container { 
        padding-top: 5rem !important; 
        padding-bottom: 0rem !important; 
    }
    
    .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; }
    
    /* ২. টপ বার ডিজাইন - মোবাইলে কাত (Rotate) করলে নিজে থেকে সাজিয়ে নেবে */
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
    .nav-clock { color: #ffeb3b; font-size: 15px; font-weight: bold; }

    /* ৩. মোবাইল রেসপনসিভ লজিক */
    @media (max-width: 768px) {
        .top-nav { flex-direction: column; gap: 10px; text-align: center; }
        .nav-title { font-size: 16px; }
        .main .block-container { padding-top: 6rem !important; }
        .v38-table { font-size: 10px; } /* মোব
