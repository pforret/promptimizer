import json
import re

import streamlit as st

from lib.db import get_db, list_invocations, get_invocation, get_stats, update_cost, delete_invocation
from lib.openrouter import fetch_cost
from lib.prompts import list_topics


@st.cache_resource
def _db():
    return get_db()


def _parse_items(response: str) -> list[dict] | None:
    """Extract the first list-of-dicts from a JSON response."""
    if not response:
        return None
    m = re.search(r"```json?\s*\n(.*?)```", response, re.DOTALL)
    text = m.group(1) if m else response
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, AttributeError):
        return None
    # If top-level is a list, use it directly
    if isinstance(data, list) and data and isinstance(data[0], dict):
        items = data
    elif isinstance(data, dict):
        # Find first value that is a non-empty list of dicts
        items = None
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                items = v
                break
        if not items:
            return None
    else:
        return None
    # Sort by the first string-valued field (typically name/title/brand)
    label_key = _label_key(items[0])
    return sorted(items, key=lambda x: str(x.get(label_key, "")).lower())


def _label_key(item: dict) -> str:
    """Find the best field to use as display label (first short string field)."""
    for k in ("title", "brand", "name", "label"):
        if k in item:
            return k
    for k, v in item.items():
        if isinstance(v, str) and len(v) < 100:
            return k
    return next(iter(item), "")


def _score_key(item: dict) -> str | None:
    """Find the best numeric field for comparison scoring."""
    for k in ("similarity_score", "score", "cars_sold_europe", "sales", "count", "quantity"):
        if k in item:
            return k
    for k, v in item.items():
        if isinstance(v, (int, float)) and k not in ("year", "introduction_year", "release_year"):
            return k
    return None


def _item_cell(item: dict | None, bg: str, label_key: str, score_key: str | None,
               score_delta: float | None = None) -> str:
    """Return an HTML div for an item cell in the comparison table."""
    style = f"padding:4px 8px;border-radius:4px;margin-bottom:2px;{bg}"
    if item is None:
        return f'<div style="{style}">&nbsp;</div>'
    label = item.get(label_key, "?")
    parts = [f"<b>{label}</b>"]
    # Show a few extra fields inline
    for k, v in item.items():
        if k == label_key or k == "remarks":
            continue
        parts.append(f"{k}: {v}")
        if len(parts) >= 4:
            break
    score_str = ""
    if score_delta is not None and score_delta != 0:
        color = "green" if score_delta > 0 else "crimson"
        sign = "+" if score_delta > 0 else ""
        score_str = f' <span style="color:{color};font-weight:bold">({sign}{score_delta:g})</span>'
    return f'<div style="{style}">{" | ".join(parts)}{score_str}</div>'


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
                if st.checkbox("Compare", key=f"sel_{inv['id']}", label_visibility="collapsed"):
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

                    # Header metrics
                    col_a, col_b = st.columns(2)
                    for col, inv in [(col_a, inv_a), (col_b, inv_b)]:
                        with col:
                            lat = inv.get("latency_ms")
                            st.markdown(f"### #{inv['id']} — `{inv['model_id'].rsplit('/', 1)[-1]}`")
                            st.markdown(
                                f"**Temp**: {inv.get('temperature')} | **Tokens**: {inv.get('total_tokens')} | "
                                f"**CPMI**: {_cpmi(inv.get('cost_usd'))} | **Latency**: {f'{lat / 1000:.1f}s' if lat else '?'}"
                            )

                    st.divider()

                    items_a = _parse_items(inv_a.get("full_response", ""))
                    items_b = _parse_items(inv_b.get("full_response", ""))

                    if items_a is not None or items_b is not None:
                        sample = (items_a or items_b)[0]
                        lk = _label_key(sample)
                        sk = _score_key(sample)
                        dict_a = {str(m.get(lk, "")).lower(): m for m in (items_a or [])}
                        dict_b = {str(m.get(lk, "")).lower(): m for m in (items_b or [])}
                        all_keys = sorted(set(dict_a) | set(dict_b))

                        for item_key in all_keys:
                            m_a = dict_a.get(item_key)
                            m_b = dict_b.get(item_key)

                            bg_a = bg_b = ""
                            score_delta = None
                            if m_a and m_b:
                                if sk:
                                    try:
                                        score_delta = round(
                                            float(m_b.get(sk, 0)) - float(m_a.get(sk, 0)), 2
                                        )
                                    except (TypeError, ValueError):
                                        pass
                            elif m_a and not m_b:
                                bg_a = "background-color:#ffe0e0;"
                            elif m_b and not m_a:
                                bg_b = "background-color:#e0ffe0;"

                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(_item_cell(m_a, bg_a, lk, sk), unsafe_allow_html=True)
                            with col_b:
                                st.markdown(_item_cell(m_b, bg_b, lk, sk, score_delta), unsafe_allow_html=True)
                    else:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(inv_a.get("full_response", "") or "_No response_")
                        with col_b:
                            st.markdown(inv_b.get("full_response", "") or "_No response_")
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
