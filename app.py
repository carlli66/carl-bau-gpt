import streamlit as st
import google.generativeai as genai
from PIL import Image
import extra_streamlit_components as stx
import time

# ==========================================
# 1. 页面配置 (宽屏 + 移动端优化)
# ==========================================
st.set_page_config(
    page_title="DE-BauKI | Ihr Experten-Tool", 
    page_icon="🏗️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 核心配置
PREMIUM_CODE = "BAU2026"  
STRIPE_LINK = "https://buy.stripe.com/6oUbJ1dR4bfQfsj0EodMI02" 

# ==========================================
# 2. Cookie 管理 (无需 @st.cache_resource)
# ==========================================
cookie_manager = stx.CookieManager()
cookie_usage = cookie_manager.get(cookie="bauki_usage")

# 初始化 Session State
if "msg_count" not in st.session_state:
    st.session_state.msg_count = int(cookie_usage) if cookie_usage else 0
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False 
if "messages" not in st.session_state:
    st.session_state.messages = [] 

# 同步 Cookie
if cookie_usage and int(cookie_usage) > st.session_state.msg_count:
    st.session_state.msg_count = int(cookie_usage)

# ==========================================
# 3. 侧边栏 (黑色模式适配)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=70)
    st.markdown("## 🏗️ DE-BauKI")
    st.caption("Professional AI Real Estate Expert")
    
    # API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("🔑 Google API Key", type="password")

    st.markdown("---")

    if st.session_state.is_premium:
        st.success("🌟 **PREMIUM STATUS**")
        st.caption("✅ Modell: **Gemini 2.5 Pro**")
        st.caption("✅ Unbegrenzt")
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.is_premium = False
            st.rerun()
    else:
        left = 3 - st.session_state.msg_count
        if left < 0: left = 0
        
        st.info(f"Basis-Nutzung: **{left} / 3** Fragen")
        st.progress((3 - left) / 3)
        
        if left == 0:
            st.error("Limit erreicht.")
            st.markdown("### 🔓 Professional Upgrade")
            st.link_button("👉 Jetzt freischalten (4,99€)", STRIPE_LINK, use_container_width=True)
            
            with st.expander("🎫 Code einlösen"):
                code = st.text_input("Code:", type="password")
                if st.button("Aktivieren"):
                    if code == PREMIUM_CODE:
                        st.session_state.is_premium = True
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Ungültig")

    st.markdown("---")
    st.caption("v3.3 Dark Mode Fix")

# ==========================================
# 4. AI 核心函数
# ==========================================
def get_ai_response(api_key, sys_prompt, user_prompt, image=None):
    genai.configure(api_key=api_key)
    # 优先顺序
    models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            content = [sys_prompt + "\n\nUser Anfrage: " + user_prompt]
            if image: content.append(image)
            response = model.generate_content(content)
            return response.text
        except:
            continue
    raise Exception("KI-Dienst momentan ausgelastet.")

# ==========================================
# 5. 主界面 (CSS 强制修复看不清的问题)
# ==========================================

# ★★★ CSS 修复核心：强制文字颜色为深色，背景为浅色 ★★★
st.markdown("""
<style>
    /* 强制 Header 颜色适配 */
    .main-header {
        font-size: 2.5rem; 
        font-weight: 700; 
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem; 
        margin-bottom: 20px; 
        opacity: 0.8;
    }
    
    /* 修复 Feature Card 在夜间模式看不清的问题 */
    .feature-card {
        background-color: #F1F5F9 !important; /* 强制浅灰背景 */
        padding: 15px; 
        border-radius: 8px; 
        border-left: 5px solid #0F172A;
        color: #0F172A !important; /* ★★★ 强制文字为深蓝/黑色 ★★★ */
        margin-bottom: 10px;
    }
    
    /* 强制卡片内的小字也是深色 */
    .feature-card div, .feature-card b {
        color: #0F172A !important;
    }
</style>

<div class="main-header">DE-BauKI Experte</div>
<div class="sub-header">Ihr digitaler Architekt, Bauingenieur und Finanzierungsberater.</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Privat & Wohnen", 
    "🏢 Gewerbe & Investment", 
    "⚖️ Recht & Normen", 
    "💶 Finanzierung & KfW"
])

base_role = "Du bist 'DE-BauKI', Deutschlands führender KI-Experte für Immobilien."
current_context = ""

# 定义内容 (HTML 中已强制字体颜色)
with tab1:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Einfamilienhäuser, Eigentumswohnungen, Sanierung, Energieeffizienz (GEG).
    </div>
    """, unsafe_allow_html=True)
    current_context = "ROLLENBESCHREIBUNG: Architekt für privaten Wohnbau. Fokus: Wohnkomfort, Kosten, Sanierung."

with tab2:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Bürogebäude, Lagerhallen, Renditeobjekte, Brandschutz, ASR.
    </div>
    """, unsafe_allow_html=True)
    current_context = "ROLLENBESCHREIBUNG: Projektentwickler Gewerbe. Fokus: Rendite, Brandschutz, Flächeneffizienz."

with tab3:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Landesbauordnungen (LBO), Baugenehmigungen, Abstandsflächen, DIN-Normen.
    </div>
    """, unsafe_allow_html=True)
    current_context = "ROLLENBESCHREIBUNG: Fachplaner Baurecht. Fokus: Genehmigungspflicht, LBO, DIN-Normen."

