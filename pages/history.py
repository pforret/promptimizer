import json
import re

import streamlit as st

from lib.db import get_db, list_invocations, get_invocation, get_stats, update_cost, delete_invocation
from lib.openrouter import fetch_cost
from lib.prompts import list_topics


@st.cache_resource
def _db():
    return get_db()


def _parse_movies(response: str) -> list[dict] | None:
    """Try to extract comparable_movies list from JSON response."""
    if not response:
        return None
    # Extract JSON block from markdown code fence or raw text
    m = re.search(r"```json?\s*\n(.*?)```", response, re.DOTALL)
    text = m.group(1) if m else response
    try:
        data = json.loads(text)
        movies = data.get("comparable_movies") if isinstance(data, dict) else None
        if isinstance(movies, list) and movies:
            return sorted(movies, key=lambda x: x.get("title", "").lower())
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def _cpmi(cost_usd) -> str:
    """Format cost as CPMI (Cost Per Mille Inferences = cost * 1000)."""
    if cost_usd:
        return f"${cost_usd * 1000:.2f}/1Ki"
    return "pending"


st.header("History")

tab_browse, tab_stats = st.tabs(["Browse", "Stats"])

# --- Browse tab ---
with tab_browse:
    # Filters
    col_topic, col_name, col_model, col_limit = st.columns(4)
    with col_topic:
        topics = ["All"] + list_topics()
        filter_topic = st.selectbox("Topic", topics, key="hist_topic")
    with col_name:
        filter_name = st.text_input("Prompt name", key="hist_name", placeholder="e.g. beautiful")
    with col_model:
        filter_model = st.text_input("Model filter", key="hist_model", placeholder="e.g. anthropic/")
    with col_limit:
        limit = st.number_input("Limit", 10, 500, 50, key="hist_limit")

    invocations = list_invocations(
        _db(),
        prompt_topic=filter_topic if filter_topic != "All" else None,
        prompt_name=filter_name or None,
        model_id=filter_model or None,
        limit=limit,
    )

    if not invocations:
        st.info("No invocations yet. Run a prompt first.")
    else:
        selected_ids = []
        for inv in invocations:
            model_short = inv["model_id"].rsplit("/", 1)[-1]
            failed = inv.get("status") != "success" or not inv.get("full_response")
            icon = ":red_circle:" if failed else ""
            latency_ms = inv.get("latency_ms")
            latency_str = f"{latency_ms / 1000:.1f}s" if latency_ms else "?s"
            label = (
                f"{icon}  #{inv['id']}  {inv['created_at']}  —  "
                f"**{inv['prompt_topic']}/{inv['prompt_name']}**  |  "
                f"`{model_short}`  |  {_cpmi(inv.get('cost_usd'))}  |  {latency_str}"
            )

            col_check, col_exp = st.columns([0.05, 0.95])
            with col_check:
                if st.checkbox("", key=f"sel_{inv['id']}", label_visibility="collapsed"):
                    selected_ids.append(inv["id"])
            with col_exp:
                with st.expander(label):
                    # Lazy cost fetch
                    if inv.get("cost_usd") is None and inv.get("generation_id"):
                        with st.spinner("Fetching cost..."):
                            cost = fetch_cost(inv["generation_id"])
                        if cost is not None:
                            update_cost(_db(), inv["id"], cost)
                            inv["cost_usd"] = cost

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Prompt tokens", inv.get("prompt_tokens", "?"))
                    c2.metric("Completion tokens", inv.get("completion_tokens", "?"))
                    c3.metric("CPMI", _cpmi(inv.get("cost_usd")))
                    latency = inv.get("latency_ms")
                    c4.metric("Latency", f"{latency / 1000:.1f}s" if latency else "?")

                    st.markdown(f"**Model**: {inv['model_id']} | **Temp**: {inv.get('temperature')} | **Version**: {inv.get('prompt_version')}")

                    with st.container():
                        st.markdown("**Prompt**")
                        st.code(inv.get("full_prompt", ""), language="markdown")

                    with st.container():
                        st.markdown("**Response**")
                        st.markdown(inv.get("full_response", "") or "_No response_")

                    if inv.get("error_message"):
                        st.error(f"Error: {inv['error_message']}")

                    if st.button("Delete", key=f"del_{inv['id']}", type="secondary"):
                        delete_invocation(_db(), inv["id"])
                        st.rerun()

        if len(selected_ids) == 2:
            if st.button("Compare selected", type="primary"):
                inv_a = get_invocation(_db(), selected_ids[0])
                inv_b = get_invocation(_db(), selected_ids[1])
                if inv_a and inv_b:
                    st.divider()
                    st.subheader("Comparison")
                    col_a, col_b = st.columns(2)
                    for col_idx, (col, inv) in enumerate([(col_a, inv_a), (col_b, inv_b)]):
                        with col:
                            lat = inv.get("latency_ms")
                            st.markdown(f"### #{inv['id']} — `{inv['model_id'].rsplit('/', 1)[-1]}`")
                            st.markdown(f"**Temp**: {inv.get('temperature')} | **Tokens**: {inv.get('total_tokens')} | **CPMI**: {_cpmi(inv.get('cost_usd'))} | **Latency**: {f'{lat / 1000:.1f}s' if lat else '?'}")
                            st.divider()
                            movies = _parse_movies(inv.get("full_response", ""))
                            if movies:
                                for i, movie in enumerate(movies):
                                    title = movie.get("title", "?")
                                    year = str(movie.get("release_year", "")) or movie.get("release_date", "?")[:4]
                                    score = movie.get("similarity_score", "?")
                                    with st.expander(f"**{title}** ({year}): {score}"):
                                        for k, v in movie.items():
                                            if k not in ("title", "release_date", "similarity_score"):
                                                st.markdown(f"- **{k}**: {v}")
                            else:
                                st.markdown(inv.get("full_response", "") or "_No response_")
        elif len(selected_ids) > 2:
            st.warning("Select exactly 2 invocations to compare.")

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
