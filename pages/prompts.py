import streamlit as st

from lib.prompts import (
    list_topics,
    list_prompts,
    read_prompt,
    write_prompt,
    delete_prompt,
    parse_frontmatter,
    extract_variables,
    prompt_version,
)

st.header("Prompts")

tab_list, tab_create = st.tabs(["Browse", "Create"])

# --- Browse tab ---
with tab_list:
    topics = list_topics()
    if not topics:
        st.info("No prompts yet. Use the Create tab to add one.")
    else:
        for topic in topics:
            with st.expander(f"**{topic}**", expanded=True):
                prompts = list_prompts(topic)
                for p in prompts:
                    col_name, col_ver, col_actions = st.columns([3, 1, 2])
                    try:
                        content = read_prompt(p["topic"], p["name"])
                        meta, body = parse_frontmatter(content)
                        ver = prompt_version(content)
                        variables = extract_variables(body)
                    except FileNotFoundError:
                        continue

                    with col_name:
                        desc = meta.get("description", "")
                        st.markdown(f"**{p['name']}**")
                        if desc:
                            st.caption(desc)
                        if variables:
                            st.caption(f"Variables: {', '.join(variables)}")

                    with col_ver:
                        st.code(ver, language=None)

                    with col_actions:
                        btn_key = f"edit_{topic}_{p['name']}"
                        del_key = f"del_{topic}_{p['name']}"
                        if st.button("Edit", key=btn_key):
                            st.session_state["edit_topic"] = topic
                            st.session_state["edit_name"] = p["name"]
                            st.session_state["edit_content"] = content
                            st.rerun()
                        if st.button("Delete", key=del_key):
                            delete_prompt(topic, p["name"])
                            st.success(f"Deleted {topic}/{p['name']}")
                            st.rerun()

    # Edit form (shown when edit button clicked)
    if "edit_content" in st.session_state:
        st.divider()
        st.subheader(f"Edit: {st.session_state['edit_topic']}/{st.session_state['edit_name']}")
        edited = st.text_area(
            "Content",
            value=st.session_state["edit_content"],
            height=400,
            key="edit_area",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save", type="primary"):
                write_prompt(st.session_state["edit_topic"], st.session_state["edit_name"], edited)
                del st.session_state["edit_content"]
                del st.session_state["edit_topic"]
                del st.session_state["edit_name"]
                st.success("Saved!")
                st.rerun()
        with c2:
            if st.button("Cancel"):
                del st.session_state["edit_content"]
                del st.session_state["edit_topic"]
                del st.session_state["edit_name"]
                st.rerun()

# --- Create tab ---
with tab_create:
    st.subheader("Create new prompt")
    new_topic = st.text_input("Topic", placeholder="e.g. office, coding, analysis")
    new_name = st.text_input("Name", placeholder="e.g. generate_meeting_report")

    template = """---
description:
model: openai/gpt-4o
temperature: 0.7
system:
---
Your prompt here. Use {{variable_name}} for template variables.
"""
    new_content = st.text_area("Content", value=template, height=400, key="create_content")

    if st.button("Create", type="primary"):
        if not new_topic or not new_name:
            st.error("Topic and name are required.")
        else:
            # Check if exists
            try:
                read_prompt(new_topic, new_name)
                st.error(f"Prompt `{new_topic}/{new_name}` already exists.")
            except FileNotFoundError:
                write_prompt(new_topic, new_name, new_content)
                st.success(f"Created `{new_topic}/{new_name}`")
                st.rerun()
