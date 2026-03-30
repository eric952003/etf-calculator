import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px  # 這次新增的超強畫圖套件！

st.set_page_config(page_title="ETF 股息再投入試算", page_icon="📈")
st.title("📈 ETF 股息再投入試算機 (全自動版)")

st.sidebar.header("1. 選擇台股標的")
ticker_input = st.sidebar.text_input("輸入 ETF 股票代號", value="00878.TW")

st.sidebar.header("2. 設定投資參數")
monthly_invest = st.sidebar.number_input("每月固定投入金額 (元)", min_value=1000, value=10000, step=1000)
years = st.sidebar.slider("預計投資年限", min_value=1, max_value=30, value=10)

st.write(f"正在抓取 **{ticker_input}** 的最新股價與配息資料...")

try:
    ticker = yf.Ticker(ticker_input)
    hist = ticker.history(period="1d")
    
    if not hist.empty:
        current_price = hist['Close'].iloc[0]
        dividends = ticker.dividends
        
        st.success("✅ 成功取得即時股價與配息紀錄！")
        
        col1, col2 = st.columns(2)
        col1.metric(label="最新收盤價", value=f"{current_price:.2f} 元")
        
        if not dividends.empty:
            recent_dividends = dividends.tail(4) 
            total_dividend_1y = recent_dividends.sum()
            real_yield = (total_dividend_1y / current_price) * 100
            annual_yield = real_yield / 100
            
            col2.metric(label="近四季合計配息", value=f"{total_dividend_1y:.2f} 元", delta=f"真實殖利率: {real_yield:.2f}%")
            
            st.write("### 💰 最近配息紀錄")
            recent_dividends.index = recent_dividends.index.strftime('%Y-%m-%d')
            st.dataframe(recent_dividends.rename("每股配息金額 (元)"), use_container_width=True)
            
        else:
            st.warning("⚠️ 找不到近期的配息紀錄，將使用預設殖利率 5% 試算。")
            annual_yield = 0.05
            
        st.write("---")
        if st.button(f"使用真實殖利率 ({annual_yield*100:.2f}%) 開始試算複利"):
            data = []
            total_shares_value = 0
            total_principal = 0
            
            for year in range(1, years + 1):
                yearly_invest = monthly_invest * 12
                total_principal += yearly_invest
                total_shares_value = (total_shares_value + yearly_invest) * (1 + annual_yield)
                
                data.append({
                    "第幾年": f"第 {year} 年",
                    "累積投入本金": int(total_principal),
                    "含息總資產": int(total_shares_value),
                })
            
            df = pd.DataFrame(data)
            
            st.write(f"### 🎯 如果你每個月投入 {monthly_invest:,} 元...")
            estimated_shares = int(total_shares_value / (current_price * 1000))
            
            res_col1, res_col2 = st.columns(2)
            res_col1.metric("預估總資產", f"{int(total_shares_value):,} 元")
            res_col2.metric("約等於現在股價的", f"{estimated_shares} 張")
            
            # 原本的折線圖
            st.line_chart(df.set_index("第幾年")[["累積投入本金", "含息總資產"]])
            
            # --- 以下是這次新增的圓餅圖區塊 ---
            st.write("### 🥧 最終資產組成比例")
            total_profit = total_shares_value - total_principal # 算出生出來的總獲利
            
            # 整理給圓餅圖的資料
            pie_data = pd.DataFrame({
                "分類": ["累積投入本金", "股息滾入獲利"],
                "金額": [total_principal, total_profit]
            })
            
            # 使用 Plotly 畫出精美的圓餅圖
            fig = px.pie(pie_data, values="金額", names="分類", 
                         color_discrete_sequence=["#1f77b4", "#ff7f0e"], # 設定藍橘配色
                         hole=0.4) # 中間挖空變成甜甜圈圖，看起來更專業
            
            # 顯示在網頁上
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("⚠️ 找不到該檔股票，請確認代號是否正確。")
except Exception as e:
    st.error(f"連線失敗，請稍後再試。錯誤訊息: {e}")
