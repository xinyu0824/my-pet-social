import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
import datetime
from PIL import Image  # 處理照片必備
from io import BytesIO

# --- 基礎設定 ---
st.set_page_config(page_title="我的互動小世界", page_icon="🌐", layout="wide")

# --- 1. 取得 Secrets 資訊 (大約在第 15-25 行之間) ---
try:
    GAS_URL = st.secrets["GAS_URL"]
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 這裡我們換成最穩定的初始化方式
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"初始化失敗，請檢查 Secrets 設定：{e}")
    st.stop()  # 如果這步失敗，就停止執行後面的程式碼
    
    # 嘗試使用最穩定的名稱
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"AI 初始化失敗：{e}")
except:
    st.error("請在 Secrets 設定 GAS_URL 與 GEMINI_API_KEY")
    st.stop()

# [新增] 圖片轉 Base64 的函數
def convert_image_to_base64(uploaded_file):
    if uploaded_file is not None:
        # 讀取圖片並進行編碼
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        # 加上圖片格式標頭，讓瀏覽器認得它
        return f"data:image/png;base64,{base64_str}"
    return None

# 2. 資料存取函數
def get_all_members():
    try:
        response = requests.get(f"{GAS_URL}?t={datetime.datetime.now().timestamp()}")
        return response.json()
    except: return []

def add_member(name, bio, avatar_b64):
    payload = {"name": name, "bio": bio, "avatar_url": avatar_b64}
    try:
        requests.post(GAS_URL, data=json.dumps(payload))
        return True
    except: return False

members = get_all_members()

# --- 側邊欄 ---
with st.sidebar:
    st.title("⚙️ 設定中心")
    group_type = st.text_input("為此空間命名", value="小世界")
    
    tab_post, tab_manage = st.tabs(["📸 分享紀錄", "➕ 成員管理"])
    
    with tab_manage:
        st.subheader(f"✨新增{group_type}成員")
        new_name = st.text_input("成員名稱")
        new_bio = st.text_area("性格描述")
        
        # [功能升級] 使用檔案上傳器來取代網址輸入
        avatar_file = st.file_uploader("上傳成員大頭照", type=['png', 'jpg', 'jpeg'])
        
        if st.button(f"正式加入這個{group_type}"):
            if new_name and new_bio:
                with st.spinner("入住中..."):
                    # 將圖片檔案轉成 Base64 字串
                    avatar_b64 = convert_image_to_base64(avatar_file)
                    if add_member(new_name, new_bio, avatar_b64):
                        st.success(f"{new_name}已成功面試進入{group_type}了！")
                        st.rerun()
            else:
                st.warning("未填寫名稱或性格描述！")

    with tab_post:
        st.subheader("發布紀錄")
        if not members:
            st.warning("目前沒有成員")
            selected = []
        else:
            member_names = [m['name'] for m in members]
            selected = st.multiselect("參與成員", member_names)
            
        img = st.file_uploader("這篇動態的照片", type=['png', 'jpg', 'jpeg'])
        msg = st.text_area("說些什麼...")
        btn_pub = st.button("確認發布")

# --- 主畫面 ---
st.title(f"✨{group_type}")

if btn_pub and img and selected:
    st.divider()
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(img, use_container_width=True)
        with st.popover("🗑️撤回內容"):
            if st.button("確認從牆上拿下來"):
                st.rerun()

    with col2:
        st.subheader(f"📍{group_type}又出什麼事？")
        st.write(msg)
        
# --- 這裡是最關鍵的「防偷跑」邏輯 ---
# 確保所有條件（點按鈕、有圖、有成員）都滿足，AI 才會開口
if btn_pub and img and selected:
    st.divider()
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(img, use_container_width=True)
        # 刪除確認
        with st.popover("🗑️ 撤回內容"):
            st.warning("確定要從牆上拿下來嗎？")
            if st.button("確認撤回"):
                st.rerun()

    with col2:
        st.subheader(f"📍 在 {group_type} 發生的故事")
        st.write(msg if msg else "(主人沒有寫下文字，但照片說明了一切...)")
        st.caption(f"參與成員：{' '.join([f'@{p}' for p in selected])}")
        
        # --- AI 回覆區：現在只有在按了「確認發布」後才會跑這裡 ---
        for p_name in selected:
            # 找到成員資訊
            p_info = next((m for m in members if m['name'] == p_name), None)
            
            if p_info:
                with st.chat_message("assistant", avatar=p_info.get('avatar_url') if p_info.get('avatar_url') else "🐾"):
                    st.write(f"**{p_name} 的回覆：**")
                    with st.spinner(f"喔！{p_name} 秒讀了，打字中..."):
                        try:
                            # 1. 轉換圖片格式 (確保 PIL 已載入)
                            img_pil = Image.open(img)
                            
                            # 2. 重新初始化模型，使用更完整的名稱路徑
                            # 有時候需要加 'models/' 才能解決 404
                            temp_model = genai.GenerativeModel('models/gemini-1.5-flash')
                            
                            # 3. 建立咒語 (Prompt)
                            prompt = f"場景設定：{group_type}。你的身分：{p_name}。性格背景：{p_info['bio']}。主人發文：{msg}。請根據照片與文字，給予讚美或者批判性建議的回覆。"
                            
                            # 4. 呼叫 AI
                            response = temp_model.generate_content([prompt, img_pil])
                            st.write(response.text)
                            
                        except Exception as e:
                            st.error(f"哎呀，{p_name} 年紀大了，看不清圖片，請耐心稍等：{str(e)}")
                            st.info("💡 如果看到404，請確認Secrets裡的API Key是否有效，並嘗試重新整理網頁。")  

else:
    st.info("開啟左側選單，紀錄你們的點點滴滴吧！")
