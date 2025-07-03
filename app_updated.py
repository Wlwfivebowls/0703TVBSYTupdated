
import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

st.set_page_config(page_title="YouTube 直播頻道儀表板", layout="wide")

st.markdown("## 📊 YouTube 直播頻道在線人數分析（雲端自動更新）")

# Google Sheet 設定
sheet_url = "https://docs.google.com/spreadsheets/d/1DIz9Cd5iSr1ssNkyYgvBshwKcxfkdraOYilXbXzLXhU/edit#gid=0"

@st.cache_data(ttl=600)
def load_data():
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    df = pd.read_csv(csv_url)
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ 無法載入或解析資料表，請檢查格式是否正確。\n錯誤訊息：{e}")
    st.stop()

# 嘗試轉置表格，將頻道為列、時間為欄
try:
    header_row_index = 0
    df_raw.columns = df_raw.iloc[header_row_index]
    df = df_raw.drop(index=range(header_row_index + 1))

    # 只保留頻道名稱與每小時數據
    df = df.reset_index(drop=True)
    df_clean = df.iloc[:, 1:]  # 跳過頻道連結欄位
    df_clean = df_clean.rename(columns={df_clean.columns[0]: "頻道名稱"})
    df_clean = df_clean.set_index("頻道名稱")

    # 將欄位轉為時間序列
    df_clean.columns = pd.to_datetime(df_clean.columns, errors="coerce")
    df_clean = df_clean.dropna(axis=1, how="all")  # 去除無法解析的時間欄

    # 數值轉為 float
    df_clean = df_clean.apply(pd.to_numeric, errors='coerce')

    st.markdown("### ✅ 各頻道每日平均在線人數")
    avg_by_day = df_clean.T.resample("D").mean().T
    avg_by_day["每日平均在線人數"] = avg_by_day.mean(axis=1).round(0).astype(int)
    sorted_df = avg_by_day[["每日平均在線人數"]].sort_values(by="每日平均在線人數", ascending=False)
    st.dataframe(sorted_df.style.set_properties(**{
        "font-weight": "bold",
        "color": "black",
        "background-color": "#FFD700"
    }))
except Exception as e:
    st.error(f"❌ 資料處理時發生錯誤：{e}")
