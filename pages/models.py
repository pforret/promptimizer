import streamlit as st
import pandas as pd

from lib.openrouter import list_models


@st.cache_data(ttl=3600)
def _fetch_models():
    return list_models()


st.header("Models")

models = _fetch_models()

if not models:
    st.warning("Could not fetch models from OpenRouter. Check your network connection.")
    if st.button("Retry"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

st.caption(f"{len(models)} models available")

# Search
search = st.text_input("Search models", placeholder="e.g. claude, gpt, gemini, llama")

filtered = models
if search:
    q = search.lower()
    filtered = [m for m in models if q in m["id"].lower() or q in m["name"].lower()]

if not filtered:
    st.info("No models match your search.")
    st.stop()

# Convert pricing to readable format
for m in filtered:
    try:
        prompt_price = float(m["pricing_prompt"]) * 1_000_000
        completion_price = float(m["pricing_completion"]) * 1_000_000
        m["prompt_$/M"] = f"${prompt_price:.2f}" if prompt_price > 0 else "free"
        m["completion_$/M"] = f"${completion_price:.2f}" if completion_price > 0 else "free"
    except (ValueError, TypeError):
        m["prompt_$/M"] = "?"
        m["completion_$/M"] = "?"

df = pd.DataFrame(filtered)
display_cols = ["id", "name", "context_length", "prompt_$/M", "completion_$/M"]
available = [c for c in display_cols if c in df.columns]

st.dataframe(df[available], width="stretch", hide_index=True)
