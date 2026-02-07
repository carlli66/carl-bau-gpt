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

# --- 2. 初始化 Session State ---
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False 

# --- 3. 侧边栏 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### Mein Status")

    # 配置 Keys (优先从 Secrets 读取)
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

    # 会员状态显示
    if st.session_state.is_premium == "Day":
        st.success("🎫 Tagespass Aktiv")
        st.caption("Gültig für 24 Stunden.")
    elif st.session_state.is_premium == "Week":
        st.success("👑 Wochenpass Aktiv")
        st.caption("7 Tage Premium-Zugriff.")
    else:
        # 免费用户逻辑
        left = 3 - st.session_state.msg_count
        if left > 0:
            st.info(f"Kostenlose Fragen: {left} / 3")
            st.progress((3 - left) / 3)
            # --- 【修改点3】新增价格提示 ---
            st.caption("Danach: **1,99€**/Tag oder **6,99€**/Woche")
            # ---------------------------
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
                            # 简单的金额判断逻辑：小于5欧算日票，大于5欧算周票
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

# --- 4. 主界面优化 ---

# 【修改点4】更新大标题 (语法修正: Ihr Experte)
st.title("🏗️ DE-BauKI: Ihr Immobilien-, Bau- und Finanzierungsexperte")

st.markdown("---")

# 【修改点1 & 2】使用 HTML 美化三列布局 (解决文字显示不全问题)
# 这里不用 st.metric，改用自定义 HTML，保证文字完整显示且居中美观
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="text-align: center;">
        <div style="font-size: 24px;">⚖️</div>
        <div style="font-weight: bold; font-size: 16px;">Baurecht Check</div>
        <div style="font-size: 14px; color: gray;">Deutschlandweit</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center;">
        <div style="font-size: 24px;">🔨</div>
        <div style="font-weight: bold; font-size: 16px;">Sanierung</div>
        <div style="font-size: 14px; color: gray;">Kosten & Preise</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center;">
        <div style="font-size: 24px;">💶</div>
        <div style="font-weight: bold; font-size: 16px;">Finanzierung</div>
        <div style="font-size: 14px; color: gray;">Budget & KfW</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 5. AI 逻辑 ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-flash-latest") 

        # Prompt 更新：覆盖全德国 + 融资
        sys_instruction = """
        Du bist ein erfahrener deutscher Bau- und Finanzierungsexperte.
        
        Aufgaben:
        1. **Baurecht:** Prüfe Genehmigungspflichten basierend auf der Landesbauordnung (LBO) des jeweiligen Bundeslandes. Frage den Nutzer nach dem Bundesland, falls unklar.
        2. **Kosten:** Schätze Sanierungskosten realistisch (Material + Handwerker).
        3. **Finanzierung:** Ermittle Gesamtkosten (Kauf + Sanierung) und weise auf KfW-Förderungen hin.

        Regeln:
        - Antworte strukturiert auf Deutsch.
        - Disclaimer: "Hinweis: KI-Ersteinschätzung. Keine Rechts- oder Finanzberatung."
        """
        
        if st.session_state.is_premium or st.session_state.msg_count < 3:
            
            # 使用 expander 把上传按钮收起来一点，界面更清爽 (可选)
            uploaded_file = st.file_uploader("Datei hochladen (Grundriss / Exposé / Angebot)", type=["jpg", "png", "pdf", "jpeg"])
            
            user_input = st.chat_input("Frage stellen (z.B. Was kostet eine Wärmepumpe im Altbau?)")

            if user_input:
                st.session_state.msg_count += 1
                
                with st.chat_message("user"):
                    st.write(user_input)
                    if uploaded_file:
                        st.image(uploaded_file, caption="Anhang", width=300)

                with st.chat_message("assistant"):
                    with st.spinner("Analysiere..."):
                        full_prompt = sys_instruction + "\n\nUser Frage: " + user_input
                        try:
                            if uploaded_file:
                                img = Image.open(uploaded_file)
                                response = model.generate_content([full_prompt, img])
                            else:
                                response = model.generate_content(full_prompt)
                            st.write(response.text)
                        except Exception as e:
                            st.error("Fehler bei der Analyse.")
        else:
            st.warning("🔒 Kostenloses Limit erreicht. Bitte Upgrade wählen.")

    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")

import streamlit as st

# --- 放在页面底部或 Sidebar 底部 ---
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    # 紧急联系方式 (Support)
    st.info("📧 **Hilfe & Support**\n\nHaben Sie keinen Code erhalten oder gibt es Probleme mit der Zahlung? Kontaktieren Sie uns bitte:\n\n**support@bau-ki.de** (Bitte Ihre E-Mail einfügen)")

with col2:
    # 法律声明 (Impressum) - 折叠以节省空间
    with st.expander("⚖️ Impressum & Rechtliches"):
        st.markdown("""
        ### Angaben gemäß § 5 TMG
        
        **Betreiber:** [M.Sc. Architekt Li]  
        [Vorgarten 1b]  
        [38104 Braunschweig]  
        
        **Kontakt:** E-Mail: [hello@lionmove.net]  
        
        **Umsatzsteuer-ID:** [USt-IdNr.: DE368013016]  
        
        **Haftungsausschluss:** Die durch die KI generierten Inhalte dienen lediglich als Hilfestellung und ersetzen keine fachliche Beratung. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte wird keine Gewähr übernommen.
        """)

# 版权声明
st.caption("© 2026 Bau-KI. Entwickelt in Braunschweig. Alle Rechte vorbehalten.")
