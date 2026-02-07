import streamlit as st
import google.generativeai as genai
import stripe
from PIL import Image
from datetime import datetime, timedelta

# --- 1. 页面基础配置 ---
st.set_page_config(
    page_title="BauAI: Ihr digitaler Architekt", 
    page_icon="🏗️",
    layout="centered"
)

# --- 2. 初始化 Session State (记忆模块) ---
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False # False, "Day", or "Week"

# --- 3. 侧边栏 (控制中心) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### Mein Status")

    # [A] 配置 API Keys (优先从 Secrets 读取)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key", type="password")
        st.warning("⚠️ Admin Mode: Key manuell eingegeben")

    if "STRIPE_API_KEY" in st.secrets:
        stripe.api_key = st.secrets["STRIPE_API_KEY"]
    
    # 获取 Stripe 链接 (从 Secrets 读取，或者使用默认占位符)
    link_day = st.secrets.get("LINK_DAY", "https://buy.stripe.com/你的日票链接")
    link_week = st.secrets.get("LINK_WEEK", "https://buy.stripe.com/你的周票链接")

    st.markdown("---")

    # [B] 会员状态显示
    if st.session_state.is_premium == "Day":
        st.success("🎫 Tagespass Aktiv")
        st.caption("Gültig für 24 Stunden.")
    elif st.session_state.is_premium == "Week":
        st.success("👑 Wochenpass Aktiv")
        st.caption("7 Tage Premium-Zugriff.")
    else:
        # [C] 免费用户逻辑
        left = 3 - st.session_state.msg_count
        if left > 0:
            st.info(f"Kostenlose Fragen: {left} / 3")
            st.progress((3 - left) / 3)
        else:
            st.error("Limit erreicht (0/3)")
            
            # --- 付费墙 (Paywall) ---
            st.markdown("#### 🔓 Upgrade wählen:")
            
            # 选项 1: 日票
            col1, col2 = st.columns([1.5, 1])
            col1.markdown("**24h Pass**")
            col2.link_button("1,99€", link_day) 

            # 选项 2: 周票
            col1, col2 = st.columns([1.5, 1])
            col1.markdown("**7-Tage Pass**")
            col2.link_button("9,99€", link_week) 
            
            st.caption("Nach Zahlung erhalten Sie eine **Bestellnummer** (cs_...).")

    st.markdown("---")

    # [D] 自动查账 / 解锁区域
    with st.expander("🔓 Code / Bestellnummer eingeben"):
        code_input = st.text_input("Code:", placeholder="cs_... oder Code", label_visibility="collapsed")
        
        if st.button("Aktivieren"):
            # 1. 优先检查：是否是 Stripe 订单号 (cs_...)
            if code_input.startswith("cs_"):
                if not stripe.api_key:
                    st.error("Systemfehler: Stripe Key fehlt.")
                else:
                    try:
                        session = stripe.checkout.Session.retrieve(code_input)
                        if session.payment_status == 'paid':
                            payment_time = datetime.fromtimestamp(session.created)
                            now = datetime.now()
                            
                            # 判断金额来区分日票/周票 (假设日票 < 5欧)
                            amount_paid = session.amount_total / 100 # 转成欧元
                            
                            if amount_paid < 5.0: # 日票逻辑
                                if now - payment_time < timedelta(hours=24):
                                    st.session_state.is_premium = "Day"
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("Dieser Tagespass ist abgelaufen (>24h).")
                            else: # 周票逻辑
                                if now - payment_time < timedelta(days=7):
                                    st.session_state.is_premium = "Week"
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("Dieser Wochenpass ist abgelaufen (>7 Tage).")
                        else:
                            st.error("Zahlung noch nicht abgeschlossen.")
                    except Exception as e:
                        st.error("Bestellnummer nicht gefunden.")
            
            # 2. 备用检查：是否是后台预设的万能暗号 (VIP Code)
            elif "VIP_CODE" in st.secrets and code_input == st.secrets["VIP_CODE"]:
                st.session_state.is_premium = "Week"
                st.success("VIP Code akzeptiert!")
                st.rerun()
            else:
                st.error("Ungültiger Code.")

# --- 4. 主界面 ---
st.title("🏗️ DE-BauAI: Ihr Bau- & Finanzierungs-Experte")

# 服务概览
col1, col2, col3 = st.columns(3)
col1.metric("⚖️ Genehmigung", "NBauO Check")
col2.metric("🔨 Sanierung", "Kosten-Schätzung")
col3.metric("💶 Finanzierung", "Budget-Planung")

st.markdown("---")

# --- 5. AI 核心逻辑 ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-flash-latest") 

        # --- 终极 Prompts (懂法律 + 懂钱) ---
        sys_instruction = """
        Du bist ein erfahrener deutscher Architekt (Niedersachsen) und Baufinanzierungs-Experte.
        
        Deine Aufgaben:
        1. **Sanierung & Kosten:** Schätze Kosten für Renovierungen (Dach, Fenster, Heizung) realistisch inkl. Handwerkerpreise 2024/2025.
        2. **Baurecht:** Prüfe Genehmigungspflichten strikt nach NBauO (Niedersachsen).
        3. **Finanzierung:** - Berechne "Gesamtkosten" (Kaufpreis + Nebenkosten + Sanierung).
           - Weise auf KfW-Förderprogramme hin (z.B. Nr. 261, 124, 424).
           - Warne vor finanziellen Risiken (Puffer einplanen!).

        Regeln:
        - Antworte strukturiert auf Deutsch.
        - Sei direkt und ehrlich ("Das lohnt sich nicht").
        - Disclaimer am Ende: "Hinweis: KI-Ersteinschätzung. Keine Rechts- oder Finanzberatung. Bitte Architekt/Bankberater konsultieren."
        """
        
        # --- 聊天/输入区 ---
        # 只有在 (是会员) 或者 (还有免费次数) 时显示输入框
        if st.session_state.is_premium or st.session_state.msg_count < 3:
            
            uploaded_file = st.file_uploader("Datei hochladen (Grundriss / Exposé / Foto)", type=["jpg", "png", "pdf", "jpeg"])
            user_input = st.chat_input("Ihre Frage (z.B.: Was kostet eine Dachsanierung für 120qm?)")

            if user_input:
                st.session_state.msg_count += 1 # 扣除次数
                
                with st.chat_message("user"):
                    st.write(user_input)
                    if uploaded_file:
                        st.image(uploaded_file, caption="Anhang", width=300)

                with st.chat_message("assistant"):
                    with st.spinner("Analysiere Daten & Vorschriften..."):
                        # 组合 Prompt
                        full_prompt = sys_instruction + "\n\nUser Frage: " + user_input
                        
                        try:
                            if uploaded_file:
                                img = Image.open(uploaded_file)
                                response = model.generate_content([full_prompt, img])
                            else:
                                response = model.generate_content(full_prompt)
                            
                            st.write(response.text)
                        except Exception as e:
                            st.error("Fehler bei der Analyse. Bitte versuchen Sie es erneut.")
        else:
            st.warning("🔒 Kostenloses Limit erreicht. Bitte Upgrade wählen.")

    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
