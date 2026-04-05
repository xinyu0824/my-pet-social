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

# --- 1. 連接 Google Sheets (永久記憶) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 讀取現有的成員資料
    pet_df = conn.read(ttl=0) # ttl=0 代表不快取，即時讀取
except:
    # 如果還沒設定好 Sheets，先用一個空的暫時替代
    pet_df = pd.DataFrame(columns=["name", "bio"])

# ---30隻寵物清單 (你可以隨時修改名字) ---
PET_LIST = [f"寵物 {i+1} 號" for i in range(30)] 

st.title("📸 寵物時光牆")
st.caption("這裡只有我們，還有滿滿的愛。")

# --- 2. AI 串接 (直接讀取後台 Secrets) ---
try:
    # 這裡會直接抓取你在 Streamlit 設置的 GEMINI_API_KEY
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("偵測不到 API Key，請檢查 Streamlit 後台的 Secrets 設定。")
    st.stop()

# --- 3. 側邊欄：管理與發布 ---
with st.sidebar:
    st.title("⚙️ 設定中心")
    
    # [新功能] 自定義群組環境
    group_type = st.text_input("定義這個空間 (例如：學校、飲料店)", value="家")
    
    tab_post, tab_manage = st.tabs(["📸 分享動態", "➕ 成員管理"])
    
    with tab_manage:
        st.subheader(f"新增成員到{group_type}")
        new_name = st.text_input("成員姓名")
        new_bio = st.text_area("性格與聲音設定")
        
        if st.button(f"加入這個{group_type}"):
            if new_name and new_bio:
                # 將新成員存入 Google Sheets
                new_data = pd.DataFrame([{"name": new_name, "bio": new_bio}])
                updated_df = pd.concat([pet_df, new_data], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"{new_name} 已正式進入這個{group_type}！")
                st.rerun()

    with tab_post:
        st.subheader("發布紀錄")
        if pet_df.empty:
            st.warning("請先新增成員喔！")
            selected_pets = []
        else:
            selected_pets = st.multiselect("哪些寶貝參與了？", pet_df["name"].tolist())
            
        uploaded_image = st.file_uploader("選擇照片", type=['png', 'jpg', 'jpeg'])
        content = st.text_area("想說的話...")
        btn_publish = st.button("發布")
        
# --- 4. 主畫面：時光牆 ---
st.title(f"✨ 我們的{group_type}動態牆")

if btn_publish and uploaded_image and selected_pets:
    st.divider()
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(uploaded_image, use_container_width=True)
        with st.popover("🗑️ 撤回內容"):
            if st.button("確認從牆上拿下來"):
                st.rerun()

    with col2:
        st.subheader(f"📍 發生在{group_type}的小事")
        st.markdown(f"**參與成員：** {' '.join([f'#{p}' for p in selected_pets])}")
        st.write(content)
        
        # --- AI 回覆邏輯 ---
        for pet in selected_pets:
            # 找到該成員的性格描述
            pet_bio = pet_df[pet_df["name"] == pet]["bio"].values[0]
            
            with st.chat_message("assistant", avatar="💬"):
                st.write(f"**{pet}：**")
                with st.spinner("思考中..."):
                    prompt = f"""
                    場景設定：現在在一個 '{group_type}' 裡面。
                    你現在要扮演：'{pet}'。
                    你的性格設定：'{pet_bio}'。
                    你的主人剛在 '{group_type}' 裡面發了一篇貼文：'{content}'。
                    請根據場景和性格，給予一段回應。
                    """
                    response = model.generate_content(prompt)
                    st.write(response.text)
else:
    st.info(f"歡迎來到你的專屬{group_type}。請從左側開始你的紀錄。")
