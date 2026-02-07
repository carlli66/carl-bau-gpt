import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. 页面配置 ---
st.set_page_config(page_title="DE-BauAI: Ihr digitaler Architekt", page_icon="🇩🇪")

# --- 2. 初始化状态 ---
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

# --- 3. 侧边栏 (控制台) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50) # 加个小图标
    st.header("Einstellungen")
    
    # 【自动读取 Key】: 不再需要用户输入
    # 如果 Secrets 里没有配 Key，为了防止报错，给个提示
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ System Online")
    else:
        api_key = st.text_input("Admin Key eingeben", type="password")
        st.warning("⚠️ Bitte API Key in Secrets hinterlegen")

    st.markdown("---")
    
    # 状态栏
    if st.session_state.is_premium:
        st.success("💎 Premium Aktiv (24h)")
        st.caption("Genießen Sie unbegrenzte Beratung!")
    else:
        left = 3 - st.session_state.msg_count
        st.info(f"Kostenlose Fragen: {left}/3")
        st.progress((3 - left) / 3)

    st.markdown("---")
    
    # 解锁区域
    with st.expander("🔓 Zugangscode eingeben"):
        code = st.text_input("Code:", placeholder="z.B. BAU2026")
        if st.button("Freischalten"):
            if code == "BAU2026":  # 你的 Stripe 确认页上给的密码
                st.session_state.is_premium = True
                st.rerun() # 刷新页面
            else:
                st.error("Ungültiger Code")

# --- 4. 主界面 ---
st.title("🇩🇪 DE-BauAI: Ihr Bau-Experte für ganz Deutschland")

# 展示服务范围
col1, col2, col3 = st.columns(3)
col1.metric("🏗️ Genehmigung", "LBO Prüfung")
col2.metric("💰 Kosten & Preise", "Schätzung")
col3.metric("🌱 Energie & KfW", "Förderung")

st.markdown("---")

# --- 5. 核心逻辑 ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-flash-latest") 

        # --- 升级版全德国 Prompt ---
        sys_instruction = """
        Du bist ein erfahrener deutscher Architekt und Energieberater (Energieeffizienz-Experte).
        Deine Aufgabe: Professionelle Bauberatung für ganz Deutschland.

        Regeln:
        1. **Kontext Bundesland:** Wenn der Nutzer nach Gesetzen fragt (z.B. Abstandsflächen), frage zuerst: "In welchem Bundesland befindet sich das Objekt?", da die LBOs unterschiedlich sind.
        2. **Themen:** Du bist Experte für Baugenehmigungen, Sanierungskosten, Handwerker-Angebote und KfW/BAFA Förderungen.
        3. **Struktur:** Antworte klar, strukturiert und immer auf Deutsch.
        4. **Disclaimer:** Ende immer mit: "Hinweis: KI-Ersteinschätzung. Keine Rechtsberatung."
        5. **Upsell:** Wenn es komplex wird (z.B. Statik, detaillierter Bauantrag), empfehle die persönliche Beratung durch Architekt Carl.
        """
        
        # --- 6. 计费墙逻辑 ---
        if not st.session_state.is_premium and st.session_state.msg_count >= 3:
            st.warning("🔒 Ihr kostenloses Tageslimit ist erreicht.")
            st.markdown("""
            <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border:1px solid #dcdcdc;">
                <h3>🚀 Upgrade auf Premium (Tagespass)</h3>
                <p>Schalten Sie sofort folgende Funktionen frei:</p>
                <ul>
                    <li>✅ <b>Unbegrenzte Fragen</b> für 24 Stunden</li>
                    <li>✅ <b>Dokumenten-Check</b> (Grundrisse, Angebote)</li>
                    <li>✅ <b>KfW-Fördermittel</b> Analyse</li>
                </ul>
                <h2 style="color:#2ecc71">Nur 4,99 €</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # 这里的链接换成你 Stripe 生成的真实链接
            st.link_button("👉 Hier klicken & Freischalten (Stripe)", "https://buy.stripe.com/test_eVa...") 
            st.caption("Nach der Zahlung erhalten Sie sofort Ihren Zugangscode.")
            
        else:
            # --- 正常对话界面 ---
            if st.session_state.msg_count == 0:
                st.chat_message("assistant").write("Hallo! Wo drückt der Schuh? Ich kann Ihnen bei Bauanträgen, Kosten oder Energiethemen helfen.")

            # 文件上传
            uploaded_file = st.file_uploader("Datei hochladen (Grundriss/Angebot/Foto)", type=["jpg", "png", "pdf"])
            
            # 输入框
            user_input = st.chat_input("Ihre Frage stellen...")

            if user_input:
                st.session_state.msg_count += 1
                
                with st.chat_message("user"):
                    st.write(user_input)
                    if uploaded_file:
                        st.image(uploaded_file, caption="Hochgeladene Datei", width=300)

                with st.chat_message("assistant"):
                    with st.spinner("Analysiere deutsche Bauvorschriften..."):
                        # 拼接 Prompt
                        full_prompt = sys_instruction + "\n\nUser Frage: " + user_input
                        
                        try:
                            if uploaded_file:
                                img = Image.open(uploaded_file)
                                response = model.generate_content([full_prompt, img])
                            else:
                                response = model.generate_content(full_prompt)
                            
                            st.write(response.text)
                        except Exception as e:
                            st.error("Entschuldigung, ich konnte das Bild nicht verarbeiten. Bitte versuchen Sie es erneut.")

    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
