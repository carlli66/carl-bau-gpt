import streamlit as st
import google.generativeai as genai
from PIL import Image
import extra_streamlit_components as stx
import time

# ==========================================
# 1. 专业级页面配置
# ==========================================
st.set_page_config(
    page_title="DE-BauKI | Ihr Experten-Tool", 
    page_icon="🏗️", 
    layout="wide", # 开启宽屏模式
    initial_sidebar_state="expanded"
)

# 核心配置
PREMIUM_CODE = "BAU2026"  
STRIPE_LINK = "https://buy.stripe.com/6oUbJ1dR4bfQfsj0EodMI02" 

# ==========================================
# 2. Cookie 管理 & 状态初始化 (已修复 CachedWidgetWarning)
# ==========================================
# ★★★ 修复点：直接初始化，不要使用 @st.cache_resource ★★★
cookie_manager = stx.CookieManager()

# 获取 Cookie (稍作延迟以确保组件加载)
cookie_usage = cookie_manager.get(cookie="bauki_usage")

# 初始化 Session State
if "msg_count" not in st.session_state:
    # 如果 Cookie 有值，就用 Cookie 的值，否则为 0
    st.session_state.msg_count = int(cookie_usage) if cookie_usage else 0

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False 
if "messages" not in st.session_state:
    st.session_state.messages = [] 

# 同步检查 (如果浏览器里存的次数比当前 Session 多，说明是刷新了页面，强制同步)
if cookie_usage and int(cookie_usage) > st.session_state.msg_count:
    st.session_state.msg_count = int(cookie_usage)

# ==========================================
# 3. 侧边栏 (控制面板)
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

    # 状态显示
    if st.session_state.is_premium:
        st.success("🌟 **PREMIUM STATUS**")
        st.caption("✅ Modell: **Gemini 2.5 Pro**")
        st.caption("✅ Gewerbe & Privat")
        st.caption("✅ Dokumentenanalyse")
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.is_premium = False
            # 清除状态并刷新
            st.rerun()
    else:
        # 免费版进度条
        left = 3 - st.session_state.msg_count
        if left < 0: left = 0
        
        st.info(f"Basis-Nutzung: **{left} / 3** Fragen")
        st.progress((3 - left) / 3)
        
        if left == 0:
            st.error("Limit erreicht.")
            st.markdown("### 🔓 Professional Upgrade")
            st.markdown("""
            Nutzen Sie das volle Potenzial:
            - 🏢 **Gewerbebau & Investment**
            - 💶 **Detaillierte Finanzierung**
            - ⚖️ **Rechtssichere Ersteinschätzung**
            """)
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
    st.caption("v3.2 Professional Build")

# ==========================================
# 4. 智能 AI 核心 (多模型支持)
# ==========================================
def get_ai_response(api_key, sys_prompt, user_prompt, image=None):
    genai.configure(api_key=api_key)
    # 优先使用最强模型
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
    raise Exception("Alle KI-Modelle derzeit ausgelastet.")

# ==========================================
# 5. 主界面布局 (Tab 分页设计 - 专业版)
# ==========================================

# Hero Header - 专业配色
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 700; color: #0F172A; margin-bottom: 0;}
    .sub-header {font-size: 1.2rem; color: #475569; margin-bottom: 20px;}
    .feature-card {background-color: #F1F5F9; padding: 15px; border-radius: 8px; border-left: 5px solid #0F172A;}
</style>
<div class="main-header">DE-BauKI Experte</div>
<div class="sub-header">Ihr digitaler Architekt, Bauingenieur und Finanzierungsberater.</div>
""", unsafe_allow_html=True)

# 定义四个专业板块
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Privat & Wohnen", 
    "🏢 Gewerbe & Investment", 
    "⚖️ Recht & Normen", 
    "💶 Finanzierung & KfW"
])

# 默认 System Prompt
base_role = "Du bist 'DE-BauKI', Deutschlands führender KI-Experte für Immobilien."
current_context = ""

with tab1:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Einfamilienhäuser, Eigentumswohnungen, Sanierung, Energieeffizienz (GEG).
    </div>
    """, unsafe_allow_html=True)
    current_context = """
    ROLLENBESCHREIBUNG:
    Du bist ein erfahrener Architekt für privaten Wohnbau.
    Fokus: Wohnkomfort, Grundrissoptimierung, Kosteneffizienz für Privatleute, energetische Sanierung (Wärmepumpe, Dämmung).
    Tone-of-Voice: Hilfsbereit, verständlich, aber fachlich korrekt.
    """

with tab2:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Bürogebäude, Lagerhallen, Renditeobjekte, Brandschutz, Arbeitsstättenverordnung.
    </div>
    """, unsafe_allow_html=True)
    current_context = """
    ROLLENBESCHREIBUNG:
    Du bist ein Projektentwickler und Architekt für Gewerbeimmobilien.
    Fokus: Flächeneffizienz, Arbeitsstättenrichtlinien (ASR), Brandschutz, Renditeberechnung, Nutzungsänderungen.
    Tone-of-Voice: Business-orientiert, zahlengetrieben, präzise.
    """

with tab3:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Landesbauordnungen (LBO), Baugenehmigungen, Abstandsflächen, DIN-Normen.
    </div>
    """, unsafe_allow_html=True)
    current_context = """
    ROLLENBESCHREIBUNG:
    Du bist ein Fachplaner für Baurecht und Normung.
    Fokus: Prüfung auf Genehmigungspflicht, LBO-Check (nach Bundesland), DIN-Normen (z.B. DIN 276, DIN 277), Nachbarschaftsrecht.
    Tone-of-Voice: Juristisch präzise, warnend bei Risiken, zitierend (Paragraphen).
    """

