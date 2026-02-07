import streamlit as st
import google.generativeai as genai
import stripe
from PIL import Image
from datetime import datetime, timedelta

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="DE-BauKI", 
    page_icon="🏗️",
    layout="centered"
)

# --- 2. 初始化 Session State (记忆模块) ---
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0  # 已问次数

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False 

# 【修复点1】初始化聊天记录列表
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. 侧边栏 (Sidebar) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### Mein Status")

    # 配置 Keys
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key", type="password")

    if "STRIPE_API_KEY" in st.secrets:
        stripe.api_key = st.secrets["STRIPE_API_KEY"]
    
    # 获取链接
    link_day = st.secrets.get("LINK_DAY", "#")
    link_week = st.secrets.get("LINK_WEEK", "#")

    st.markdown("---")

    # 会员状态显示逻辑
    if st.session_state.is_premium == "Day":
        st.success("🎫 Tagespass Aktiv")
        st.caption("Gültig für 24 Stunden.")
    elif st.session_state.is_premium == "Week":
        st.success("👑 Wochenpass Aktiv")
        st.caption("7 Tage Premium-Zugriff.")
    else:
        # 免费用户逻辑
        left = 3 - st.session_state.msg_count
        # 防止显示负数
        if left < 0: left = 0
        
        if left > 0:
            st.info(f"Kostenlose Fragen: {left} / 3")
            st.progress((3 - left) / 3)
            st.caption("Danach: **1,99€**/Tag oder **6,99€**/Woche")
        else:
            st.error("Limit erreicht (0/3)")
            
            st.markdown("#### 🔓 Upgrade wählen:")
            col1, col2 = st.columns([1.5, 1])
            col1.markdown("24h Pass")
            col2.link_button("1,99€", link_day) 

            col1, col2 = st.columns([1.5, 1])
            col1.markdown("7-Tage")
            col2.link_button("6,99€", link_week) 
            
            st.caption("Sie erhalten eine **Bestellnummer** (cs_...).")

    st.markdown("---")

    # 自动查账区域
    with st.expander("🔓 Code / Bestellnummer"):
        code_input = st.text_input("Nr.", placeholder="cs_... einfügen", label_visibility="collapsed")
        
        if st.button("Aktivieren"):
            if code_input.startswith("cs_"):
                if not stripe.api_key:
                    st.error("Systemfehler: Stripe Key fehlt.")
                else:
                    try:
                        session = stripe.checkout.Session.retrieve(code_input)
                        if session.payment_status == 'paid':
                            payment_time = datetime.fromtimestamp(session.created)
                            now = datetime.now()
                            amount_paid = session.amount_total / 100 
                            
                            if amount_paid < 5.0: 
                                if now - payment_time < timedelta(hours=24):
                                    st.session_state.is_premium = "Day"
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("Code abgelaufen (>24h).")
                            else: 
                                if now - payment_time < timedelta(days=7):
                                    st.session_state.is_premium = "Week"
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("Code abgelaufen (>7 Tage).")
                        else:
                            st.error("Zahlung offen.")
                    except Exception as e:
                        st.error("Nummer nicht gefunden.")
            elif "VIP_CODE" in st.secrets and code_input == st.secrets["VIP_CODE"]:
                st.session_state.is_premium = "Week"
                st.success("VIP Login")
                st.rerun()
            else:
                st.error("Ungültig.")


# --- 4. 主界面标题与布局 ---
st.title("🏗️ DE-BauKI: Ihr Immobilien-, Bau- und Finanzierungsexperte")

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""<div style="text-align: center;"><div style="font-size: 24px;">⚖️</div><div style="font-weight: bold;">Baurecht Check</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div style="text-align: center;"><div style="font-size: 24px;">🔨</div><div style="font-weight: bold;">Sanierung</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div style="text-align: center;"><div style="font-size: 24px;">💶</div><div style="font-weight: bold;">Finanzierung</div></div>""", unsafe_allow_html=True)

st.markdown("---")


# --- 5. 【核心修复】聊天历史回显 ---
# 必须在 chat_input 之前执行，否则历史记录会闪烁或消失
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 如果历史消息里有图片，这里暂时不显示，只显示文字，
        # 如果需要显示图片，逻辑会更复杂，建议 MVP 版本只存文字对话。


# --- 6. 核心逻辑处理 ---
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash") # 修正模型名称

    # 检查是否允许提问
    can_ask = False
    if st.session_state.is_premium:
        can_ask = True
    elif st.session_state.msg_count < 3:
        can_ask = True
    
    # 只有当允许提问时，才显示输入框
    if can_ask:
        # 文件上传放在输入框上方，用折叠栏收纳比较整洁
        with st.expander("📎 Datei anhängen (optional)", expanded=False):
            uploaded_file = st.file_uploader("Bild oder PDF", type=["jpg", "png", "pdf", "jpeg"])

        user_input = st.chat_input("Frage stellen (z.B. Was kostet eine Wärmepumpe?)")

        if user_input:
            # A. 显示用户输入
            st.chat_message("user").markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            # B. 生成 AI 回答
            with st.chat_message("assistant"):
                with st.spinner("Bau-KI analysiert..."):
                    
                    # 准备 Prompt
                    sys_instruction = """
                    Du bist ein erfahrener deutscher Bau- und Finanzierungsexperte.
                    Antworte strukturiert auf Deutsch.
                    Disclaimer: "Hinweis: KI-Ersteinschätzung. Keine Rechts- oder Finanzberatung."
                    """
                    full_prompt = sys_instruction + "\n\nUser Frage: " + user_input

                    try:
                        # 调用 API
                        if uploaded_file:
                            img = Image.open(uploaded_file)
                            response = model.generate_content([full_prompt, img])
                        else:
                            response = model.generate_content(full_prompt)
                        
                        response_text = response.text
                        st.markdown(response_text)

                        # C. 存入历史
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        
                        # D. 【修复点2】扣费与刷新
                        if not st.session_state.is_premium:
                            st.session_state.msg_count += 1
                            st.rerun() # 强制刷新，让 sidebar 计数器立刻变
                            
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    else:
        # 次数用完的提示
        st.warning("🔒 Ihr kostenloses Limit ist erreicht (3/3). Bitte kaufen Sie einen Pass, um fortzufahren.")


# --- 7. 底部 Footer (合规信息) ---
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.info("📧 **Hilfe & Support**\n\nProblem mit dem Code? Kontaktieren Sie:\n\n**hello@lionmove.net**")

with col2:
    with st.expander("⚖️ Impressum & Rechtliches"):
        st.markdown("""
        **Betreiber:** [M.Sc. Architekt Li]  
        [Vorgarten 1b]  
        [38104 Braunschweig]  
        **Kontakt:** hello@lionmove.net  
        **Haftung:** KI-Inhalte sind keine Fachberatung.
        """)

st.caption("© 2026 Bau-KI. Braunschweig.")
