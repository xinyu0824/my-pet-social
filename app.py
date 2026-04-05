import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import datetime
import pandas as pd  # <--- 就是這一行！一定要有

# --- 基礎設定 ---
st.set_page_config(page_title="我的專屬小世界", page_icon="🌐", layout="wide")

# --- 1. 連接 Google Sheets (永久記憶庫) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    pet_df = conn.read(ttl=0)
    # 確保如果讀到的是空的，也要有欄位名
    if pet_df is None or pet_df.empty:
        pet_df = pd.DataFrame(columns=["name", "bio", "avatar_url"])
except Exception as e:
    # 這是發生錯誤時的預防措施
    pet_df = pd.DataFrame(columns=["name", "bio", "avatar_url"])

# --- 2. AI 串接 (Secrets 讀取) ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("請確認 Streamlit Secrets 已設定 GEMINI_API_KEY")
    st.stop()

# --- 3. 側邊欄：管理中心 ---
with st.sidebar:
    st.title("⚙️ 設定中心")
    
    group_type = st.text_input("定義這個空間性質 (例如：學校、診所)", value="小世界")
    
    tab_post, tab_manage = st.tabs(["📸 分享紀錄", "➕ 成員管理"])
    
    with tab_manage:
        st.subheader(f"✨ 註冊{group_type}成員")
        new_name = st.text_input("成員姓名")
        new_bio = st.text_area("性格與人設描述")
        new_avatar = st.text_input("頭貼網址 (選填)")
        
        if st.button(f"確認加入{group_type}"):
            if new_name and new_bio:
                new_entry = pd.DataFrame([{"name": new_name, "bio": new_bio, "avatar_url": new_avatar}])
                # 更新資料並寫入 Sheets
                updated_df = pd.concat([pet_df, new_entry], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"成員 {new_name} 已加入！")
                st.rerun()

    with tab_post:
        st.subheader("發布動態")
        if pet_df.empty:
            st.warning("目前沒有成員")
            selected_pets = []
        else:
            selected_pets = st.multiselect("哪些成員參與？", pet_df["name"].tolist())
            
        uploaded_image = st.file_uploader("上傳照片", type=['png', 'jpg', 'jpeg'])
        content = st.text_area("此刻的心情...")
        btn_publish = st.button("確認發布")

# --- 4. 主畫面 ---
st.title(f"✨ 我們的{group_type}動態牆")

if btn_publish and uploaded_image and selected_pets:
    st.divider()
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.image(uploaded_image, use_container_width=True)
    with col2:
        st.subheader(f"📍 {group_type}動態")
        st.write(content)
        for pet in selected_pets:
            # 獲取性格描述
            p_info = pet_df[pet_df["name"] == pet].iloc[0]
            with st.chat_message("assistant", avatar=p_info["avatar_url"] if p_info["avatar_url"] else None):
                st.write(f"**{pet} 的回應：**")
                prompt = f"場景：{group_type}。你是{pet}，性格：{p_info['bio']}。主人發文：{content}。請簡短回覆。"
                response = model.generate_content(prompt)
                st.write(response.text)
else:
    st.info("請在左側操作")
