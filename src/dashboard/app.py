import streamlit as st


st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.title("Nifty 100 Analytics")
st.write("Nifty 100 Financial Intelligence Platform")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "Home",
        "Company Profile",
        "Screener",
        "Peer Comparison",
        "Trend Analysis",
        "Sector Analysis",
        "Capital Allocation",
        "Annual Reports",
    ]
)


if page == "Home":
    st.header("Home")
    st.info("Home dashboard coming next.")

elif page == "Company Profile":
    st.header("Company Profile")
    st.info("Company Profile screen coming next.")

elif page == "Screener":
    st.header("Screener")
    st.info("Screener screen coming next.")

elif page == "Peer Comparison":
    st.header("Peer Comparison")
    st.info("Peer Comparison screen coming next.")

elif page == "Trend Analysis":
    st.header("Trend Analysis")
    st.info("Trend Analysis screen coming next.")

elif page == "Sector Analysis":
    st.header("Sector Analysis")
    st.info("Sector Analysis screen coming next.")

elif page == "Capital Allocation":
    st.header("Capital Allocation")
    st.info("Capital Allocation screen coming next.")

elif page == "Annual Reports":
    st.header("Annual Reports")
    st.info("Annual Reports screen coming next.")