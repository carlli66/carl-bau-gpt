# --- 3. 侧边栏 (控制台) ---
with st.sidebar:
    # 加一个更友好的 Logo 或标题
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50) 
    st.markdown("### Mein Status") # 改成“我的状态”，比“设置”更亲切
    
    # 【自动读取 Key - 静默模式】
    # 我们删除了 st.success 提示，让它在后台默默工作
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        # 只有在还没配置 Secrets 时才显示输入框（给你自己看的）
        api_key = st.text_input("Admin Key eingeben", type="password")
        st.warning("⚠️ Admin Mode")

    st.markdown("---")
    
    # --- 商业核心区：剩余次数提示 ---
    if st.session_state.is_premium:
        # 付费用户看到的界面
        st.success("💎 Premium Pass Aktiv")
        st.caption("Sie haben 24h unbegrenzten Zugriff.")
    else:
        # 免费用户看到的界面 (制造紧迫感)
        left = 3 - st.session_state.msg_count
        # 用颜色区分：还有次数显示蓝色/绿色，没次数了显示红色
        if left > 0:
            st.info(f"Kostenlose Fragen: {left} / 3")
            st.progress((3 - left) / 3) # 进度条
        else:
            st.error("Limit erreicht (0/3)")
            st.caption("🔒 Bitte upgraden")

    st.markdown("---")
    
    # --- 解锁区域 ---
    with st.expander("🔓 Zugangscode eingeben"):
        code = st.text_input("Code:", placeholder="z.B. BAU2026", label_visibility="collapsed")
        if st.button("Aktivieren"):
            if code == "BAU2026": 
                st.session_state.is_premium = True
                st.rerun() 
            else:
                st.error("Code ungültig")
