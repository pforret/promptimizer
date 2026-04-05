# PRP: Prompt Optimisation & Versioning Framework (Streamlit + Python)

## Feature Overview

### Brief Description
A Streamlit web app for managing, executing, and comparing LLM prompts across models via OpenRouter. Tracks every invocation (model, tokens, cost, response) in SQLite for analysis and optimisation.

### User Value
Enables systematic prompt engineering: run the same prompt across models/temperatures, compare outputs side-by-side, track costs, and iterate toward optimal prompts — all through an interactive web UI.

### Scope
**Included:**
- Streamlit multi-page app with sidebar configuration
- CRUD prompt files (`input/prompts/<topic>/<name>.md`)
- Send prompts to any OpenRouter model with configurable temperature, structured output
- Media file upload/attachment support (images)
- SQLite tracking of all invocations (datetime, model, version, tokens, cost, full prompt/response)
- Markdown export of results to `docs/output/`
- Browse/compare/filter past invocations
- OpenRouter documentation in `docs/openrouter/`

**Not included:**
- Prompt chaining / multi-step workflows
- Automatic prompt optimisation (human-driven comparison only)
- Authentication / multi-user support
- Deployment (local only for v1)

---

## Context & Research

### Codebase Patterns
- **Fresh project** — only scaffolding exists: `docs/`, `input/prompts/`, `input/media/`, `database/`, `output -> docs/output`
- MkDocs Material docs site configured via `zensical.toml`
- `.gitignore` covers Node artifacts — needs Python additions (`__pycache__/`, `.venv/`, etc.)
- `input/media/.gitignore` contains `*` — media files excluded from git (as intended)
- Symlink: `output -> docs/output` and `README.md -> docs/index.md`

### External Resources

#### OpenRouter via OpenAI Python SDK
- **OpenRouter Quickstart**: https://openrouter.ai/docs/quickstart
- **API Reference**: https://openrouter.ai/docs/api-reference/overview
- **Models Directory**: https://openrouter.ai/models
- **Generation Stats**: https://openrouter.ai/docs/api-reference/get-a-generation
- **OpenAI Python SDK**: https://github.com/openai/openai-python

**Key API patterns:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://github.com/pforret/promptimizer",
        "X-Title": "Promptimizer",
    },
)

# Non-streaming chat completion
response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=4096,
)
# response.choices[0].message.content — the response text
# response.usage.prompt_tokens, completion_tokens, total_tokens
# response.id — generation ID for cost lookup

# Get cost (NOT in chat response — separate REST call required)
import requests
r = requests.get(
    f"https://openrouter.ai/api/v1/generation?id={response.id}",
    headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
)
cost_data = r.json()["data"]
# cost_data["total_cost"] — USD
# cost_data["latency"] — ms

# Structured output (JSON mode)
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "List 3 colors as JSON"}],
    response_format={"type": "json_object"},
)

# Structured output (JSON schema)
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=messages,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "output",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"items": {"type": "array", "items": {"type": "string"}}},
                "required": ["items"],
                "additionalProperties": False,
            },
        },
    },
)

# Image/media attachment (OpenAI-compatible multipart content)
import base64
with open("image.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ],
    }],
)

# Streaming
stream = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=messages,
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

# List models (no auth required)
r = requests.get("https://openrouter.ai/api/v1/models")
models = r.json()["data"]
# model["id"], model["name"], model["pricing"]["prompt"], model["pricing"]["completion"]
# model["context_length"], model["top_provider"]
```

**Gotchas:**
- Cost is NOT in the chat response — must call `/api/v1/generation?id=` separately
- Generation stats may take ~1s to populate after completion — retry once if null
- `response_format` with `json_schema` requires a model that supports it
- Model IDs are `provider/model-name` format (e.g. `anthropic/claude-sonnet-4`)

#### Streamlit
- **Docs**: https://docs.streamlit.io
- **Multi-page apps**: https://docs.streamlit.io/develop/concepts/multipage-apps
- **Session state**: https://docs.streamlit.io/develop/concepts/architecture/session-state
- **Streaming**: https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream
- **File uploader**: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader

**Key Streamlit patterns:**

```python
# Multi-page app (app.py)
import streamlit as st
pg = st.navigation([
    st.Page("pages/run.py", title="Run Prompt", icon="▶️", default=True),
    st.Page("pages/prompts.py", title="Prompts", icon="📝"),
    st.Page("pages/history.py", title="History", icon="📊"),
    st.Page("pages/models.py", title="Models", icon="🤖"),
    st.Page("pages/export.py", title="Export", icon="📤"),
])
pg.run()

