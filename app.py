import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. 核心配置
# ==========================================
PREMIUM_CODE = "BAU2026"  # 解锁密码
STRIPE_LINK = "https://buy.stripe.com/你的链接" # Stripe 链接

# ==========================================
# 2. 页面配置
# ==========================================
st.set_page_config(page_title="DE-BauKI Expert", page_icon="🏗️", layout="centered")

# 初始化状态
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0 
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False 
if "messages" not in st.session_state:
    st.session_state.messages = [] 

# ==========================================
# 3. 侧边栏
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### Mein Status")

    # 获取 API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key", type="password")

    st.markdown("---")

    # 会员状态逻辑
    if st.session_state.is_premium:
        st.success("👑 **Premium Aktiv**")
        st.caption("Modell: Gemini 1.5 Pro")
        if st.button("Logout"):
            st.session_state.is_premium = False
            st.rerun()
    else:
        left = 3 - st.session_state.msg_count
        if left < 0: left = 0
        
        if left > 0:
            st.info(f"Kostenlose Fragen: {left} / 3")
            st.progress((3 - left) / 3)
        else:
            st.error("Limit erreicht (0/3)")
            st.markdown("#### 🔓 Vollzugriff erhalten:")
            st.markdown("Nutzen Sie das **Pro-Modell** unbegrenzt für 7 Tage.")
            st.link_button("👉 Jetzt freischalten (4,99€)", STRIPE_LINK)
            st.caption("Code erhalten Sie nach der Zahlung.")

        st.markdown("---")
        
        # 密码输入框
        with st.expander("🎫 Code eingeben", expanded=True):
            user_code = st.text_input("Zugangscode:", placeholder="Code hier eingeben...", type="password")
            if st.button("Prüfen"):
                if user_code == PREMIUM_CODE:
                    st.session_state.is_premium = True
                    st.balloons()
                    st.success("Code akzeptiert!")
                    st.rerun()
                else:
                    st.error("Falscher Code.")

# ==========================================
# 4. 主界面
# ==========================================
st.title("🏗️ DE-BauKI Expert")
st.markdown("Ihr KI-Architekt für Baurecht, Sanierung & Kosten.")

col1, col2, col3 = st.columns(3)
with col1: st.markdown('<div style="text-align:center">⚖️<br><small>Baurecht</small></div>', unsafe_allow_html=True)
with col2: st.markdown('<div style="text-align:center">🔨<br><small>Technik</small></div>', unsafe_allow_html=True)
with col3: st.markdown('<div style="text-align:center">💶<br><small>Kosten</small></div>', unsafe_allow_html=True)

st.divider()

# ==========================================
# 5. 聊天历史回显
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 6. AI 核心逻辑 (智能容错版)
# ==========================================
if api_key:
    genai.configure(api_key=api_key)
    
    # 定义一个函数，专门用来尝试生成回答
    # 如果 Pro 模型失败，自动用 Flash 模型重试
    def smart_generate(model_name, prompt_parts):
        try:
            model = genai.GenerativeModel(model_name)
            return model.generate_content(prompt_parts)
        except Exception as e:
            # 如果是 404 错误（找不到模型），抛出异常让外面捕获
            raise e

    # 判断权限
    can_ask = st.session_state.is_premium or (st.session_state.msg_count < 3)

    if can_ask:
        with st.expander("📎 Datei / Bild hochladen (Optional)"):
            uploaded_file = st.file_uploader("Bild/PDF", type=["jpg", "png", "jpeg", "pdf"])

        if prompt := st.chat_input("Frage stellen (z.B. Ist eine Baugenehmigung nötig?)..."):
            
            # 1. 记录用户提问
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file:
                    st.image(uploaded_file, width=200)

            # 2. 生成回答
            with st.chat_message("assistant"):
                with st.spinner("Bau-KI denkt nach..."):
                    
                    # 准备 Prompt
                    sys_prompt = """
                    Du bist ein erfahrener deutscher Architekt und Bauingenieur.
                    Aufgaben: Baurecht (LBO), Kosten, DIN-Normen.
                    Antworte präzise auf Deutsch.
                    Disclaimer: "Hinweis: KI-Ersteinschätzung. Keine Rechtsberatung."
                    """
                    full_prompt = sys_prompt + "\n\nUser Frage: " + prompt
                    
                    # 准备发送给 AI 的内容列表
                    content_parts = [full_prompt]
                    if uploaded_file:
                        img = Image.open(uploaded_file)
                        content_parts.append(img)

                    # --- 核心修改：双保险机制 ---
                    response_text = ""
                    try:
                        # 第一步：尝试用最强的 1.5 Pro
                        response = smart_generate("gemini-1.5-pro", content_parts)
                        response_text = response.text
                    except Exception:
                        try:
                            # 第二步：如果 Pro 挂了，尝试用 1.5 Flash (最稳)
                            # st.caption("⚠️ Pro-Modell ausgelastet, nutze Flash-Modell...") 
                            response = smart_generate("gemini-1.5-flash", content_parts)
                            response_text = response.text
                        except Exception as e2:
                             st.error(f"Verbindungsfehler: {e2}")
                             st.stop()
                    
                    # 显示回答
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                    # 3. 扣费逻辑
                    if not st.session_state.is_premium:
                        st.session_state.msg_count += 1
                        st.rerun()
    else:
        st.warning("🔒 **Limit erreicht.** Bitte Code eingeben.")
        st.caption("Den Code 'BAU2026' finden Sie auf der Zahlungsbestätigung.")

else:
    st.warning("Bitte Google API Key in der Sidebar eingeben.")

# 底部信息
st.divider()
with st.expander("Impressum & Kontakt"):
    st.write("Kontakt: support@bau-ki.de | Betreiber: M.Sc. Architekt [Dein Name]")
