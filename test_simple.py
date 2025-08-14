# -*- coding: utf-8 -*-
"""
Simple test application to verify environment setup.
"""

import streamlit as st

st.set_page_config(
    page_title="Sky Globe Test",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Sky Globe - Test Application")
st.write("This is a simple test to verify the environment is working correctly.")

st.success("✅ Streamlit is working!")
st.info("📝 Next step: Configure API keys and test full application")

# Test basic functionality
if st.button("Test Button"):
    st.balloons()
    st.write("Button works!")

st.sidebar.title("Test Sidebar")
st.sidebar.write("Sidebar is working!")