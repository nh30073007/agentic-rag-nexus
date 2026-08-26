import streamlit as st

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

st.title("Main Content")

with st.sidebar:
    st.header("✅ Sidebar Working!")
    st.write("If you see this, sidebar is working.")

st.write("Main content area")