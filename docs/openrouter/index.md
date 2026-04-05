# OpenRouter

[OpenRouter](https://openrouter.ai) is a unified API gateway for 200+ LLM models from providers like OpenAI, Anthropic, Google, Meta, Mistral, and more.

## Why OpenRouter?

- **Single API, many models**: Switch between GPT-4o, Claude, Gemini, Llama, etc. with just a model ID change
- **OpenAI-compatible**: Use the standard OpenAI Python SDK with a different `base_url`
- **Pay-per-use**: No subscriptions — pay only for tokens consumed
- **Provider routing**: Automatically route to the cheapest or fastest provider

## Setup

1. Create an account at [openrouter.ai](https://openrouter.ai)
2. Go to [Keys](https://openrouter.ai/keys) and create an API key
3. Add to your `.env` file:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
4. Add credits at [openrouter.ai/credits](https://openrouter.ai/credits)

## Links

- [Quickstart](https://openrouter.ai/docs/quickstart)
- [API Reference](https://openrouter.ai/docs/api-reference/overview)
- [Models Directory](https://openrouter.ai/models)
- [Pricing](https://openrouter.ai/models) (per-model pricing shown on each model page)
