import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="ETF 股息再投入試算", page_icon="⚔️", layout="wide")
st.title("⚔️ ETF 股息再投入：自訂多檔擂台")

# ==========================================
# 側邊欄設定區 (動態產生輸入框)
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

# ==========================================
# 抓取資料的小幫手函式
# ==========================================
def fetch_etf_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return None, 0, 0
        
        price = hist['Close'].iloc[0]
        dividends = ticker.dividends
        
        if not dividends.empty:
            recent_divs = dividends.tail(4)
            total_1y_div = recent_divs.sum()
            annual_yield = total_1y_div / price
        else:
            annual_yield = 0.05
            total_1y_div = 0
            
        return price, annual_yield, total_1y_div
    except:
        return None, 0, 0

# ==========================================
# 抓取並顯示選手資料 (動態分欄)
# ==========================================
st.write("### 📊 選手資料連線中...")

cols = st.columns(num_etfs)
etf_data = {}

for i, t in enumerate(tickers):
    price, yld, div_sum = fetch_etf_data(t)
    etf_data[t] = {'price': price, 'yield': yld}
    
    with cols[i]:
        st.subheader(f"{colors[i]} {t}")
        if price:
            st.metric("最新收盤價", f"{price:.2f} 元")
            st.metric("近四季合計配息", f"{div_sum:.2f} 元", delta=f"真實殖利率: {yld*100:.2f}%")
        else:
            st.error("找不到資料或代號錯誤")

# ==========================================
# 複利試算與圖表大亂鬥
# ==========================================
st.write("---")
all_valid = all(etf_data[t]['price'] is not None for t in tickers)

if all_valid and st.button(f"🔥 開始 {years} 年殘酷試算"):
    data = []
    total_principal = 0
    total_values = {t: 0 for t in tickers} 
    
    for year in range(1, years + 1):
        yearly_invest = monthly_invest * 12
        total_principal += yearly_invest
        
        row_data = {
            "年份": f"第 {year} 年",
            "累積投入本金": int(total_principal)
        }
        
        for t in tickers:
            current_yield = etf_data[t]['yield']
            total_values[t] = (total_values[t] + yearly_invest) * (1 + current_yield)
            row_data[f"{t} 總資產"] = int(total_values[t])
            
        data.append(row_data)
        
    df = pd.DataFrame(data)
    
    st.write(f"### 🎯 每月投入 {monthly_invest:,} 元，{years} 年後結果...")
    
    res_cols = st.columns(num_etfs)
    for i, t in enumerate(tickers):
        with res_cols[i]:
            st.info(f"{colors[i]} **{t}** 預估總資產：\n### {int(total_values[t]):,} 元")
    
    st.write("### 📈 資產成長曲線大 PK")
    chart_columns = ["累積投入本金"] + [f"{t} 總資產" for t in tickers]
    st.line_chart(df.set_index("年份")[chart_columns])
