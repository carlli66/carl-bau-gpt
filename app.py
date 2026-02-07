import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. 核心配置
# ==========================================
PREMIUM_CODE = "BAU2026"  
STRIPE_LINK = "https://buy.stripe.com/6oUbJ1dR4bfQfsj0EodMI02" 

# ==========================================
# 2. 页面配置 (宽屏模式更显专业)
# ==========================================
st.set_page_config(
    page_title="DE-BauKI Experte", 
    page_icon="🏗️", 
    layout="centered"
)

# 初始化状态
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0 
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False 
if "messages" not in st.session_state:
    st.session_state.messages = [] 

# ==========================================
# 3. 侧边栏 (专业控制面板)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=60)
    st.markdown("### ⚙️ Einstellungen")

    # API Key 输入
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key", type="password")

    st.markdown("---")

    # 会员状态逻辑
    if st.session_state.is_premium:
        st.success("🌟 **Premium-Status: AKTIV**")
        st.caption("✅ Modell: **Gemini 2.5 Pro**")
        st.caption("✅ Unbegrenzte Anfragen")
        st.caption("✅ Bildanalyse aktiviert")
        
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
            st.caption("Testen Sie die Basis-Funktionen.")
        else:
            st.error("Limit erreicht (0/3)")
            
            st.markdown("#### 🔓 Upgrade auf PRO")
            st.markdown("""
            - **Unbegrenzte** Fragen
            - **Gemini 2.5 Pro** (Besseres Modell)
            - **Bild-Upload** & Analyse
            - **Finanzierungs-Check**
            """)
            st.link_button("👉 Jetzt freischalten (4,99€)", STRIPE_LINK)
            st.caption("Einmalig zahlen, 7 Tage nutzen.")

        st.markdown("---")
        
        # 密码输入框
        with st.expander("🎫 Code einlösen", expanded=True):
            user_code = st.text_input("Zugangscode:", placeholder="Code aus Bestätigung...", type="password")
            if st.button("Code prüfen"):
                if user_code == PREMIUM_CODE:
                    st.session_state.is_premium = True
                    st.balloons()
                    st.success("Freigeschaltet!")
                    st.rerun()
                else:
                    st.error("Ungültiger Code.")

# ==========================================
# 4. AI 智能核心 (Gemini 2.5 Pro)
# ==========================================
def get_ai_response(api_key, prompt, image=None):
    genai.configure(api_key=api_key)
    
    # 优先使用 Pro，其次 Flash
    # 确保调用的是您 API Key 支持的最新模型
    model_priority = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    
    last_error = None

    for model_name in model_priority:
        try:
            model = genai.GenerativeModel(model_name)
            
            content = [prompt]
            if image:
                content.append(image)
            
            # 发送请求
            response = model.generate_content(content)
            return response.text
            
        except Exception as e:
            last_error = e
            continue 
    
    raise last_error

# ==========================================
# 5. 主界面 (UI 升级)
# ==========================================

# 标题区域 - 恢复完整描述
st.title("🏗️ DE-BauKI")
st.subheader("Ihr Immobilien-, Bau- und Finanzierungsexperte")
st.caption("Powered by Google Gemini 2.5 Pro | Spezialisiert auf deutsche Standards (DIN/LBO)")

st.markdown("---")

# 核心功能展示 (Dashboard 风格)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; text-align:center;">
        <div style="font-size:30px;">⚖️</div>
        <div style="font-weight:bold; margin-top:5px;">Baurecht & LBO</div>
        <div style="font-size:12px; color:#555;">Genehmigungen, Abstandsflächen</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; text-align:center;">
        <div style="font-size:30px;">🔨</div>
        <div style="font-weight:bold; margin-top:5px;">Sanierung & Technik</div>
        <div style="font-size:12px; color:#555;">Dämmung, Heizung (WP), DIN</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; text-align:center;">
        <div style="font-size:30px;">💶</div>
        <div style="font-weight:bold; margin-top:5px;">Kosten & Finanzierung</div>
        <div style="font-size:12px; color:#555;">Schätzungen, KfW-Förderung</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 显示历史聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 6. 交互区域
