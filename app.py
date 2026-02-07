import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. 核心配置
# ==========================================
PREMIUM_CODE = "BAU2026"  # 解锁密码
STRIPE_LINK = "https://buy.stripe.com/你的链接" # Stripe 链接

# ==========================================
# 2. 页面配置
# ==========================================
st.set_page_config(page_title="DE-BauKI Expert", page_icon="🏗️", layout="centered")

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

    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key", type="password")

    st.markdown("---")

    if st.session_state.is_premium:
        st.success("👑 **Premium Aktiv**")
        st.caption("Modell: Gemini 2.5 Pro (Latest)")
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
            st.link_button("👉 Jetzt freischalten (4,99€)", STRIPE_LINK)
            
        st.markdown("---")
        with st.expander("🎫 Code eingeben", expanded=True):
            user_code = st.text_input("Zugangscode:", type="password")
            if st.button("Prüfen"):
                if user_code == PREMIUM_CODE:
                    st.session_state.is_premium = True
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Falscher Code.")

# ==========================================
# 4. AI 智能调用函数 (已更新为您的可用模型)
# ==========================================
def get_ai_response(api_key, prompt, image=None):
    genai.configure(api_key=api_key)
    
    # ★★★ 关键修改：使用了您列表里存在的模型 ★★★
    # 优先用 2.5 Pro (最强)，如果不行用 2.5 Flash (最快)
    model_priority = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
    
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
            continue # 尝试下一个模型
    
    # 如果所有模型都失败
    raise last_error

# ==========================================
# 5. 主界面
# ==========================================
st.title("🏗️ DE-BauKI Expert")
st.markdown("Ihr KI-Architekt für Baurecht, Sanierung & Kosten (Powered by Gemini 2.5).")

col1, col2, col3 = st.columns(3)
with col1: st.markdown('<div style="text-align:center">⚖️<br><small>Baurecht</small></div>', unsafe_allow_html=True)
with col2: st.markdown('<div style="text-align:center">🔨<br><small>Technik</small></div>', unsafe_allow_html=True)
with col3: st.markdown('<div style="text-align:center">💶<br><small>Kosten</small></div>', unsafe_allow_html=True)

st.divider()

# 显示历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理输入
if api_key:
    can_ask = st.session_state.is_premium or (st.session_state.msg_count < 3)

    if can_ask:
        with st.expander("📎 Datei hochladen (Optional)"):
            uploaded_file = st.file_uploader("Bild/PDF", type=["jpg", "png", "jpeg", "pdf"])

        if prompt := st.chat_input("Frage stellen..."):
            
            # 显示用户问题
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file:
                    st.image(uploaded_file, width=200)

            # AI 回答
            with st.chat_message("assistant"):
                with st.spinner("Bau-KI denkt nach (Gemini 2.5)..."):
                    try:
                        # 准备图片
                        img_obj = Image.open(uploaded_file) if uploaded_file else None
                        
                        # 构造 Prompt
                        sys_prompt = "Du bist ein deutscher Bau-Experte. Antworte präzise auf Deutsch."
                        full_prompt = sys_prompt + "\n\nFrage: " + prompt

                        # 调用 AI
                        ans_text = get_ai_response(api_key, full_prompt, img_obj)
                        
                        # 显示并保存
                        st.markdown(ans_text)
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})

                        # 扣费
                        if not st.session_state.is_premium:
                            st.session_state.msg_count += 1
                            st.rerun()

                    except Exception as e:
                        st.error(f"Ein Fehler ist aufgetreten: {e}")
                        st.info("Falls das Problem weiterhin besteht, prüfen Sie Ihren API Key.")
    else:
        st.warning("🔒 Limit erreicht.")
        st.caption("Bitte Code eingeben (siehe Sidebar).")
else:
    st.warning("Bitte Google API Key in der Sidebar eingeben.")