# SQLite connection (cached)
@st.cache_resource
def get_db():
    conn = sqlite3.connect("database/db.sqlite", check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS ...")
    return conn

# Sidebar config
with st.sidebar:
    model = st.selectbox("Model", model_list, key="model")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, step=0.1)
    max_tokens = st.number_input("Max tokens", 100, 32000, 4096)

# Streaming LLM output
def stream_response(prompt, model, temperature):
    stream = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=temperature, stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

result = st.write_stream(stream_response(prompt, model, temp))

# Side-by-side comparison
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"Run #{id1}")
    st.markdown(response_a)
with col2:
    st.subheader(f"Run #{id2}")
    st.markdown(response_b)

# File upload
uploaded = st.file_uploader("Attach image", type=["png", "jpg", "webp"])
if uploaded:
    st.image(uploaded)
    # uploaded.getvalue() for raw bytes
```

### Dependencies

```bash
uv init
uv add streamlit openai python-dotenv requests pyyaml
uv add --dev pytest
```

No native modules, no build step. Python stdlib `sqlite3`, `hashlib`, and `re` cover the rest. `pyyaml` for prompt frontmatter parsing.

### Environment Requirements
- Python 3.10+ (managed via `uv`)
- `uv` package manager
- `OPENROUTER_API_KEY` in `.env`
- macOS / Linux / Windows

---

## Architecture & Design

### File Structure

```
promptimizer/
├── app.py                          # Streamlit entry point (st.navigation)
├── pages/
│   ├── run.py                      # Main page: select prompt, configure, run, see response
│   ├── prompts.py                  # CRUD prompt files
│   ├── history.py                  # Browse/compare/filter past invocations
│   ├── models.py                   # List & search OpenRouter models
│   └── export.py                   # Export invocations to Markdown
├── lib/
│   ├── db.py                       # SQLite init, migrations, query functions
│   ├── openrouter.py               # OpenAI client wrapper, cost fetching, model listing
│   ├── prompts.py                  # Prompt file I/O (list/read/write/delete from input/prompts/)
│   └── export.py                   # Markdown generation for docs/output/
├── input/
│   ├── prompts/                    # Prompt files organized by topic
│   │   └── office/
│   │       └── generate_meeting_report.md
│   └── media/                      # Media files (not in git)
├── database/
│   └── db.sqlite                   # Created at runtime
├── docs/
│   ├── output/                     # Markdown exports
│   └── openrouter/                 # OpenRouter documentation
├── .env                            # OPENROUTER_API_KEY (not in git)
├── .env.example                    # Template
├── .streamlit/
│   └── config.toml                 # Streamlit theme/config
├── pyproject.toml                  # uv project metadata + dependencies
├── uv.lock                         # uv lockfile
└── tests/
    ├── test_db.py
    ├── test_prompts.py
    └── test_export.py
```

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS invocations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    -- prompt info
    prompt_topic    TEXT NOT NULL,
    prompt_name     TEXT NOT NULL,
    prompt_version  TEXT NOT NULL DEFAULT '1',
    full_prompt     TEXT NOT NULL,
    -- model info
    model_id        TEXT NOT NULL,
    model_name      TEXT,
    -- parameters
    temperature     REAL DEFAULT 1.0,
    max_tokens      INTEGER,
    response_format TEXT,
    response_schema TEXT,
    -- response
    full_response   TEXT,
    -- metrics
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_tokens      INTEGER,
    cost_usd          REAL,
    latency_ms        INTEGER,
    -- media
    media_files     TEXT,
    -- timestamps
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    -- status
    status          TEXT NOT NULL DEFAULT 'success',
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_invocations_prompt ON invocations(prompt_topic, prompt_name);
CREATE INDEX IF NOT EXISTS idx_invocations_model ON invocations(model_id);
CREATE INDEX IF NOT EXISTS idx_invocations_created ON invocations(created_at);
```

