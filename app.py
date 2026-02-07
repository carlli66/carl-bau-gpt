import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. 核心配置
# ==========================================
PREMIUM_CODE = "BAU2026"  
STRIPE_LINK = "https://buy.stripe.com/你的链接" 

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
# 4. AI 智能调用函数 (核心修复)
# ==========================================
def try_generate_content(api_key, prompt, image=None):
    genai.configure(api_key=api_key)
    
    # 备选模型列表：从最新到最老
    # 如果 1.5 都不行，最后会尝试 gemini-pro (1.0版本)
    candidate_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    last_error = None

    for model_name in candidate_models:
        try:
            # 尝试加载模型
            model = genai.GenerativeModel(model_name)
            
            # 准备内容
            content = [prompt]
            if image:
                content.append(image)
                
            # 发送请求
            response = model.generate_content(content)
            
            # 如果成功，返回文本和使用的模型名
            return response.text, model_name
            
        except Exception as e:
            # 记录错误并继续尝试下一个模型
            last_error = e
            continue
    
    # 如果循环结束还没成功，抛出最后的错误
    raise last_error

# ==========================================
# 5. 主界面
# ==========================================
st.title("🏗️ DE-BauKI Expert")
st.markdown("Ihr KI-Architekt für Baurecht, Sanierung & Kosten.")

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
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                if uploaded_file:
                    st.image(uploaded_file, width=200)

            with st.chat_message("assistant"):
                with st.spinner("Bau-KI denkt nach..."):
                    try:
                        # 准备图片对象
                        img_obj = Image.open(uploaded_file) if uploaded_file else None
                        
                        # 构造 Prompt
                        sys_prompt = "Du bist ein deutscher Bau-Experte. Antworte präzise auf Deutsch."
                        full_prompt = sys_prompt + "\n\nFrage: " + prompt

                        #调用我们的智能函数
                        ans_text, used_model = try_generate_content(api_key, full_prompt, img_obj)
                        
                        # 显示回答
                        st.markdown(ans_text)
                        # (可选) 显示到底用了哪个模型，方便调试
                        # st.caption(f"Beantwortet mit Modell: {used_model}")
                        
                        st.session_state.messages.append({"role": "assistant", "content": ans_text})

                        if not st.session_state.is_premium:
                            st.session_state.msg_count += 1
                            st.rerun()

                    except Exception as e:
                        st.error(f"Verbindungsfehler: {e}")
                        # 只有在出错时才显示调试信息
                        st.info("Tipp: Klicken Sie oben rechts auf 'App' -> 'Reboot app'.")
                        
                        # 调试：显示所有可用模型，让你知道到底支持啥
                        try:
                            st.warning("Verfügbare Modelle für diesen API Key:")
                            for m in genai.list_models():
                                if 'generateContent' in m.supported_generation_methods:
                                    st.write(f"- {m.name}")
                        except:
                            pass
    else:
        st.warning("🔒 Limit erreicht.")
else:
    st.warning("Bitte Google API Key eingeben.")
