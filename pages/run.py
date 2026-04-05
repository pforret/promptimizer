import base64
import os
import time

import streamlit as st

from lib.db import get_db, insert_invocation
from lib.openrouter import (
    default_model,
    configured_models,
    send_prompt_stream,
    AuthenticationError,
    RateLimitError,
    APIError,
)
from lib.prompts import (
    list_topics,
    list_prompts,
    read_prompt,
    parse_frontmatter,
    extract_variables,
    render_template,
    prompt_version,
)


@st.cache_resource
def _db():
    return get_db()


st.header("Run Prompt")

# Check API key
if not os.environ.get("OPENROUTER_API_KEY"):
    st.error("Missing `OPENROUTER_API_KEY`. Add it to your `.env` file and restart.")
    st.stop()

# --- Prompt selection ---
topics = list_topics()
if not topics:
    st.warning("No prompts found in `input/prompts/`. Create some on the Prompts page first.")
    st.stop()

col_topic, col_name = st.columns(2)
with col_topic:
    topic = st.selectbox("Topic", topics, key="run_topic")
with col_name:
    prompts = list_prompts(topic)
    prompt_names = [p["name"] for p in prompts]
    if not prompt_names:
        st.warning(f"No prompts in topic `{topic}`.")
        st.stop()
    name = st.selectbox("Prompt", prompt_names, key="run_prompt")

# Load prompt and parse frontmatter
raw_content = read_prompt(topic, name)
meta, body = parse_frontmatter(raw_content)

# --- Sidebar config (pre-filled from frontmatter) ---
with st.sidebar:
    st.subheader("Configuration")

    uploaded = st.file_uploader("Attach media", type=["png", "jpg", "jpeg", "webp", "gif"], key="run_media")
    has_media = uploaded is not None

    # Build labeled model list from config, grouped by category
    _SEP = " :: "
    labeled_options: list[str] = []
    if has_media:
        categories = [("VIDEO", "video"), ("IMAGE", "vision")]
    else:
        categories = [("TEXT", "text"), ("IMAGE", "vision"), ("VIDEO", "video")]
    for label, cat in categories:
        for m in configured_models(cat):
            labeled_options.append(f"[{label}]{_SEP}{m}")

    fm_model = meta.get("model", default_model(has_media))
    # Ensure frontmatter model is in the list
    fm_labeled = None
    for opt in labeled_options:
        if opt.split(_SEP, 1)[1] == fm_model:
            fm_labeled = opt
            break
    if fm_labeled is None:
        fm_labeled = f"[CUSTOM]{_SEP}{fm_model}"
        labeled_options.insert(0, fm_labeled)

    default_idx = labeled_options.index(fm_labeled)
    selected = st.selectbox("Model", labeled_options, index=default_idx, key="run_model")
    model = selected.split(_SEP, 1)[1]

    fm_temp = meta.get("temperature", 0.7)
    temperature = st.slider("Temperature", 0.0, 2.0, float(fm_temp), step=0.1, key="run_temp")

    fm_max = meta.get("max_tokens", 4096)
    max_tokens = st.number_input("Max tokens", 100, 128000, int(fm_max), key="run_max_tokens")

    fm_format = meta.get("response_format", "text")
    format_options = ["text", "json_object", "json_schema"]
    response_format_choice = st.selectbox(
        "Response format", format_options,
        index=format_options.index(fm_format) if fm_format in format_options else 0,
        key="run_format",
    )

    json_schema_text = None
    if response_format_choice == "json_schema":
        json_schema_text = st.text_area("JSON Schema", height=150, key="run_schema")

# --- Show prompt body (read-only) ---
st.subheader("Prompt")
if meta.get("description"):
    st.caption(meta["description"])
if meta.get("system"):
    st.info(f"**System**: {meta['system']}")

st.code(body, language="markdown")

# --- Variable inputs ---
variables = extract_variables(body)
var_values: dict[str, str] = {}
if variables:
    st.subheader("Variables")
    for var in variables:
        var_values[var] = st.text_area(f"`{{{{{var}}}}}`", key=f"var_{var}", height=100)

# --- Media preview ---
if uploaded:
    st.image(uploaded, caption=uploaded.name, width=300)

# --- Run button ---
if st.button("Run", type="primary", width="stretch"):
    # Substitute variables
    rendered_body = render_template(body, var_values)

    # Build messages
    messages: list[dict] = []
    if meta.get("system"):
        messages.append({"role": "system", "content": meta["system"]})

    if uploaded:
        media_bytes = uploaded.getvalue()
        b64 = base64.b64encode(media_bytes).decode()
        mime = uploaded.type or "image/png"
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": rendered_body},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        })
    else:
        messages.append({"role": "user", "content": rendered_body})

    # Build response_format param
    rf_param = None
    if response_format_choice == "json_object":
        rf_param = {"type": "json_object"}
    elif response_format_choice == "json_schema" and json_schema_text:
        import json
        try:
            schema = json.loads(json_schema_text)
            rf_param = {
                "type": "json_schema",
                "json_schema": {"name": "output", "strict": True, "schema": schema},
            }
        except json.JSONDecodeError:
            st.error("Invalid JSON schema.")
            st.stop()

    # Stream response
    version = prompt_version(rendered_body)
    start_time = time.time()
    state = {"full_response": "", "response_id": None, "usage": {}}

    try:
        def stream_gen():
            for event in send_prompt_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=rf_param,
            ):
                if event["type"] == "delta":
                    state["full_response"] += event["content"]
                    yield event["content"]
                elif event["type"] == "done":
                    state["response_id"] = event.get("response_id")
                    state["usage"] = event.get("usage", {})

        st.subheader("Response")
        st.write_stream(stream_gen())

    except AuthenticationError:
        st.error("Invalid API key. Check your `.env` file.")
        st.stop()
    except RateLimitError:
        st.warning("Rate limited by OpenRouter. Wait a moment and retry.")
        st.stop()
    except APIError as e:
        st.error(f"OpenRouter error: {e}")
        insert_invocation(
            _db(),
            prompt_topic=topic, prompt_name=name, prompt_version=version,
            full_prompt=rendered_body, model_id=model,
            temperature=temperature, max_tokens=max_tokens,
            status="error", error_message=str(e),
        )
        st.stop()

    latency_ms = int((time.time() - start_time) * 1000)

    # Save to DB
    inv_id = insert_invocation(
        _db(),
        prompt_topic=topic,
        prompt_name=name,
        prompt_version=version,
        full_prompt=rendered_body,
        model_id=model,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format_choice,
        response_schema=json_schema_text,
        full_response=state["full_response"],
        prompt_tokens=state["usage"].get("prompt_tokens"),
        completion_tokens=state["usage"].get("completion_tokens"),
        total_tokens=state["usage"].get("total_tokens"),
        cost_usd=None,
        latency_ms=latency_ms,
        generation_id=state["response_id"],
        media_files=uploaded.name if uploaded else None,
        status="success",
    )

    # Metrics
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prompt tokens", state["usage"].get("prompt_tokens", "?"))
    c2.metric("Completion tokens", state["usage"].get("completion_tokens", "?"))
    c3.metric("Total tokens", state["usage"].get("total_tokens", "?"))
    c4.metric("Latency", f"{latency_ms} ms")
    st.caption(f"Saved as invocation #{inv_id} (cost fetched lazily in History)")
