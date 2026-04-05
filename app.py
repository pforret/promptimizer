import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Promptimizer",
    page_icon=":material/psychology:",
    layout="wide",
)

pg = st.navigation([
    st.Page("pages/run.py", title="Run Prompt", icon=":material/play_arrow:", default=True),
    st.Page("pages/prompts.py", title="Prompts", icon=":material/edit_note:"),
    st.Page("pages/history.py", title="History", icon=":material/history:"),
    st.Page("pages/models.py", title="Models", icon=":material/smart_toy:"),
    st.Page("pages/export.py", title="Export", icon=":material/download:"),
])

pg.run()
