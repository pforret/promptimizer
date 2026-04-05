# pforret/promptimizer

Framework for prompt comparison and optimisation across LLM models via [OpenRouter](https://openrouter.ai).

## What it does

- **Manage prompts** as Markdown files with YAML frontmatter (model, temperature, system prompt)
- **Run prompts** against 300+ models (OpenAI, Anthropic, Google, Mistral, Qwen, ...) with configurable parameters
- **Template variables** (`{{variable}}`) auto-detected and rendered as input fields
- **Track every invocation** in SQLite: model, tokens, cost, latency, full prompt/response
- **Compare results** side-by-side across models and temperatures
- **Export** results as Markdown to `docs/output/`

## Quick start

```bash
# Clone and install
git clone https://github.com/pforret/promptimizer.git
cd promptimizer
uv sync

# Configure API key
cp .env.example .env
# Edit .env and add your OpenRouter API key

# Run
uv run streamlit run app.py
```

## Running

| Service           | URL                                     | Command                       |
|-------------------|-----------------------------------------|-------------------------------|
| **Streamlit app** | [localhost:8501](http://localhost:8501) | `uv run streamlit run app.py` |
| **Zensical docs** | [localhost:8069](http://localhost:8069) | `mkdox2 serve`                |

## Project structure

```
app.py                  # Streamlit entry point (5 pages)
pages/
  run.py                # Select prompt, fill variables, run, stream response
  prompts.py            # Create/edit/delete prompt files
  history.py            # Browse, filter, compare invocations
  models.py             # Search available models with pricing
  export.py             # Export results to Markdown
lib/
  db.py                 # SQLite schema and queries
  openrouter.py         # OpenAI SDK + OpenRouter client
  prompts.py            # Prompt file I/O, frontmatter, templating
  export.py             # Markdown export
config/
  models.yaml           # Curated model list (edit to add/remove models)
input/prompts/          # Prompt files organized by topic
input/media/            # Media files for vision/video models (not in git)
database/               # SQLite DB (created at runtime, not in git)
docs/openrouter/        # OpenRouter documentation
```

## Prompt format

Prompts are Markdown files in `input/prompts/<topic>/<name>.md` with optional YAML frontmatter:

```markdown
---
description: Generate a meeting report from transcript
model: openai/gpt-4o
temperature: 0.3
max_tokens: 4096
system: You are an expert meeting summarizer.
---
Produce a structured report from the following transcript:

{{transcript}}
```

- `model` / `temperature` / `max_tokens` pre-fill the sidebar (overridable per run)
- `system` becomes the system message
- `{{variable}}` placeholders render as input fields

## Model configuration

Edit `config/models.yaml` to curate available models per category:

- **text** -- text-only models (no image/video input)
- **vision** -- models that accept image input
- **video** -- models that accept video input

Defaults and model lists are read from this file.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [OpenRouter API key](https://openrouter.ai/keys)
