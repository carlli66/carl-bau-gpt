import streamlit as st
import google.generativeai as genai
from PIL import Image
import extra_streamlit_components as stx
import time

# ==========================================
# 1. 核心配置 & 页面初始化
# ==========================================
PREMIUM_CODE = "BAU2026"  
STRIPE_LINK = "https://buy.stripe.com/6oUbJ1dR4bfQfsj0EodMI02" 

st.set_page_config(
    page_title="DE-BauKI Experte", 
    page_icon="🏗️", 
    layout="centered"
)

# ==========================================
# 2. Cookie 管理器初始化 (这是记住次数的关键)
# ==========================================
# 初始化 Cookie 管理器
cookie_manager = stx.CookieManager()

# --- 核心逻辑：同步 Cookie 和 Session State ---
# 读取浏览器里存的 'bauki_usage' (使用次数)
cookie_usage = cookie_manager.get(cookie="bauki_usage")

# 初始化 session_state
if "msg_count" not in st.session_state:
    if cookie_usage is None:
        st.session_state.msg_count = 0
    else:
        st.session_state.msg_count = int(cookie_usage)

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False 
if "messages" not in st.session_state:
    st.session_state.messages = [] 

# 如果 Cookie 里的次数比当前 session 的大，说明用户刷新了页面，强制同步
if cookie_usage is not None and int(cookie_usage) > st.session_state.msg_count:
    st.session_state.msg_count = int(cookie_usage)

# ==========================================
# 3. 侧边栏 (控制面板)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=60)
    st.markdown("### ⚙️ Einstellungen")

    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key", type="password")

    st.markdown("---")

    # 会员状态逻辑
    if st.session_state.is_premium:
        st.success("🌟 **Premium: AKTIV**")
        st.caption("✅ Modell: **Gemini 2.5 Pro**")
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.is_premium = False
            st.rerun()
    else:
        # 免费次数显示
        left = 3 - st.session_state.msg_count
        if left < 0: left = 0
        
        st.markdown("### 📊 Ihr Kontingent")
        if left > 0:
            st.info(f"Kostenlose Fragen: **{left} / 3**")
            st.progress((3 - left) / 3)
            st.caption("Verlauf wird im Browser gespeichert.")
        else:
            st.error("Limit erreicht (0/3)")
            
            st.markdown("#### 🔓 Upgrade auf PRO")
            st.markdown("- **Unbegrenzte** Fragen\n- **Gemini 2.5 Pro**\n- **Bild-Upload**")
            st.link_button("👉 Jetzt freischalten (4,99€)", STRIPE_LINK)

        st.markdown("---")
        
        # 密码输入框
        with st.expander("🎫 Code einlösen", expanded=True):
            user_code = st.text_input("Zugangscode:", placeholder="Code...", type="password")
            if st.button("Prüfen"):
                if user_code == PREMIUM_CODE:
                    st.session_state.is_premium = True
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Ungültig.")

# ==========================================
# 4. AI 智能核心
# ==========================================
def get_ai_response(api_key, prompt, image=None):
    genai.configure(api_key=api_key)
    model_priority = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    
    last_error = None
    for model_name in model_priority:
        try:
            model = genai.GenerativeModel(model_name)
            content = [prompt]
            if image: content.append(image)
            response = model.generate_content(content)
            return response.text
        except Exception as e:
            last_error = e
            continue 
    raise last_error

# ==========================================
# 5. 主界面
# ==========================================
st.title("🏗️ DE-BauKI")
st.subheader("Ihr Immobilien-, Bau- und Finanzierungsexperte")
st.caption("Powered by Google Gemini 2.5 Pro | Spezialisiert auf deutsche Standards")

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1: st.markdown("""<div style="background-color:#f0f2f6; padding:10px; border-radius:10px; text-align:center;">⚖️ <b>Baurecht</b></div>""", unsafe_allow_html=True)
with col2: st.markdown("""<div style="background-color:#f0f2f6; padding:10px; border-radius:10px; text-align:center;">🔨 <b>Technik</b></div>""", unsafe_allow_html=True)
with col3: st.markdown("""<div style="background-color:#f0f2f6; padding:10px; border-radius:10px; text-align:center;">💶 <b>Kosten</b></div>""", unsafe_allow_html=True)

st.divider()

# 显示历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 6. 交互与扣费逻辑 (带 Cookie 更新)
# ==========================================
if api_key:
    can_ask = st.session_state.is_premium or (st.session_state.msg_count < 3)

    if can_ask:
        uploaded_file = st.file_uploader("📎 Dokumente/Bilder analysieren", type=["jpg", "png", "jpeg", "pdf"])

        if prompt := st.chat_input("Ihre Frage stellen..."):
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file: st.image(uploaded_file, width=300)

            with st.chat_message("assistant"):
                with st.spinner("Bau-KI analysiert (Gemini 2.5 Pro)..."):
                    try:
                        img_obj = Image.open(uploaded_file) if uploaded_file else None
                        
                        sys_prompt = """
                        Du bist 'DE-BauKI', ein Experte für Immobilien, Baurecht (LBO), DIN-Normen und Finanzierung.
                        Regeln:
                        1. Antworte professionell auf Deutsch.
                        2. Nenne bei Kosten realistische Spannen.
                        3. Disclaimer am Ende: "⚠️ Hinweis: KI-Ersteinschätzung. Keine Rechtsberatung."
                        """
                        full_prompt = sys_prompt + "\n\nUser Frage: " + prompt

                        ans_text = get_ai_response(api_key, full_prompt, img_obj)
                        
                        st.markdown(ans_text)
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})

                        # ★★★ 关键修改：更新 Cookie ★★★
                        if not st.session_state.is_premium:
                            # 1. 增加次数
                            new_count = st.session_state.msg_count + 1
                            st.session_state.msg_count = new_count
                            
                            # 2. 写入浏览器 Cookie (有效期 30 天)
                            cookie_manager.set("bauki_usage", new_count, key="set_usage")
                            
                            # 3. 强制刷新，确保侧边栏数字变动
                            time.sleep(0.5) # 给 Cookie 写入一点时间
                            st.rerun()

                    except Exception as e:
                        st.error(f"Fehler: {e}")
    else:
        st.warning("🔒 **Limit erreicht.**")
        st.markdown("Bitte Premium freischalten.")
else:
    st.info("Bitte API Key eingeben.")

# ==========================================
# 7. 底部
# ==========================================
st.divider()
st.warning("⚖️ **Haftungsausschluss:** Keine Rechts- oder Finanzberatung.")
with st.expander("Impressum & Kontakt"):
    st.write("Kontakt: hello@xxxxxxx.net | Betreiber: M.Sc. Architekt [Name]")
