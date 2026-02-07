import streamlit as st
import google.generativeai as genai
import stripe  # 引入 Stripe 查账工具
from datetime import datetime, timedelta

# --- 1. 页面配置 ---
st.set_page_config(page_title="BauAI: Ihr digitaler Architekt", page_icon="🏗️")

# --- 2. 初始化状态 ---
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

# --- 3. 侧边栏 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### Mein Status")

    # 配置 Google Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Admin Key", type="password")

    # 配置 Stripe Key
    if "STRIPE_API_KEY" in st.secrets:
        stripe.api_key = st.secrets["STRIPE_API_KEY"]

    st.markdown("---")

    # --- 状态显示逻辑 ---
    if st.session_state.is_premium:
        st.success("💎 Premium Aktiv")
        st.caption("Vielen Dank für Ihre Unterstützung!")
    else:
        left = 3 - st.session_state.msg_count
        if left > 0:
            st.info(f"Kostenlose Fragen: {left} / 3")
            st.progress((3 - left) / 3)
        else:
            st.error("Limit erreicht (0/3)")
            # 这里放你的 Stripe 购买链接
            st.link_button("👉 24h Pass kaufen (1,99€)", "https://buy.stripe.com/你的链接")
            st.caption("Sie erhalten sofort eine Order-ID.")

    st.markdown("---")

    # --- 【核心升级】Stripe 自动查账系统 ---
    with st.expander("🔓 Order-ID eingeben"):
        # 用户输入他在 Stripe 看到的 Session ID (格式通常是 cs_live_...)
        order_id = st.text_input("Bestellnummer (cs_...):", placeholder="cs_live_...", label_visibility="collapsed")
        
        if st.button("Aktivieren"):
            if not order_id.startswith("cs_"):
                st.error("Ungültiges Format. ID muss mit 'cs_' beginnen.")
            else:
                try:
                    # 1. 呼叫 Stripe 服务器查账
                    session = stripe.checkout.Session.retrieve(order_id)
                    
                    # 2. 检查是否已付款
                    if session.payment_status == 'paid':
                        # 3. 获取付款时间 (Unix Timestamp)
                        payment_time = datetime.fromtimestamp(session.created)
                        now = datetime.now()
                        
                        # 4. 计算是否过期 (例如 24 小时)
                        if now - payment_time < timedelta(hours=24):
                            st.session_state.is_premium = True
                            st.balloons()
                            st.success("Zahlung bestätigt! Premium aktiviert.")
                            st.rerun()
                        else:
                            st.error("Dieser Code ist abgelaufen (älter als 24h).")
                    else:
                        st.error("Zahlung noch nicht abgeschlossen.")
                        
                except Exception as e:
                    # 如果 ID 输错了，Stripe 会报错
                    st.error("ID nicht gefunden. Bitte prüfen Sie die Eingabe.")
