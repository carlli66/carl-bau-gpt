import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 页面配置
st.set_page_config(page_title="Carl的AI建筑顾问", page_icon="🏗️")
st.title("🏗️ 德国建筑师 Carl 的 AI 助手")
st.caption("基于 Gemini 2.0 Flash Lite | 专精下萨克森州建筑法")

# 2. 侧边栏
with st.sidebar:
    st.header("🔑 启动设置")
    api_key = st.text_input("请输入 Google API Key", type="password")
    st.markdown("---")
    st.info("💡 提示：这是一个 MVP 原型。如果遇到报错，请稍等 1 分钟再试。")

# 3. 主逻辑
if api_key:
    try:
        # 配置 API
        genai.configure(api_key=api_key)
        
        # --- 核心修改：使用你列表里最稳的 Lite 模型 ---
        model_name = "models/gemini-2.0-flash-lite-001" 
        # -------------------------------------------

        # 定义建筑师人设
        sys_instruction = """
        你是一名德国下萨克森州（Niedersachsen）的资深注册建筑师。
        你的任务是帮助用户分析装修、扩建和法规问题。
        
        回答规则：
        1. 引用 NBauO (Niedersächsische Bauordnung) 相关条款。
        2. 语气专业、客观，像在写一封咨询邮件。
        3. 如果涉及结构安全，必须提示“请咨询结构工程师(Statiker)”。
        4. 在结尾委婉推荐：'如需更详细的图纸预审，请预约 Carl 的付费咨询。'
        """
        
        # 启动模型
        model = genai.GenerativeModel(model_name, system_instruction=sys_instruction)

        # 界面：文件上传
        uploaded_file = st.file_uploader("上传平面图或现场照片 (可选)", type=["jpg", "png", "jpeg"])
        
        image_part = None
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="已上传图纸", use_column_width=True)
            image_part = image

        # 界面：聊天输入
        user_input = st.chat_input("输入你的问题（例如：加盖Wintergarten需要审批吗？）")

        if user_input:
            # 显示用户的问题
            with st.chat_message("user"):
                st.write(user_input)

            # 生成回答
            with st.chat_message("assistant"):
                with st.spinner("Carl 的 AI 正在查阅法规库..."):
                    try:
                        if image_part:
                            # 视觉模式
                            response = model.generate_content([user_input, image_part])
                        else:
                            # 纯文本模式
                            response = model.generate_content(user_input)
                        
                        st.write(response.text)
                    
                    except Exception as e:
                        # 如果还报错，显示友好的提示
                        st.error(f"连接繁忙，请稍等几秒再试。错误信息: {e}")

    except Exception as e:
        st.error(f"API Key 似乎有问题: {e}")

else:
    st.warning("👈 请先在左侧输入 API Key 才能开始咨询。")
