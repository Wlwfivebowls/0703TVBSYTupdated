
import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(layout="wide")
st.title("📊 YouTube 直播頻道在線人數分析（雲端自動更新）")

# 設定 Google Sheets 權限
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

try:
    sheet = client.open_by_key("1DIz9Cd5iSr1ssNkyYgvBshwKcxfkdraOYilXbXzLXhU").worksheet("工作表1")
    data = sheet.get_all_values()
    df = pd.DataFrame(data)

    # 處理表格
    df.columns = df.iloc[0]
    df = df[1:]

    # 將日期時間欄轉為數值
    df_long = df.melt(id_vars=["頻道名稱"], var_name="時間", value_name="在線人數")
    df_long["在線人數"] = pd.to_numeric(df_long["在線人數"], errors="coerce")
    df_long.dropna(subset=["在線人數"], inplace=True)
    df_long["時間"] = pd.to_datetime(df_long["時間"], errors="coerce")
    df_long.dropna(subset=["時間"], inplace=True)

    channels = df_long["頻道名稱"].unique().tolist()
    selected_channels = st.multiselect("選擇頻道", channels, default=channels)

    df_filtered = df_long[df_long["頻道名稱"].isin(selected_channels)]

    # 繪圖
    st.line_chart(df_filtered.pivot(index="時間", columns="頻道名稱", values="在線人數"))

    # 每日平均 & 加總表格
    df_filtered["日期"] = df_filtered["時間"].dt.date
    daily_stats = df_filtered.groupby(["頻道名稱", "日期"])["在線人數"].agg(["mean", "sum"]).reset_index()
    daily_stats.columns = ["頻道名稱", "日期", "每日平均在線人數", "每日加總在線人數"]

    avg_stats = daily_stats.groupby("頻道名稱")[["每日平均在線人數", "每日加總在線人數"]].mean().reset_index()
    avg_stats = avg_stats.sort_values(by="每日平均在線人數", ascending=False)
    st.subheader("📌 各頻道每日平均與加總（依平均排序）")
    st.dataframe(avg_stats.style.set_properties(**{
        "font-weight": "bold", "color": "black", "background-color": "#FFD700"
    }))

    st.subheader("📅 每日統計數據")
    st.dataframe(daily_stats)

except Exception as e:
    st.error(f"❌ 無法載入或解析資料表，請檢查格式是否正確。

錯誤訊息：{e}")