### Page Designs

#### Run Prompt (`pages/run.py`) — Main page
- **Sidebar**: model selector (searchable dropdown), temperature slider, max_tokens input, response format toggle (text/json/json_schema), optional JSON schema text area
- **Main area**: prompt selector (topic → name dropdowns), prompt content preview (read-only), auto-detected `{{variable}}` input fields, media file uploader, "Run" button
- **Output area**: streaming response display, then metrics summary (tokens, cost, latency) in `st.metric` columns
- **Bottom**: "Save to history" auto-enabled, link to view in history

#### Prompts (`pages/prompts.py`)
- List all prompts grouped by topic (expandable sections)
- Create: topic + name inputs, text area for content, save button
- Edit: select prompt, modify in text area, save
- Delete: with confirmation
- Show prompt version (SHA-256 hash, first 8 chars)

#### History (`pages/history.py`)
- Filterable table: by prompt, model, date range, status
- Click row to expand full details (prompt, response, metrics)
- Multi-select for comparison: side-by-side view with `st.columns(2)`
- Stats tab: total cost, tokens by model, cost over time chart

#### Models (`pages/models.py`)
- Searchable/filterable table of OpenRouter models
- Columns: ID, name, context length, prompt price, completion price
- Cache model list with `@st.cache_data(ttl=3600)`
- Click to set as active model (updates sidebar)

#### Export (`pages/export.py`)
- Filter options (same as history)
- Preview generated Markdown
- "Export" button writes to `docs/output/`
- Shows list of previously exported files

### Design Decisions

1. **Streamlit over CLI**: Interactive exploration (model switching, temperature tweaking, side-by-side comparison) is the core use case. Streamlit provides this natively; a CLI would need 3x the code for inferior UX.

2. **OpenAI Python SDK + base_url**: OpenRouter is OpenAI-compatible. Using the standard `openai` package means well-maintained, well-documented, zero vendor lock-in. No need for a separate OpenRouter-specific SDK.

3. **Python stdlib sqlite3**: No extra dependency. Synchronous, simple, sufficient for single-user local app. Use `check_same_thread=False` for Streamlit's threading model.

4. **Prompts as files**: Git-friendly versioning. The DB stores the full prompt text (with variables substituted) at invocation time, so historical runs are preserved even if the file changes.

5. **Lazy cost tracking**: OpenRouter doesn't return cost in completions. Cost is fetched from `/api/v1/generation?id=` only when expanding a single invocation's details in History. Stored in DB once fetched, so subsequent views are instant.

6. **Prompt frontmatter**: Prompts support optional YAML frontmatter (`---` delimited) for defaults: `description`, `model`, `temperature`, `max_tokens`, `response_format`, `system`. Parsed with PyYAML.

7. **System prompt via frontmatter**: If `system:` is set in frontmatter, it becomes the system message. The prompt body becomes the user message. If no `system:` field, everything is sent as a single user message.

8. **Smart model defaults**: `openai/chatgpt-4o-latest` for text, `google/gemini-2.5-pro` for media-attached prompts. Frontmatter `model:` overrides the default.

9. **Template variables**: `{{variable}}` placeholders detected via `re.findall(r'\{\{(\w+)\}\}', content)`. Each renders as an input field on the Run page. Substituted before sending. Prompt body is read-only — users fill variables, not edit the template.

10. **DB recreation**: During development, the DB is simply recreated (drop + create tables) when schema changes. No migration system.

---

## Implementation Blueprint

### Pseudocode: Run page

