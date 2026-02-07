import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. 核心配置
# ==========================================
# 通用解锁密码 (请在 Stripe 成功页面上也写这个)
PREMIUM_CODE = "BAU2026" 
# 你的 Stripe 支付链接
STRIPE_LINK = "https://buy.stripe.com/你的链接" 

# ==========================================
# 2. 页面配置
# ==========================================
st.set_page_config(page_title="DE-BauKI Pro", page_icon="🏗️", layout="centered")

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
        st.caption("Modell: Gemini 1.5 Pro (High-End)")
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
st.markdown("Ihr KI-Architekt für Baurecht, Sanierung & Kosten (Powered by Gemini 1.5 Pro).")

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
# 6. AI 核心逻辑 (修复了缩进和模型名称)
# ==========================================
# 这一行必须顶格写，不能有空格！
if api_key:
    genai.configure(api_key=api_key)
    
    # 尝试加载 Pro 模型，如果失败自动切回 Flash
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
    except:
        model = genai.GenerativeModel("gemini-1.5-flash")

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
                with st.spinner("Bau-KI analysiert..."):
                    try:
                        sys_prompt = """
                        Du bist ein erfahrener deutscher Architekt.
                        Aufgaben: Baurecht (LBO), Kosten, DIN-Normen.
                        Antworte präzise auf Deutsch.
                        Disclaimer: "Hinweis: KI-Ersteinschätzung. Keine Rechtsberatung."
                        """
                        full_prompt = sys_prompt + "\n\nUser Frage: " + prompt
                        
                        if uploaded_file:
                            img = Image.open(uploaded_file)
                            response = model.generate_content([full_prompt, img])
                        else:
                            response = model.generate_content(full_prompt)
                        
                        ans = response.text
                        st.markdown(ans)
                        
                        st.session_state.messages.append({"role": "assistant", "content": ans})

                        # 3. 扣费逻辑
                        if not st.session_state.is_premium:
                            st.session_state.msg_count += 1
                            st.rerun()

                    except Exception as e:
                        # 错误处理：如果 Pro 崩了，尝试用 Flash 重试一次
                        try:
                            fallback_model = genai.GenerativeModel("gemini-1.5-flash")
                            response = fallback_model.generate_content(full_prompt)
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except:
                            st.error(f"Ein Fehler ist aufgetreten: {e}")
    else:
        st.warning("🔒 **Limit erreicht.** Bitte Code eingeben.")
        st.caption("Den Code 'BAU2026' finden Sie auf der Zahlungsbestätigung.")

else:
    st.warning("Bitte Google API Key in der Sidebar eingeben.")

# 底部信息
st.divider()
with st.expander("Impressum & Kontakt"):
    st.write("Kontakt: support@bau-ki.de | Betreiber: M.Sc. Architekt [Dein Name]")