with tab4:
    st.markdown("""
    <div class="feature-card">
    <b>Fokus:</b> Baufinanzierung, Zinsen, KfW-Förderprogramme, BAFA-Zuschüsse, Budgetplanung.
    </div>
    """, unsafe_allow_html=True)
    current_context = """
    ROLLENBESCHREIBUNG:
    Du bist ein unabhängiger Baufinanzierungsberater.
    Fokus: Machbarkeitsanalyse, Vollkostenrechnung (Kaufpreis + Nebenkosten + Sanierung), Fördermittel-Check (KfW/BAFA), Tilgungspläne.
    Tone-of-Voice: Analytisch, konservativ kalkulierend.
    """

st.markdown("---")

# ==========================================
# 6. 聊天与交互区域
# ==========================================

# 历史记录回显
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if api_key:
    # 权限判断
    can_ask = st.session_state.is_premium or (st.session_state.msg_count < 3)

    if can_ask:
        # 文件上传区 (更专业)
        with st.expander("📎 Dokumenten-Upload (Grundrisse, Exposés, Angebote)", expanded=False):
            uploaded_file = st.file_uploader("Datei auswählen", type=["jpg", "png", "jpeg", "pdf"], label_visibility="collapsed")

        # 输入框
        placeholder_text = "Stellen Sie Ihre Frage hier..."
        if tab4: placeholder_text = "z.B. Welche KfW-Förderung gibt es für Neubau?"
        
        if prompt := st.chat_input(placeholder_text):
            
            # 1. 记录用户输入
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file: st.image(uploaded_file, width=300)

            # 2. 生成回答
            with st.chat_message("assistant"):
                with st.spinner("Bau-KI analysiert Daten & Vorschriften..."):
                    try:
                        img_obj = Image.open(uploaded_file) if uploaded_file else None
                        
                        # 组合最终 Prompt
                        final_sys_prompt = base_role + current_context + """
                        \nALLGEMEINE REGELN:
                        1. Antworte immer auf Deutsch.
                        2. Strukturiere deine Antwort (Fettdruck, Aufzählungszeichen).
                        3. Beende JEDE Antwort mit dem Disclaimer:
                        "⚠️ Haftungsausschluss: KI-Ersteinschätzung. Ersetzt keine fachliche Planung oder Rechtsberatung."
                        """
                        
                        # 调用 AI
                        ans_text = get_ai_response(api_key, final_sys_prompt, prompt, img_obj)
                        
                        st.markdown(ans_text)
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})

                        # 3. 扣费 & Cookie 更新
                        if not st.session_state.is_premium:
                            new_val = st.session_state.msg_count + 1
                            st.session_state.msg_count = new_val
                            
                            # 更新 Cookie
                            cookie_manager.set("bauki_usage", new_val, key="update_usage")
                            
                            # 稍作等待以确保 Cookie 写入
                            time.sleep(0.5)
                            st.rerun()

                    except Exception as e:
                        st.error(f"Systemfehler: {e}")
    else:
        st.warning("🔒 **Limit erreicht.**")
        st.info("Bitte schalten Sie den Premium-Zugang frei, um fortzufahren.")
else:
    st.info("👋 Bitte API Key eingeben.")

# ==========================================
# 7. 底部 Footer (专业合规)
# ==========================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.markdown("##### Kontakt")
    st.caption("📧 support@bau-ki.de")
    st.caption("📍 Braunschweig, Deutschland")

with col_f2:
    st.markdown("##### Rechtliches")
    with st.expander("Impressum & Datenschutz"):
        st.caption("""
        **Angaben gemäß § 5 TMG**
        Betreiber: M.Sc. Architekt [Ihr Name]
        [Adresse]
        USt-ID: [Nummer]
        
        **Haftung:** Keine Gewähr für Richtigkeit der KI-Antworten.
        """)

with col_f3:
    st.markdown("##### Systemstatus")
    st.caption("🟢 Alle Systeme betriebsbereit")
    st.caption("🤖 Engine: Gemini 2.5 Pro")
