import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime

# --- 基礎設定 ---
st.set_page_config(page_title="我的寵物小世界", page_icon="🐾")

# 簡單的隱私鎖 (密碼可以自己改)
PASSWORD = "My_pet" 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("請輸入密碼進入小世界：", type="password")
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

# --- AI 設定 (這裡預留給你填 API Key) ---
# 提示：你可以去 Google AI Studio 免費申請
API_KEY = st.sidebar.text_input("輸入你的 Gemini API Key", type="password")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 22 隻寵物清單 (你可以隨時修改名字) ---
PET_LIST = [f"皮克敏 {i+1} 號" for i in range(22)] 

st.title("📸 寵物家族時光牆")
st.caption("這裡只有我們，還有滿滿的愛。")

# --- 發文區 ---
with st.sidebar:
    st.header("✨ 分享新動態")
    selected_pet = st.selectbox("今天是哪位寶貝的故事？", PET_LIST)
    uploaded_image = st.file_uploader("上傳可愛瞬間", type=['png', 'jpg', 'jpeg'])
    content = st.text_area("寫下你想說的話...")
    
    if st.button("發布貼文"):
        if uploaded_image and content:
            st.toast("貼文發布成功！(這僅為模擬展示)")
            # 觸發 AI 回覆
            if API_KEY:
                with st.spinner(f'{selected_pet} 正在組織語言...'):
                    prompt = f"你現在是主人養的寵物 '{selected_pet}'。主人剛發了一篇貼文：'{content}'。請用非常可愛、療癒、且符合你身為寵物的口吻回覆主人。這是一篇私密紀錄，只有你跟主人看得到。"
                    response = model.generate_content(prompt)
                    st.session_state.last_reply = response.text
            else:
                st.warning("請先輸入 API Key 才能讓寵物回覆你喔！")

# --- 貼文牆展示區 ---
st.divider()
if uploaded_image:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(uploaded_image, use_container_width=True)
    with col2:
        st.subheader(f"🐾 {selected_pet} 的日常")
        st.write(content)
        st.caption(f"發布時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # 顯示 AI 回覆
        if "last_reply" in st.session_state:
            with st.chat_message("assistant", avatar="✨"):
                st.write(f"**{selected_pet} 回覆了你：**")
                st.write(st.session_state.last_reply)
else:
    st.info("左側上傳第一張照片，開啟你的專屬時光吧！")
