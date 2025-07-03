
import streamlit as st
import pandas as pd

st.set_page_config(page_title="📊 YouTube 直播頻道在線人數分析", layout="wide")

# 公開 Google Sheet CSV 連結
CSV_URL = "https://docs.google.com/spreadsheets/d/1DIz9Cd5iSr1ssNkyYgvBshwKcxfkdraOYilXbXzLXhU/export?format=csv&gid=0"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL, encoding='utf-8')
    df = df.dropna(how='all')  # 移除空白列
    df.columns = df.iloc[0]    # 第一列為欄位名稱
    df = df[1:]                 # 移除欄位列
    df = df.reset_index(drop=True)
    return df

def parse_data(df):
    # 取出頻道名稱列
    df.columns.values[0:3] = ['頻道連結', '頻道名稱', '影片標題']
    channel_names = df['頻道名稱'].tolist()

    # 將時間欄轉置成長格式
    df_long = pd.melt(df, id_vars=['頻道連結', '頻道名稱', '影片標題'],
                      var_name='時間', value_name='在線人數')
    df_long['在線人數'] = pd.to_numeric(df_long['在線人數'], errors='coerce')
    df_long['時間'] = pd.to_datetime(df_long['時間'], errors='coerce')
    df_long = df_long.dropna(subset=['在線人數', '時間'])

    return df_long

def show_dashboard(df_long):
    st.title("📊 YouTube 直播頻道在線人數分析（雲端自動更新）")

    # 時間篩選器
    min_time = df_long['時間'].min()
    max_time = df_long['時間'].max()
    start_time, end_time = st.slider("選擇分析時間區間：", min_value=min_time, max_value=max_time,
                                     value=(min_time, max_time), step=pd.Timedelta(hours=1))

    filtered = df_long[(df_long['時間'] >= start_time) & (df_long['時間'] <= end_time)]

    if filtered.empty:
        st.warning("❌ 篩選後沒有資料，請調整時間區間")
        return

    # 顯示折線圖
    st.subheader("📈 各頻道在線人數趨勢")
    chart_df = filtered.pivot_table(index='時間', columns='頻道名稱', values='在線人數')
    st.line_chart(chart_df)

    # 統計表
    st.subheader("📋 每日平均在線人數比較表")
    daily_avg = filtered.groupby(['頻道名稱', filtered['時間'].dt.date])['在線人數'].mean().reset_index()
    summary = daily_avg.groupby('頻道名稱')['在線人數'].mean().reset_index(name='每日平均在線人數')
    summary['每日加總人數'] = daily_avg.groupby('頻道名稱')['在線人數'].sum().values
    summary = summary.sort_values(by='每日平均在線人數', ascending=False)

    # 加上總平均一列
    avg_row = pd.DataFrame({
        '頻道名稱': ['總平均'],
        '每日平均在線人數': [summary['每日平均在線人數'].mean()],
        '每日加總人數': [summary['每日加總人數'].mean()]
    })
    summary = pd.concat([avg_row, summary], ignore_index=True)

    styled = summary.style.apply(lambda x: ['font-weight: bold; background-color: #FFD700; color: black'
                                            if x.name == 0 else '' for _ in x], axis=1)
    st.dataframe(styled, use_container_width=True)

# 執行主程式
try:
    df_raw = load_data()
    df_long = parse_data(df_raw)
    show_dashboard(df_long)
except Exception as e:
    st.error(f"❌ 無法載入或解析資料表，請檢查格式是否正確。

錯誤訊息：{e}")
