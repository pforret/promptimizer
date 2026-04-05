import streamlit as st

from lib.db import get_db, list_invocations
from lib.export import export_invocations, OUTPUT_DIR
from lib.prompts import list_topics


@st.cache_resource
def _db():
    return get_db()


st.header("Export to Markdown")

# Filters
col_topic, col_model, col_limit = st.columns(3)
with col_topic:
    topics = ["All"] + list_topics()
    filter_topic = st.selectbox("Topic", topics, key="exp_topic")
with col_model:
    filter_model = st.text_input("Model filter", key="exp_model")
with col_limit:
    limit = st.number_input("Max invocations", 10, 1000, 100, key="exp_limit")

invocations = list_invocations(
    _db(),
    prompt_topic=filter_topic if filter_topic != "All" else None,
    model_id=filter_model or None,
    limit=limit,
)

st.caption(f"{len(invocations)} invocations matched")

if not invocations:
    st.info("No invocations to export.")
    st.stop()

# Preview
with st.expander("Preview invocations"):
    for inv in invocations[:10]:
        cost_str = f"${inv['cost_usd']:.6f}" if inv.get("cost_usd") else "pending"
        st.markdown(
            f"- **#{inv['id']}** {inv['prompt_topic']}/{inv['prompt_name']} "
            f"| {inv['model_id']} | {cost_str} | {inv['created_at']}"
        )
    if len(invocations) > 10:
        st.caption(f"... and {len(invocations) - 10} more")

# Export
if st.button("Export", type="primary", width="stretch"):
    with st.spinner("Exporting..."):
        files = export_invocations(invocations)

    st.success(f"Exported {len(files)} invocations to `{OUTPUT_DIR}/`")

# Show existing exports
st.divider()
st.subheader("Existing exports")
if OUTPUT_DIR.exists():
    md_files = sorted(OUTPUT_DIR.rglob("*.md"))
    if md_files:
        for f in md_files[:50]:
            st.markdown(f"- `{f.relative_to(OUTPUT_DIR)}`")
        if len(md_files) > 50:
            st.caption(f"... and {len(md_files) - 50} more")
    else:
        st.info("No exports yet.")
else:
    st.info("No exports yet.")
