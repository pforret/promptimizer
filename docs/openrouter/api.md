# API Usage with Python

## Client Setup

OpenRouter is OpenAI-compatible. Use the standard `openai` Python package:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-...",
    default_headers={
        "HTTP-Referer": "https://yoursite.com",
        "X-Title": "Your App Name",
    },
)
```

## Chat Completion

```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=4096,
)
print(response.choices[0].message.content)
```

## Streaming

```python
stream = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Structured Output

### JSON mode
```python
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "List 3 colors as JSON"}],
    response_format={"type": "json_object"},
)
```

### JSON Schema
```python
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
```

## Vision / Image Input

```python
import base64

with open("image.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="google/gemini-2.5-pro",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ],
    }],
)
```

## Token Usage

```python
response.usage.prompt_tokens
response.usage.completion_tokens
response.usage.total_tokens
```

## Cost Tracking

Cost is **not** included in the chat completion response. Fetch it separately:

```python
import requests

r = requests.get(
    f"https://openrouter.ai/api/v1/generation?id={response.id}",
    headers={"Authorization": "Bearer sk-or-v1-..."},
)
data = r.json()["data"]
print(data["total_cost"])  # USD
```

Note: Generation stats may take ~1 second to populate after the completion returns.

See: [Generation Stats API](https://openrouter.ai/docs/api-reference/get-a-generation)
