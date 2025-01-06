page = st.sidebar.radio("Navigation", ["Main Dashboard", "Device Analysis", "Test Analysis"])

if page == "Device Analysis":
    switch_page("device_analysis")
elif page == "Test Analysis":
    switch_page("test_analysis") 