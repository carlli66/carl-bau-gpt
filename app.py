import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Carl的AI建筑顾问", page_icon="🏗️")
st.title("🏗️ 德国建筑师 Carl 的 AI 助手 (V1.0)")

# 侧边栏
with st.sidebar:
    api_key = st.text_input("请输入 Google API Key", type="password")
    st.info("💡 如果模型报错，请尝试重启 App。")

# 主逻辑
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # 使用最经典的 gemini-pro 模型，兼容性最好
        model = genai.GenerativeModel("gemini-pro")
        
        # 简单的文件上传
        uploaded_file = st.file_uploader("上传图片 (如有)", type=["jpg", "png", "jpeg"])
        
        # 简单的聊天
        user_input = st.chat_input("输入你的问题...")

        if user_input:
            st.chat_message("user").write(user_input)
            
            with st.chat_message("assistant"):
                with st.spinner("AI 正在思考..."):
                    # 这里的 Prompt 稍微改写一下，把角色设定直接加在问题里
                    full_prompt = f"你是一名德国资深建筑师。请回答以下问题：{user_input}"
                    
                    response = model.generate_content(full_prompt)
                    st.write(response.text)
                    
    except Exception as e:
        st.error(f"发生错误: {e}")
else:
    st.warning("👈 请先在左侧输入 API Key")