```
1. Sidebar: render model selector, temperature slider, max_tokens, response_format toggle
2. Main: render prompt selector (topic dropdown → name dropdown)
3. Load selected prompt file, parse frontmatter (model, temperature, system, etc.) → pre-fill sidebar
4. Render prompt body read-only (st.markdown or st.code)
5. Detect {{variable}} placeholders → render st.text_input for each
6. Optional: file_uploader for media attachment
7. On "Run" button click:
   a. Substitute {{variables}} into prompt body
   b. Build messages list:
      - If frontmatter has system: → [{"role": "system", "content": system}, {"role": "user", "content": body}]
      - Else: [{"role": "user", "content": body}]
      - If media attached: user message becomes multipart content (text + image_url with base64)
   c. Compute prompt_version = sha256(final_content)[:8]
   c. Record start_time
   d. Call OpenRouter via streaming:
      - Use st.write_stream() with generator that yields chunks
      - Collect full response text from return value
   e. Record end_time, compute latency
   f. Extract usage (prompt_tokens, completion_tokens) from final chunk or response
   g. Insert invocation into SQLite (cost_usd=None, fetched lazily)
   h. Display metrics: st.columns with st.metric for tokens, latency
```

### Pseudocode: History comparison

```
1. Query all invocations, display as filterable dataframe
2. User selects 2+ rows via st.multiselect or checkboxes
3. Render side-by-side with st.columns:
   - Header: model, date, temperature
   - Metrics: tokens, cost, latency
   - Response: full Markdown text
4. Highlight differences (optional: difflib for text diff)
```

### Pseudocode: Markdown export

```
1. Query invocations (filtered by user selection)
2. Group by prompt_topic/prompt_name
3. For each group:
   a. Create docs/output/<topic>/<name>.md
   b. YAML frontmatter: topic, name, export date
   c. For each invocation: model, date, params, metrics, response (in details/summary)
4. Generate docs/output/index.md with table of all exports
5. Show success message with file paths
```

---

## Implementation Tasks

### Phase 1: Project Setup
- [ ] Run `uv init` and `uv add streamlit openai python-dotenv requests pyyaml` + `uv add --dev pytest`
- [ ] Create `.env.example` with `OPENROUTER_API_KEY=your-key-here`
- [ ] Create `.streamlit/config.toml` with theme (match MkDocs Material red primary)
- [ ] Update `.gitignore` — add Python patterns (`__pycache__/`, `.venv/`, `*.pyc`, `database/*.sqlite`)
- [ ] Create `app.py` with `st.navigation` wiring all pages
- [ ] Create empty page files in `pages/`

### Phase 2: Core Libraries
- [ ] Implement `lib/db.py` — `get_db()`, `init_tables()`, `insert_invocation()`, `list_invocations()`, `get_invocation()`, `get_stats()`
- [ ] Implement `lib/prompts.py` — `list_prompts()`, `read_prompt()`, `write_prompt()`, `delete_prompt()`, `prompt_version()`, `parse_frontmatter()`, `extract_variables()`, `render_template()`
- [ ] Implement `lib/openrouter.py` — `get_client()`, `send_prompt()` (streaming + non-streaming), `fetch_cost()`, `list_models()`, `default_model()` (text→chatgpt-4o-latest, media→gemini-2.5-pro)
- [ ] Implement `lib/export.py` — `export_invocations()`, `generate_index()`

### Phase 3: Pages
- [ ] Implement `pages/run.py` — sidebar config (pre-filled from frontmatter), prompt selection, `{{variable}}` input fields, run with streaming, metrics display
- [ ] Implement `pages/prompts.py` — list/create/edit/delete prompts
- [ ] Implement `pages/history.py` — filterable table, detail view, comparison, stats
- [ ] Implement `pages/models.py` — cached model list, search, pricing display
- [ ] Implement `pages/export.py` — filter, preview, export to Markdown

### Phase 4: Sample Content & Docs
- [ ] Create sample prompts in `input/prompts/` (3-4 across 2 topics)
- [ ] Write `docs/openrouter/index.md` — overview, account setup
- [ ] Write `docs/openrouter/models.md` — model IDs, pricing, capabilities
- [ ] Write `docs/openrouter/api.md` — Python SDK usage, cost tracking, structured output
- [ ] Write `docs/openrouter/tips.md` — provider routing, fallbacks, cost optimization

