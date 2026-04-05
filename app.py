import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime

# --- 基礎設定 ---
st.set_page_config(page_title="我的寵物小世界", page_icon="🐾", layout="wide")

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

# --- 1. 連接 Google Sheets (永久記憶庫) ---
# 確保 Sheets 裡有 name, bio, avatar_url 三欄
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    pet_df = conn.read(ttl=0)
except:
    pet_df = pd.DataFrame(columns=["name", "bio", "avatar_url"])

# --- 3. 側邊欄：管理中心 ---
with st.sidebar:
    st.title("⚙️ 設定中心")
    
    # [功能] 自定義空間類型
    group_type = st.text_input("定義這個空間性質 (例如：學校、診所、社團)", value="小世界")
    
    tab_post, tab_manage = st.tabs(["📸 分享紀錄", "➕ 成員管理"])
    
    with tab_manage:
        st.subheader(f"✨ 註冊{group_type}成員")
        new_name = st.text_input("成員姓名 (必填)")
        new_bio = st.text_area("性格與人設描述", placeholder="例如：Alex，統計學教授，說話有邏輯...")
        new_avatar = st.text_input("頭貼圖片網址 (選填)", placeholder="請貼上圖片的 URL 連結")
        
        if st.button(f"確認加入{group_type}"):
            if new_name and new_bio:
                # 存入 Google Sheets
                new_entry = pd.DataFrame([{"name": new_name, "bio": new_bio, "avatar_url": new_avatar}])
                updated_df = pd.concat([pet_df, new_entry], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"成員 {new_name} 已正式加入這個{group_type}！")
                st.rerun()
            else:
                st.warning("請填寫姓名與性格設定喔！")

    with tab_post:
        st.subheader("發布動態")
        if pet_df.empty:
            st.warning("目前還沒有成員，請先去『成員管理』新增吧！")
            selected_pets = []
        else:
            # 這裡只會出現你手動新增的人，不會有皮克敏 1 號 2 號了
            selected_pets = st.multiselect("哪些成員參與了？", pet_df["name"].tolist())
            
        uploaded_image = st.file_uploader("上傳照片", type=['png', 'jpg', 'jpeg'])
        content = st.text_area("寫下此刻的心情...")
        btn_publish = st.button("確認發布")
        
# --- 2. AI 串接 (直接讀取後台 Secrets) ---
try:
    # 這裡會直接抓取你在 Streamlit 設置的 GEMINI_API_KEY
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("偵測不到 API Key，請檢查 Streamlit 後台的 Secrets 設定。")
    st.stop()

# --- 4. 主畫面：時光牆 ---
st.title(f"✨ 我們的{group_type}動態牆")

if btn_publish and uploaded_image and selected_pets:
    st.divider()
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(uploaded_image, use_container_width=True)
        with st.popover("🗑️ 撤回貼文"):
            if st.button("確定從牆上拿下來"):
                st.rerun()

    with col2:
        st.subheader(f"📍 發生在{group_type}的小插曲")
        st.markdown(f"**登場成員：** {' '.join([f'@{p}' for p in selected_pets])}")
        st.write(content)
        
        # --- AI 回覆邏輯 ---
        for pet in selected_pets:
            # 抓取該成員的資料
            row = pet_df[pet_df["name"] == pet].iloc[0]
            p_bio = row["bio"]
            p_avatar = row["avatar_url"] if pd.notna(row["avatar_url"]) and row["avatar_url"] != "" else None
            
            # 顯示對話框
            with st.chat_message("assistant", avatar=p_avatar):
                st.write(f"**{pet} 的回應：**")
                with st.spinner(f"{pet} 正在輸入..."):
                    prompt = f"""
                    場景：現在在一個 '{group_type}'。
                    你扮演成員：'{pet}'。
                    你的性格設定：'{p_bio}'。
                    主人發布了動態：'{content}'。
                    請根據場景與性格給予回覆。
                    """
                    response = model.generate_content(prompt)
                    st.write(response.text)
else:
    if pet_df.empty:
        st.info(f"這個{group_type}目前空蕩蕩的，請先在左側新增成員吧！")
    else:
        st.info(f"選擇成員並上傳照片，讓這面牆熱鬧起來吧！")
