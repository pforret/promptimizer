import streamlit as st
import pandas as pd

from lib.db import get_db, list_invocations, get_invocation, get_stats, update_cost
from lib.openrouter import fetch_cost
from lib.prompts import list_topics


@st.cache_resource
def _db():
    return get_db()


st.header("History")

tab_browse, tab_compare, tab_stats = st.tabs(["Browse", "Compare", "Stats"])

# --- Browse tab ---
with tab_browse:
    # Filters
    col_topic, col_model, col_limit = st.columns(3)
    with col_topic:
        topics = ["All"] + list_topics()
        filter_topic = st.selectbox("Topic", topics, key="hist_topic")
    with col_model:
        filter_model = st.text_input("Model filter", key="hist_model", placeholder="e.g. anthropic/")
    with col_limit:
        limit = st.number_input("Limit", 10, 500, 50, key="hist_limit")

    invocations = list_invocations(
        _db(),
        prompt_topic=filter_topic if filter_topic != "All" else None,
        model_id=filter_model or None,
        limit=limit,
    )

    if not invocations:
        st.info("No invocations yet. Run a prompt first.")
    else:
        # Summary table
        df = pd.DataFrame(invocations)
        display_cols = ["id", "created_at", "prompt_topic", "prompt_name", "model_id",
                        "temperature", "total_tokens", "cost_usd", "latency_ms", "status"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], width="stretch", hide_index=True)

        # Detail view
        st.divider()
        inv_id = st.number_input("View invocation #", min_value=1, step=1, key="hist_view_id")
        if st.button("Show details"):
            inv = get_invocation(_db(), inv_id)
            if not inv:
                st.error(f"Invocation #{inv_id} not found.")
            else:
                # Lazy cost fetch
                if inv.get("cost_usd") is None and inv.get("generation_id"):
                    with st.spinner("Fetching cost..."):
                        cost = fetch_cost(inv["generation_id"])
                    if cost is not None:
                        update_cost(_db(), inv_id, cost)
                        inv["cost_usd"] = cost

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Prompt tokens", inv.get("prompt_tokens", "?"))
                c2.metric("Completion tokens", inv.get("completion_tokens", "?"))
                cost_str = f"${inv['cost_usd']:.6f}" if inv.get("cost_usd") else "pending"
                c3.metric("Cost", cost_str)
                c4.metric("Latency", f"{inv.get('latency_ms', '?')} ms")

                st.markdown(f"**Model**: {inv['model_id']} | **Temp**: {inv.get('temperature')} | **Version**: {inv.get('prompt_version')}")

                with st.expander("Full prompt", expanded=False):
                    st.code(inv.get("full_prompt", ""), language="markdown")

                with st.expander("Full response", expanded=True):
                    st.markdown(inv.get("full_response", "") or "_No response_")

                if inv.get("error_message"):
                    st.error(f"Error: {inv['error_message']}")

# --- Compare tab ---
with tab_compare:
    st.subheader("Side-by-side comparison")
    c1, c2 = st.columns(2)
    with c1:
        id1 = st.number_input("Invocation A", min_value=1, step=1, key="cmp_id1")
    with c2:
        id2 = st.number_input("Invocation B", min_value=1, step=1, key="cmp_id2")

    if st.button("Compare", type="primary"):
        inv_a = get_invocation(_db(), id1)
        inv_b = get_invocation(_db(), id2)

        if not inv_a:
            st.error(f"Invocation #{id1} not found.")
        elif not inv_b:
            st.error(f"Invocation #{id2} not found.")
        else:
            col_a, col_b = st.columns(2)
            for col, inv, label in [(col_a, inv_a, "A"), (col_b, inv_b, "B")]:
                with col:
                    st.subheader(f"#{inv['id']} ({label})")
                    st.markdown(f"**Model**: {inv['model_id']}")
                    st.markdown(f"**Temp**: {inv.get('temperature')} | **Tokens**: {inv.get('total_tokens')}")
                    cost_str = f"${inv['cost_usd']:.6f}" if inv.get("cost_usd") else "pending"
                    st.markdown(f"**Cost**: {cost_str} | **Latency**: {inv.get('latency_ms')} ms")
                    st.divider()
                    st.markdown(inv.get("full_response", "") or "_No response_")

# --- Stats tab ---
with tab_stats:
    stats = get_stats(_db())
    if stats["total_runs"] == 0:
        st.info("No data yet.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total runs", stats["total_runs"])
        cost = stats["total_cost"]
        c2.metric("Total cost", f"${cost:.4f}" if cost else "$0")
        tokens = stats["total_tokens"]
        c3.metric("Total tokens", f"{tokens:,}" if tokens else "0")
        c4.metric("Unique models", stats["unique_models"])
