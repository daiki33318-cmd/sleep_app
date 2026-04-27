import streamlit as st
import datetime
import pandas as pd
import os
import google.generativeai as genai

# 保存ファイル名
CSV_FILE = "sleep_data.csv"

# --- AI相談機能 ---
def get_ai_advice(data_summary, api_key):
    try:
        genai.configure(api_key=api_key)
        
        # 1. あなたの環境で今使えるモデル（AI）をリストアップする
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 2. 優先順位をつけて最適なものを選ぶ
        # まずは flash 1.5、なければ pro、それもなければリストの先頭を使う
        selected_model = ""
        if "models/gemini-1.5-flash" in models:
            selected_model = "models/gemini-1.5-flash"
        elif "models/gemini-pro" in models:
            selected_model = "models/gemini-pro"
        else:
            selected_model = models[0] if models else ""

        if not selected_model:
            return "利用可能なAIモデルが見つかりませんでした。"

        # 3. 選ばれたモデルで実行
        model = genai.GenerativeModel(selected_model)
        prompt = f"睡眠コンサルタントとして、以下のデータから改善点を150文字で教えて。\n{data_summary}"
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"エラーが発生しました: {e}\n(しばらく時間をおいてから再試行してください)"
        
# --- 画面構成 ---
st.set_page_config(page_title="睡眠AIサポーター", layout="wide")
st.title("🌙 睡眠改善AIサポーター")

# --- サイドバー（ここでAPIキーを入れる） ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini API Keyを入力", type="password")

# --- 入力エリア ---
st.subheader("　🛌 睡眠記録を入力")
c1, c2, c3 = st.columns(3)
with c1: today = st.date_input("日付", datetime.date.today())
with c2: bed_time = st.time_input("就寝時間", datetime.time(23, 0))
with c3: wake_time = st.time_input("起床時間", datetime.time(7, 0))

if st.button("記録を保存する"):
    start = datetime.datetime.combine(today, bed_time)
    end = datetime.datetime.combine(today, wake_time)
    if end <= start: end += datetime.timedelta(days=1)
    duration = (end - start).seconds / 3600
    
    new_data = pd.DataFrame([[today, bed_time, wake_time, duration]], 
                            columns=["日付", "就寝時間", "起床時間", "睡眠時間"])
    if not os.path.isfile(CSV_FILE):
        new_data.to_csv(CSV_FILE, index=False)
    else:
        new_data.to_csv(CSV_FILE, mode='a', header=False, index=False)
    st.success(f"保存完了！ 睡眠時間: {duration:.1f}時間")

st.divider()

# --- グラフと分析 ---
if os.path.isfile(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    st.subheader("📊 睡眠分析")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        if st.button("AIアドバイスをもらう"):
            if api_key:
                with st.spinner("AIが考え中..."):
                    advice = get_ai_advice(df.tail(7).to_string(), api_key)
                    st.info(advice)
            else:
                st.warning("左側のサイドバーにAPIキーを入力してください！")
    with col_b:
        st.line_chart(df.set_index("日付")["睡眠時間"])
    st.dataframe(df)