with tab4:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Baufinanzierung, Zinsen, KfW-Förderprogramme, BAFA, Budget.
    </div>
    """, unsafe_allow_html=True)
    current_context = "ROLLENBESCHREIBUNG: Finanzierungsberater. Fokus: Vollkostenrechnung, Kredit, Förderung."

st.markdown("---")

# ==========================================
# 6. 交互区域 (IndentationError 修复)
# ==========================================

# 历史记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ★★★ 注意：这里的缩进必须严格对齐 ★★★
if api_key:
    can_ask = st.session_state.is_premium or (st.session_state.msg_count < 3)

    if can_ask:
        with st.expander("📎 Dokumenten-Upload", expanded=False):
            uploaded_file = st.file_uploader("Datei", type=["jpg", "png", "pdf"], label_visibility="collapsed")

        placeholder_text = "Stellen Sie Ihre Frage hier..."
        if tab4: placeholder_text = "z.B. Wie viel Eigenkapital brauche ich?"
        
        if prompt := st.chat_input(placeholder_text):
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file: st.image(uploaded_file, width=300)

            with st.chat_message("assistant"):
                with st.spinner("Bau-KI analysiert..."):
                    try:
                        img_obj = Image.open(uploaded_file) if uploaded_file else None
                        
                        final_sys_prompt = base_role + current_context + """
                        \nREGELN:
                        1. Antworte auf Deutsch.
                        2. Strukturiere die Antwort.
                        3. Disclaimer am Ende: "⚠️ Haftungsausschluss: KI-Ersteinschätzung. Keine Rechtsberatung."
                        """
                        
                        ans_text = get_ai_response(api_key, final_sys_prompt, prompt, img_obj)
                        
                        st.markdown(ans_text)
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})

                        if not st.session_state.is_premium:
                            new_val = st.session_state.msg_count + 1
                            st.session_state.msg_count = new_val
                            cookie_manager.set("bauki_usage", new_val, key="update_usage")
                            time.sleep(0.5)
                            st.rerun()

                    except Exception as e:
                        st.error(f"Fehler: {e}")
    else:
        st.warning("🔒 Limit erreicht.")
        st.info("Bitte Premium freischalten.")
else:
    st.info("👋 Bitte Google API Key eingeben.")

# ==========================================
# 7. Footer
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.caption("© 2026 DE-BauKI | Gemini 2.5 Pro")
