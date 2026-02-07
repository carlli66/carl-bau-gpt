import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 页面设置
st.set_page_config(page_title="Carl的AI建筑顾问", page_icon="🏗️")
st.title("🏗️ 德国建筑师 Carl 的 AI 助手")
st.caption("基于 Gemini Flash (Stable) | 专精下萨克森州建筑法")

# 2. 侧边栏
with st.sidebar:
    st.header("🔑 启动设置")
    api_key = st.text_input("请输入 Google API Key", type="password")
    st.info("💡 这是一个 MVP 原型。如果遇到问题，请尝试刷新页面。")

# 3. 主逻辑
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # --- 关键修改：使用通用通行证别名 ---
        # 这个名字在你的白名单里，一定能用！
        model_name = "models/gemini-flash-latest"
        # --------------------------------

        # 简单的系统指令
        sys_instruction = """
        你是一名德国下萨克森州的资深注册建筑师。
        回答要专业、引用法规(NBauO)，并最后推荐 Carl 的付费咨询。
        """
        
        # 初始化模型
        model = genai.GenerativeModel(model_name, system_instruction=sys_instruction)

        # 界面：文件上传
        uploaded_file = st.file_uploader("上传平面图 (可选)", type=["jpg", "png", "jpeg"])
        
        image_part = None
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="已上传图纸", use_column_width=True)
            image_part = image

        # 界面：聊天
        user_input = st.chat_input("输入你的问题...")

        if user_input:
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("正在查阅法规..."):
                    try:
                        if image_part:
                            response = model.generate_content([user_input, image_part])
                        else:
                            response = model.generate_content(user_input)
                        
                        st.write(response.text)
                    
                    except Exception as e:
                        st.error(f"连接出错: {e}")

    except Exception as e:
        st.error(f"API Key 设置有误: {e}")

else:
    st.warning("👈 请先在左侧输入 API Key")
