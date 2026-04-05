# Models

## Model IDs

OpenRouter uses `provider/model-name` format:

| Model ID | Description |
|---|---|
| `openai/gpt-4o` | Latest ChatGPT-4o |
| `openai/gpt-4.1` | GPT-4.1 |
| `anthropic/claude-sonnet-4` | Claude Sonnet 4 |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro (vision) |
| `meta-llama/llama-4-maverick` | Llama 4 Maverick |

Full list: [openrouter.ai/models](https://openrouter.ai/models)

## Pricing

Pricing is per-token, shown as USD per million tokens. Example:

| Model | Input $/M | Output $/M |
|---|---|---|
| `openai/gpt-4o` | $2.50 | $10.00 |
| `anthropic/claude-sonnet-4` | $3.00 | $15.00 |
| `google/gemini-2.5-pro` | $1.25 | $10.00 |

Free models exist (e.g. `meta-llama/llama-3-8b-instruct:free`) but with rate limits.

## Capabilities

Not all models support all features:

- **Vision**: `openai/gpt-4o`, `google/gemini-2.5-pro`, `anthropic/claude-sonnet-4`
- **Structured output (JSON schema)**: `openai/gpt-4o`, `openai/gpt-4.1`
- **JSON mode**: Most major models
- **Long context (100k+)**: `anthropic/claude-sonnet-4`, `google/gemini-2.5-pro`

Check model pages on OpenRouter for exact capability support.