### Phase 5: Testing & Validation
- [ ] Write `tests/test_db.py` — CRUD on in-memory SQLite
- [ ] Write `tests/test_prompts.py` — file I/O with tmp_path
- [ ] Write `tests/test_export.py` — Markdown generation from fixtures
- [ ] Run all validation gates

---

## Error Handling Strategy

| Scenario | Detection | Response |
|---|---|---|
| Missing API key | `OPENROUTER_API_KEY` not in env | `st.error()` with setup instructions, disable Run |
| Invalid model ID | 404 from OpenRouter | `st.error()` with model ID, link to models page |
| Rate limited | 429 response | `st.warning()` with retry-after |
| Insufficient credits | 402 response | `st.error()` with link to OpenRouter dashboard |
| Prompt file not found | `FileNotFoundError` | `st.warning()`, refresh prompt list |
| DB write failure | `sqlite3.Error` | `st.warning()`, still display response |
| Cost fetch failure | null from generation endpoint | Store with `cost_usd=None`, show "pending" in UI |
| Media too large | Check `uploaded.size` | `st.warning()` with size limit |

```python
# Pattern in lib/openrouter.py
from openai import AuthenticationError, RateLimitError, APIError

try:
    response = client.chat.completions.create(...)
except AuthenticationError:
    st.error("Invalid API key. Check your .env file.")
    return None
except RateLimitError:
    st.warning("Rate limited. Wait a moment and retry.")
    return None
except APIError as e:
    st.error(f"OpenRouter error: {e.message}")
    # Store failed invocation
    db.insert_invocation(..., status="error", error_message=str(e))
    return None
```

---

## Testing Strategy

### Unit Tests (pytest)
- `tests/test_db.py` — insert, query, filter, stats on in-memory `:memory:` SQLite
- `tests/test_prompts.py` — list/read/write/delete with `tmp_path` fixture
- `tests/test_export.py` — Markdown generation from fixture data, verify file output

### Integration Tests
- Mock `openai.OpenAI` with `unittest.mock.patch` to test `lib/openrouter.py`
- Verify invocation record matches expected fields after mock run

### Test Data
- Sample prompts created in `tmp_path` during tests
- Mock OpenRouter responses with realistic usage data

---

## Validation Gates

```bash
# Install dependencies
uv sync

# Lint
uv run python -m py_compile app.py
uv run python -m py_compile lib/db.py lib/openrouter.py lib/prompts.py lib/export.py

# Tests
uv run pytest tests/ -v

# Smoke test: app starts without error
timeout 10 uv run streamlit run app.py --server.headless true 2>&1 | head -5

# Smoke test: DB initializes
uv run python -c "from lib.db import get_db; get_db()"
```

---

## Security Considerations

- [ ] API key in `.env` only, never committed (`.env` already in `.gitignore`)
- [ ] SQLite parameterized queries only (`?` placeholders, no f-strings in SQL)
- [ ] Media files: validate type via `uploaded.type` before sending
- [ ] Never display API key in UI or error messages
- [ ] `check_same_thread=False` is safe for Streamlit's single-user model

---

## Streamlit Config

`.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#d32f2f"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f5f5f5"
textColor = "#212121"

[server]
maxUploadSize = 50
```

---

## Sample Prompts

`input/prompts/office/generate_meeting_report.md`:
```markdown
---
description: Generate a meeting report from transcript
model: openai/chatgpt-4o-latest
temperature: 0.3
max_tokens: 4096
system: You are an expert meeting summarizer. Be concise but complete.
---
Given the following meeting transcript, produce a structured report with:
- **Summary** (2-3 sentences)
- **Key Decisions**
- **Action Items** (with owners and deadlines)
- **Discussion Points**

## Transcript
{{transcript}}
```

`input/prompts/coding/code_review.md`:
```markdown
---
description: Review code for bugs, security, and style
temperature: 0.2
---
You are a senior software engineer. Review the following {{language}} code for:
- Bugs and logic errors
- Security vulnerabilities
- Performance issues
- Code style and readability

Provide specific, actionable feedback with line references.

## Code
{{code}}
```

