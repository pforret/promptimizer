# Tips & Best Practices

## Model Fallback

Pass an array of models for automatic fallback if the primary is unavailable:

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    extra_body={
        "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4"],
    },
    messages=messages,
)
```

## Provider Routing

Control which provider serves your request:

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    extra_body={
        "provider": {
            "sort": "price",  # or "latency"
            "order": ["Azure", "OpenAI"],
        },
    },
    messages=messages,
)
```

## Cost Optimization

1. **Use free models for testing**: Many models have free tiers (e.g. `meta-llama/llama-3-8b-instruct:free`)
2. **Lower max_tokens**: Only request what you need
3. **Use cheaper models first**: Test with GPT-4o-mini before GPT-4o
4. **Monitor spending**: Check [openrouter.ai/activity](https://openrouter.ai/activity)

## Rate Limits

- Rate limits vary by model and your account tier
- Free models have stricter limits
- Handle `429 Too Many Requests` with exponential backoff
- Check `Retry-After` header in 429 responses

## Check Your Balance

```python
import requests

r = requests.get(
    "https://openrouter.ai/api/v1/credits",
    headers={"Authorization": "Bearer sk-or-v1-..."},
)
data = r.json()["data"]
print(f"Credits: ${data['total_credits']:.2f}")
print(f"Used: ${data['total_usage']:.2f}")
```