# ==========================================
if api_key:
    # 权限判断
    can_ask = st.session_state.is_premium or (st.session_state.msg_count < 3)

    if can_ask:
        # 文件上传 (更明显的入口)
        uploaded_file = st.file_uploader("📎 Dokumente oder Bilder analysieren (Grundriss, Angebot, Foto)", type=["jpg", "png", "jpeg", "pdf"])

        if prompt := st.chat_input("Ihre Frage (z.B. 'Was kostet eine Kernsanierung für 120qm?')..."):
            
            # 1. 显示用户问题
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file:
                    st.image(uploaded_file, width=300, caption="Hochgeladene Datei")

            # 2. 生成 AI 回答
            with st.chat_message("assistant"):
                with st.spinner("Bau-KI analysiert Ihre Anfrage (Modell: Gemini 2.5 Pro)..."):
                    try:
                        img_obj = Image.open(uploaded_file) if uploaded_file else None
                        
                        # ★★★ System Prompt: 强制免责声明与专家身份 ★★★
                        sys_prompt = """
                        Du bist 'DE-BauKI', ein hochspezialisierter KI-Experte für den deutschen Immobilienmarkt, Baurecht (LBOs der Bundesländer), Sanierungstechnik (DIN-Normen) und Baufinanzierung (inkl. KfW/BAFA Förderungen).

                        Deine Regeln:
                        1. Antworte immer professionell, strukturiert und präzise auf Deutsch.
                        2. Bei Kostenfragen: Gib realistische Schätzbereiche (von-bis) an.
                        3. Bei Rechtsfragen: Zitiere, wenn möglich, relevante Paragraphen oder LBOs.
                        4. Finanzierung: Erwähne aktuelle Zinssituationen oder Förderprogramme, wenn passend.
                        
                        WICHTIG: Beende JEDE Antwort mit folgendem Disclaimer:
                        "⚠️ Hinweis: Dies ist eine KI-basierte Ersteinschätzung und ersetzt keine rechtliche Beratung durch einen Architekten, Anwalt oder Energieberater."
                        """
                        full_prompt = sys_prompt + "\n\nUser Frage: " + prompt

                        # 调用 AI
                        ans_text = get_ai_response(api_key, full_prompt, img_obj)
                        
                        # 显示并保存
                        st.markdown(ans_text)
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})

                        # 3. 扣费逻辑
                        if not st.session_state.is_premium:
                            st.session_state.msg_count += 1
                            st.rerun()

                    except Exception as e:
                        st.error(f"Ein Verbindungsfehler ist aufgetreten: {e}")
                        st.info("Bitte versuchen Sie es erneut oder überprüfen Sie Ihren API Key.")
    else:
        st.warning("🔒 **Ihr kostenloses Limit ist erreicht.**")
        st.markdown("Um fortzufahren und den **Immobilien-Experten** unbegrenzt zu nutzen, schalten Sie bitte den Premium-Zugang frei.")
else:
    st.info("👋 Willkommen! Bitte geben Sie links Ihren Google API Key ein, um zu starten.")

# ==========================================
# 7. 底部法律信息 (Impressum & Haftung)
# ==========================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

# 显眼的免责声明 (在输入框下方也显示)
st.warning("⚖️ **Haftungsausschluss:** Die Antworten dieser KI dienen ausschließlich Informationszwecken. Sie stellen keine verbindliche Rechts-, Steuer- oder Bauberatung dar.")

col1, col2 = st.columns([1, 1])

with col1:
    st.info("📧 **Support & Kontakt**\n\nFragen zum Code oder Probleme?\nE-Mail: **hello@xxxxxxx.net**")

with col2:
    with st.expander("📝 Impressum anzeigen"):
        st.markdown("""
        ### Angaben gemäß § 5 TMG
        
        **Betreiber:** M.Sc. Architekt [Ihr Name]  
        [Straße und Hausnummer]  
        [PLZ und Ort]  
        
        **Kontakt:** E-Mail: hello@xxxxxxx.net  
        
        **Umsatzsteuer-ID:** [USt-IdNr., falls vorhanden]
        """)

st.caption("© 2026 DE-BauKI. Entwickelt für den deutschen Immobilienmarkt.")
