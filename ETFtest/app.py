import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="ETF 股息再投入試算", page_icon="⚔️", layout="wide")
st.title("⚔️ ETF 股息再投入：真實扣血擂台版")

# ==========================================
# 側邊欄設定區
# ==========================================
st.sidebar.header("1. 選擇比較檔數與標的")
num_etfs = st.sidebar.radio("你想同時試算幾檔 ETF？", [1, 2, 3], horizontal=True)

default_tickers = ["00878.TW", "00679B.TW", "0050.TW"]
colors = ["🔴", "🔵", "🟢"]
tickers = []

for i in range(num_etfs):
    t = st.sidebar.text_input(f"{colors[i]} 選手 {chr(65+i)}", value=default_tickers[i])
    tickers.append(t)

st.sidebar.header("2. 設定投資參數")
monthly_invest = st.sidebar.number_input("每月固定投入金額 (元)", min_value=1000, value=10000, step=1000)
years = st.sidebar.slider("預計投資年限", min_value=1, max_value=30, value=10)

st.sidebar.header("3. 真實環境設定")
freq_options = {"月配息 (一年 12 次)": 12, "季配息 (一年 4 次)": 4, "半年配 (一年 2 次)": 2, "年配息 (一年 1 次)": 1}
freq_choice = st.sidebar.selectbox("這些 ETF 的配息頻率是？", list(freq_options.keys()), index=1)
dividend_frequency = freq_options[freq_choice]

# ==========================================
# 抓取資料小幫手 (加強偵錯版)
# ==========================================
def fetch_etf_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1d")
        
        # 偵錯點 1：檢查是不是被 Yahoo 擋住了 (回傳空表)
        if hist.empty:
            st.warning(f"⚠️ {ticker_symbol} 抓不到股價：Yahoo Finance 回傳空資料，可能是雲端 IP 被擋了！")
            return None, 0.0, 0.0
        
        price = float(hist['Close'].iloc[0])
        
        # 偵錯點 2：把股息抓取獨立出來，避免因為股息抓不到而整個壞掉
        try:
            dividends = ticker.dividends
            if not dividends.empty:
                recent_divs = dividends.tail(4)
                total_1y_div = float(recent_divs.sum())
                annual_yield = float(total_1y_div / price)
            else:
                # 假設找不到配息資料，給個預設值 5%
                annual_yield = 0.05
                total_1y_div = 0.0
        except Exception as e_div:
            st.warning(f"⚠️ {ticker_symbol} 抓得到股價，但股息發生異常：{e_div}")
            annual_yield = 0.05
            total_1y_div = 0.0
            
        return price, annual_yield, total_1y_div
        
    except Exception as e:
        # 偵錯點 3：顯示最底層的真實錯誤
        st.error(f"🚨 {ticker_symbol} 系統錯誤：{e}")
        return None, 0.0, 0.0

# ==========================================
# 顯示選手資料
# ==========================================
st.write("### 📊 選手資料連線中...")
cols = st.columns(num_etfs)
etf_data = {}

for i, t in enumerate(tickers):
    price, yld, div_sum = fetch_etf_data(t)
    etf_data[t] = {'price': price, 'yield': yld}
    
    with cols[i]:
        st.subheader(f"{colors[i]} {t}")
        if price is not None:
            st.metric("最新收盤價", f"{price:.2f} 元")
            st.metric("近四季合計配息", f"{div_sum:.2f} 元", delta=f"理論殖利率: {yld*100:.2f}%")
        else:
            st.error("找不到資料或代號錯誤")

# ==========================================
# 真實扣血試算邏輯
# ==========================================
st.write("---")
# 檢查是否所有 ETF 都有抓到價格
all_valid = all(etf_data[t]['price'] is not None for t in tickers)

if all_valid and st.button(f"🔥 開始 {years} 年真實殘酷試算"):
    data = []
    total_principal = 0
    total_values = {t: 0 for t in tickers} 
    blood_loss = {t: 0 for t in tickers} # 用來紀錄被國家和銀行扣掉多少錢
    
    for year in range(1, years + 1):
        yearly_invest = monthly_invest * 12
        total_principal += yearly_invest
        
        row_data = {"年份": f"第 {year} 年", "累積投入本金": int(total_principal)}
        
        for t in tickers:
            current_yield = etf_data[t]['yield']
            base_capital = total_values[t] + yearly_invest 
            annual_raw_dividend = base_capital * current_yield 
            single_dividend = annual_raw_dividend / dividend_frequency 
            
            annual_net_dividend = 0
            
            for _ in range(dividend_frequency):
                # 補充健保費門檻計算
                nhi_fee = single_dividend * 0.0211 if single_dividend >= 20000 else 0
                transfer_fee = 10 
                
                net_single = single_dividend - nhi_fee - transfer_fee
                if net_single < 0: net_single = 0 
                
                annual_net_dividend += net_single
                blood_loss[t] += (nhi_fee + transfer_fee) 
            
            total_values[t] = base_capital + annual_net_dividend
            row_data[f"{t} 總資產"] = int(total_values[t])
            
        data.append(row_data)
        
    df = pd.DataFrame(data)
    
    # ==========================================
    # 顯示最終真實結果
    # ==========================================
    st.write(f"### 🎯 每月投入 {monthly_invest:,} 元，{years} 年後結果...")
    
    res_cols = st.columns(num_etfs)
    for i, t in enumerate(tickers):
        with res_cols[i]:
            st.info(f"{colors[i]} **{t}** 預估總資產：\n### {int(total_values[t]):,} 元")
            st.warning(f"🩸 累積扣除健保與匯費：**{int(blood_loss[t]):,}** 元")
    
    st.write("### 📈 真實資產成長曲線大 PK")
    chart_columns = ["累積投入本金"] + [f"{t} 總資產" for t in tickers]
    st.line_chart(df.set_index("年份")[chart_columns])