`input/prompts/analysis/describe_image.md`:
```markdown
---
description: Describe and analyse an uploaded image
model: google/gemini-2.5-pro
temperature: 0.5
---
Analyse the attached image and provide:
- A detailed description of what you see
- Any text or labels visible
- Key observations or notable elements

Focus on {{focus_area}}.
```

---

## Success Criteria

- [ ] `streamlit run app.py` launches the app
- [ ] Run page: select prompt, pick model, adjust temperature, click Run, see streaming response
- [ ] Run page: tokens, cost, and latency displayed after completion
- [ ] Run page: media file upload works with vision models
- [ ] Run page: structured output (JSON mode) works
- [ ] Prompts page: create, edit, delete prompt files
- [ ] History page: filter by prompt/model/date, view details, compare side-by-side
- [ ] Models page: searchable list with pricing
- [ ] Export page: generates Markdown in `docs/output/`
- [ ] All invocations tracked in `database/db.sqlite`
- [ ] OpenRouter docs written in `docs/openrouter/`

---

## Known Limitations

- **Single user** — no auth, local use only; Streamlit Cloud deployment would need secrets management
- **Cost may be delayed** — OpenRouter's generation endpoint may not have cost immediately; fetched lazily on history view
- **No batch runs** — can't run one prompt across N models simultaneously (could add later with `st.spinner` + threads)
- **Model list caching** — cached for 1 hour; new models won't appear until cache expires

---

## References

- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) — Account setup, API key
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference/overview) — Full REST API
- [OpenRouter Models](https://openrouter.ai/models) — Model directory with pricing
- [OpenRouter Generation Stats](https://openrouter.ai/docs/api-reference/get-a-generation) — Cost retrieval
- [OpenAI Python SDK](https://github.com/openai/openai-python) — Client library
- [Streamlit Docs](https://docs.streamlit.io) — Full framework reference
- [Streamlit Multi-page Apps](https://docs.streamlit.io/develop/concepts/multipage-apps) — Navigation setup
- [Streamlit Session State](https://docs.streamlit.io/develop/concepts/architecture/session-state) — State management
- [Streamlit write_stream](https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream) — LLM streaming

---

## Resolved Questions

1. **Prompt variables**: `{{variable}}` placeholders are auto-detected via regex. The Run page renders a `st.text_input` or `st.text_area` for each variable found. The prompt is rendered with substitutions before sending.
2. **Default model**: `openai/chatgpt-4o-latest` for text prompts, `google/gemini-2.5-pro` for prompts with media attachments (video/image analysis). Overridable in sidebar and via prompt frontmatter.
3. **Cost tracking**: Lazy — cost is fetched from `/api/v1/generation?id=` only when viewing invocation details in History, not at run time. Stored once fetched.
4. **Prompt frontmatter**: Yes. Prompt `.md` files support optional YAML frontmatter for defaults:

```yaml
---
description: Generate a meeting report from transcript
model: openai/chatgpt-4o-latest
temperature: 0.3
max_tokens: 4096
response_format: text
system: You are an expert meeting summarizer.
---
```

Frontmatter values pre-fill the sidebar but can be overridden per run. The `system:` field becomes the system message.

---

## PRP Metadata

- **Created**: 2026-04-05
- **Author**: Claude (PRP Generator)
- **Target Repository**: pforret/promptimizer
- **Estimated Complexity**: Medium
- **Dependencies**: streamlit, openai, python-dotenv, requests, pyyaml
- **Status**: Ready

---

## Confidence Score: 9/10

**Rationale**: All ambiguities resolved. Streamlit + OpenAI Python SDK + SQLite is a battle-tested stack with zero build complexity. `uv` handles deps cleanly. The design decisions (read-only prompts with variable substitution, system message via frontmatter, lazy cost fetch, DB recreation) simplify the implementation significantly. The only remaining risk is Streamlit's rerun model requiring careful session_state management for the Run page workflow. One-pass implementation should produce a fully working app.
