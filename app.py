import streamlit as st
import google.generativeai as genai

st.title("🕵️‍♂️ 模型侦探 (Model Diagnostic)")

# 1. 输入 Key
api_key = st.text_input("请输入 Google API Key", type="password")

if st.button("🔍 扫描可用模型"):
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.write("正在连接 Google 服务器...")
            
            # 2. 获取所有模型列表
            models = list(genai.list_models())
            
            st.success("连接成功！发现以下模型：")
            
            found_any = False
            for m in models:
                # 只显示能生成内容的模型
                if 'generateContent' in m.supported_generation_methods:
                    st.code(m.name)  # 把这一行名字复制下来
                    found_any = True
            
            if not found_any:
                st.warning("连接成功，但没有发现支持 'generateContent' 的模型。可能是区域限制。")
                
        except Exception as e:
            st.error(f"发生错误: {e}")
    else:
        st.warning("请先输入 API Key")
