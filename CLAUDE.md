# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app.py          # Streamlit on http://localhost:8501

# Run tests
uv run pytest tests/ -v              # all tests
uv run pytest tests/test_db.py -v    # single test file
uv run pytest tests/test_db.py::test_insert_and_get  # single test

# Compile check (no linter configured)
uv run python -m py_compile app.py lib/db.py lib/openrouter.py lib/prompts.py lib/export.py
```

## Architecture

Three-layer Streamlit app using OpenRouter (OpenAI-compatible API) for multi-model LLM inference.

**UI layer** (`app.py` + `pages/`): Streamlit multi-page app via `st.navigation`. Five pages: run, prompts, history, models, export. Each page imports directly from `lib/`.

**Library layer** (`lib/`): Stateless modules with factory/singleton patterns:
- `db.py` — SQLite with single `invocations` table. `get_db()` creates schema on first call. Uses `check_same_thread=False` for Streamlit. Tests use `get_db(":memory:")`.
- `openrouter.py` — Wraps `openai.OpenAI` client pointed at `https://openrouter.ai/api/v1`. Streaming (`send_prompt_stream`) yields delta dicts; non-streaming (`send_prompt`) returns full response. Cost is fetched lazily via separate REST call to `/api/v1/generation?id=`.
- `prompts.py` — File I/O for `input/prompts/<topic>/<name>.md`. Parses YAML frontmatter (`---` delimited) and `{{variable}}` template placeholders. `PROMPTS_DIR` constant is monkeypatched in tests.
- `export.py` — Generates Markdown files in `docs/output/` grouped by topic/name. `OUTPUT_DIR` constant is overridden via `output_dir` param in tests.

**Config** (`config/models.yaml`): Curated model lists (text/vision/video) with defaults. Read by `lib/openrouter.py` at import time. Edit this file to add/remove models.

## Key patterns

- **Prompt frontmatter**: `model`, `temperature`, `max_tokens`, `system`, `description` fields pre-fill the sidebar. `system` becomes a separate system message.
- **Model categories**: text (no media), vision (image input), video (video input). The Run page filters the dropdown based on whether media is attached.
- **Lazy cost**: `cost_usd` is NULL after insertion. Fetched from OpenRouter's generation endpoint only when viewing details in History, then cached in DB via `update_cost()`.
- **Prompt versioning**: SHA-256 hash of rendered content (first 8 chars). Changes automatically when the prompt text changes.
- **Streamlit caching**: `@st.cache_resource` for DB connections, `@st.cache_data(ttl=3600)` for model lists.
- **DB recreation**: No migrations. `recreate_db()` drops and recreates during development.

## Test patterns

Tests use pytest `tmp_path` fixture. For `lib/prompts.py` tests, monkeypatch `prompts_mod.PROMPTS_DIR` to `tmp_path` and restore in finally block. For `lib/export.py`, pass `output_dir=tmp_path`. For `lib/db.py`, use `get_db(":memory:")`.

## Environment

- `OPENROUTER_API_KEY` in `.env` (loaded by `python-dotenv` in `app.py`)
- Python 3.12+ managed by uv
- Streamlit theme configured in `.streamlit/config.toml`
