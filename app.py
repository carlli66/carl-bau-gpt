import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. 核心配置 (只需改这里)
# ==========================================
# 你的通用解锁密码 (要和 Stripe 成功页面上写的一样)
PREMIUM_CODE = "BAU2026" 

# 你的 Stripe 支付链接
STRIPE_LINK = "https://buy.stripe.com/你的链接" 

# ==========================================
# 2. 页面基础设置
# ==========================================
st.set_page_config(page_title="DE-BauKI Pro", page_icon="🏗️", layout="centered")

# 初始化状态 (记忆模块)
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0 # 已用次数
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False # 是否解锁
if "messages" not in st.session_state:
    st.session_state.messages = [] # 聊天记录

# ==========================================
# 3. 侧边栏 (状态与解锁)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### Mein Status")

    # 获取 Google API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key", type="password")

    st.markdown("---")

    # --- 核心逻辑：判断会员状态 ---
    if st.session_state.is_premium:
        st.success("👑 **Premium Aktiv**")
        st.caption("Modell: Gemini 1.5 Pro (High-End)")
        if st.button("Logout"):
            st.session_state.is_premium = False
            st.rerun()
    else:
        # 计算剩余次数
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
            st.caption("Sie erhalten den Code direkt nach der Zahlung.")

        st.markdown("---")
        
        # --- 解锁输入框 (密码验证) ---
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
# 4. 主界面内容
# ==========================================
st.title("🏗️ DE-BauKI Expert")
st.markdown("Ihr KI-Architekt für Baurecht, Sanierung & Kosten (Powered by Gemini 1.5 Pro).")

# 三列布局图标
col1, col2, col3 = st.columns(3)
with col1: st.markdown('<div style="text-align:center">⚖️<br><small>Baurecht</small></div>', unsafe_allow_html=True)
with col2: st.markdown('<div style="text-align:center">🔨<br><small>Technik</small></div>', unsafe_allow_html=True)
with col3: st.markdown('<div style="text-align:center">💶<br><small>Kosten</small></div>', unsafe_allow_html=True)

st.divider()

# ==========================================
# 5. 聊天历史回显 (防止对话消失)
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 6. AI 处理逻辑 (已升级为 Pro 模型)
# ==========================================
# 判断是否允许提问
can_ask = st.session_state.is_premium or (st.session_state.msg_count < 3)

# ... 前面的代码 ...
    
if api_key:
        genai.configure(api_key=api_key)
        
        # ★★★ 修改了这一行：加上 -latest ★★★
        try:
            model = genai.GenerativeModel("gemini-1.5-pro-latest") 
        except Exception as e:
            # 如果 Pro 还是报错，自动降级回 Flash 保证 App 不崩溃
            st.warning("⚠️ Pro-Modell nicht verfügbar, wechsle zu Flash...")
            model = genai.GenerativeModel("gemini-1.5-flash")

    # ... 后面的代码 ...

    if can_ask:
        # 文件上传区
        with st.expander("📎 Datei / Bild hochladen (Optional)"):
            uploaded_file = st.file_uploader("Bild/PDF", type=["jpg", "png", "jpeg", "pdf"])

        # 输入框
        if prompt := st.chat_input("Frage stellen (z.B. Ist eine Baugenehmigung nötig?)..."):
            
            # 1. 显示并保存用户问题
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file:
                    st.image(uploaded_file, width=200)

            # 2. 调用 AI
            with st.chat_message("assistant"):
                with st.spinner("Bau-KI analysiert (Pro-Modell)..."):
                    try:
                        # 设定专家人设
                        sys_prompt = """
                        Du bist ein erfahrener deutscher Architekt und Bauingenieur.
                        Deine Aufgaben:
                        1. Analysiere Fragen zu Baurecht (LBO), Sanierungskosten und DIN-Normen.
                        2. Antworte präzise, professionell und hilfreich auf Deutsch.
                        3. Wenn Bilder hochgeladen werden, analysiere bauliche Details.
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
                        
                        # 保存回答
                        st.session_state.messages.append({"role": "assistant", "content": ans})

                        # 3. 扣费逻辑 (如果是免费用户)
                        if not st.session_state.is_premium:
                            st.session_state.msg_count += 1
                            st.rerun() # 强制刷新更新计数器

                    except Exception as e:
                        st.error(f"Ein Fehler ist aufgetreten: {e}")
    else:
        st.warning("🔒 **Limit erreicht.** Bitte geben Sie den Code ein.")
        st.caption("Code vergessen? Schauen Sie auf der Stripe-Bestätigungsseite nach.")

else:
    st.warning("Bitte Google API Key in der Sidebar eingeben.")

# 底部 Impressum
st.divider()
with st.expander("Impressum & Kontakt"):
    st.write("Kontakt: support@bau-ki.de | Betreiber: M.Sc. Architekt [Dein Name]")
