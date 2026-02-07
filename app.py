import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 页面设置
st.set_page_config(page_title="Carl的AI建筑顾问", page_icon="🏗️")

st.title("🏗️ 德国建筑师 Carl 的 AI 助手")
st.write("专注德国老房翻新、法规咨询与图纸初审。")

# 2. 侧边栏设置
with st.sidebar:
    st.header("🔑 启动钥匙")
    # 为了安全，不要把 Key 写在代码里，而是让用户（也就是你）输入
    api_key = st.text_input("请输入 Google API Key", type="password")
    st.markdown("---")
    st.write("👨‍💻 由 Carl 开发")
    st.write("我们需要查看您的图纸吗？请在右侧上传。")

# 3. 主逻辑
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # 定义 AI 角色
        system_instruction = """
        你是德国下萨克森州的资深建筑师。
        你精通 NBauO (Niedersächsische Bauordnung) 和 HOAI。
        如果用户上传了图片，请从建筑师的专业角度分析（如：无障碍设计、防火、空间布局）。
        回答要简洁、专业，并以此为契机推荐 Carl 的付费咨询服务。
        """
        model = genai.GenerativeModel("gemini-pro")

        # 文件上传区
        uploaded_file = st.file_uploader("上传平面图或现场照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])
        
        image_part = None
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="已上传的图纸/照片", use_column_width=True)
            image_part = image

        # 聊天输入
        user_input = st.chat_input("输入你的问题（例如：这张图纸符合轮椅通行标准吗？）")

        if user_input:
            # 显示用户问题
            with st.chat_message("user"):
                st.write(user_input)

            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("Carl 的 AI 正在思考中..."):
                    if image_part:
                        # 有图模式
                        response = model.generate_content([user_input, image_part])
                    else:
                        # 纯文字模式
                        response = model.generate_content(user_input)
                    
                    st.write(response.text)

    except Exception as e:
        st.error(f"发生错误，请检查 API Key 是否正确。错误信息: {e}")

else:
    st.info("👈 请在左侧侧边栏输入 API Key 以启动服务。")
