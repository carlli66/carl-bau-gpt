import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. 页面配置 (Page Config) ---
st.set_page_config(page_title="DE-BauAI: Ihr digitaler Architekt", page_icon="🇩🇪")

# --- 2. 初始化 Session State (记忆功能) ---
# 用于记录用户问了几个问题，以及是否解锁了会员
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

# --- 3. 侧边栏 (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Einstellungen")
    # 这里依然需要 Key，未来可以把这个Key写死在后台(Secrets)里，不让用户看见
    api_key = st.text_input("Google API Key (Intern)", type="password")
    
    st.markdown("---")
    st.write("📊 **Status:**")
    if st.session_state.is_premium:
        st.success("💎 Premium Aktiviert (Unlimited)")
    else:
        left = 3 - st.session_state.msg_count
        st.info(f"Kostenlose Fragen übrig: {left}/3")
        
    st.markdown("---")
    # 简单的解锁逻辑 (模拟)
    unlock_code = st.text_input("Haben Sie einen Zugangscode?")
    if unlock_code == "BAU2026":  # 这里是你设置的“每日口令”
        st.session_state.is_premium = True
        st.success("Code akzeptiert!")

# --- 4. 界面标题 (UI) ---
st.title("🇩🇪 DE-BauAI: Der digitale Bauberater")
st.markdown("""
**Willkommen!** Ich bin Ihr KI-Architekt für Niedersachsen.
Stellen Sie mir Fragen zu *Baugenehmigung*, *Sanierung* oder *Kosten*.
""")

# --- 5. 核心逻辑 ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        # 使用通用稳定版模型
        model = genai.GenerativeModel("models/gemini-flash-latest") 

        # --- 系统指令 (System Prompt - 纯德语) ---
        sys_instruction = """
        Du bist ein erfahrener, in Niedersachsen zugelassener Architekt (Bauvorlageberechtigter).
        Deine Aufgabe ist es, Hausbesitzern und Bauherren professionelle Ersteinschätzungen zu geben.
        
        Regeln:
        1. Sprache: Antworte IMMER auf Deutsch. Professionell, höflich, präzise.
        2. Gesetz: Zitiere die NBauO (Niedersächsische Bauordnung), wo immer möglich.
        3. Sicherheit: Bei statischen Fragen (Wanddurchbruch etc.) warne IMMER vor Risiken ("Bitte Statiker konsultieren").
        4. Haftungsausschluss: Beende jede Antwort mit: 
           "Hinweis: Dies ist eine KI-Einschätzung. Für rechtssichere Planung wenden Sie sich bitte an das Bauamt."
        """
        
        # 聊天历史展示 (此处略简，为了代码简洁，直接用单次问答模式，也可做成连续对话)
        
        # --- 6. 计费检查逻辑 ---
        # 如果不是会员，且次数超过3次，显示支付墙
        if not st.session_state.is_premium and st.session_state.msg_count >= 3:
            st.error("🔒 Ihr kostenloses Kontingent ist aufgebraucht.")
            st.markdown("""
            ### 🔓 Schalten Sie den vollen Zugang frei!
            Erhalten Sie **unbegrenzte Antworten** und **Dokumenten-Analyse** für 24 Stunden.
            
            **Preis: nur 4,99 €**
            """)
            # 这里放你的 Stripe 链接
            st.link_button("👉 Jetzt Tagespass kaufen (4,99 €)", "https://paypal.me/carlsbauai") 
            st.caption("Nach der Zahlung erhalten Sie den Code 'BAU2026'.")
            
            # 禁用输入框
            user_input = st.chat_input("Limit erreicht.", disabled=True)
            
        else:
            # 正常咨询模式
            uploaded_file = st.file_uploader("Bauzeichnung/Foto hochladen (Optional)", type=["jpg", "png"])
            user_input = st.chat_input("Ihre Frage (z.B.: Brauche ich für ein Carport eine Genehmigung?)")

            if user_input:
                # 计数器 +1
                st.session_state.msg_count += 1
                
                # 显示用户提问
                with st.chat_message("user"):
                    st.write(user_input)
                    if uploaded_file:
                        st.image(uploaded_file)

                # 生成回答
                with st.chat_message("assistant"):
                    with st.spinner("Ich überprüfe die Bauvorschriften..."):
                        # 组合 Prompt
                        full_prompt = sys_instruction + "\n\nUser Frage: " + user_input
                        
                        if uploaded_file:
                            img = Image.open(uploaded_file)
                            response = model.generate_content([full_prompt, img])
                        else:
                            response = model.generate_content(full_prompt)
                            
                        st.write(response.text)
                        
                        # 如果是免费用户，提醒还剩几次
                        if not st.session_state.is_premium:
                            left = 3 - st.session_state.msg_count
                            if left > 0:
                                st.caption(f"ℹ️ Noch {left} kostenlose Fragen.")

    except Exception as e:
        st.error(f"Systemfehler: {e}")
else:
    st.info("👈 Bitte API Key eingeben (Admin)")
