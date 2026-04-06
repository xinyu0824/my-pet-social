import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
import datetime
from io import BytesIO
from PIL import Image

# --- 基礎設定 ---
st.set_page_config(page_title="我的互動小世界", page_icon="🌐", layout="wide")

# 1. 取得 Secrets
try:
    GAS_URL = st.secrets["GAS_URL"]
# --- 尋找這段 AI 初始化代碼 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
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
        
# --- 找到 AI 回覆的那段 loop ---
for p_name in selected:
    p_info = next(m for m in members if m['name'] == p_name)
    with st.chat_message("assistant", avatar=p_info.get('avatar_url') if p_info.get('avatar_url') else "🐾"):
        st.write(f"**{p_name} 的回覆：**")
        with st.spinner(喔！f"{p_name} 秒讀了，打字中..."):
            try:
                img_pil = Image.open(img)
                prompt = f"場景：{group_type}。你是{p_name}，性格：{p_info['bio']}。主人發文：{msg}。請根據照片內容與文字，，給予讚美或者批判性建議的回覆。"
                
                # [升級處] 強制要求回覆，避免因為 API 版本問題卡住
                response = model.generate_content(
                    [prompt, img_pil],
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        max_output_tokens=500,
                        temperature=0.7,
                    )
                )
                st.write(response.text)
            except Exception as e:
                # 如果還是 404，這裡會顯示更詳細的提示
                st.error(f"哎呀，{p_name} 遇到了年紀大了，看不清圖片，請稍等一下：{str(e)}")
                st.info("提示：如果持續出現404，可能是API Key需要重新領取或稍微等待 Google 伺服器更新。")

else:
    st.info("開啟左側選單，紀錄你們的點點滴滴吧！")
