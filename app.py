import streamlit as st
from duckduckgo_search import DDGS
from google import genai

# --- MENGAMBIL API KEY SECARA OTOMATIS ---
api_key = st.secrets["GEMINI_API_KEY"]

# --- KONFIGURASI ANTARMUKA (UI) ---
st.set_page_config(page_title="Generator Weekly Report Banten", page_icon="📰", layout="wide")

st.markdown("""
    <style>
    .stMarkdown p, .stMarkdown a {
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: pre-wrap;
    }
    div.stButton > button {
        background-color: #1E3A8A;
