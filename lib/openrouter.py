import os
import time
from collections.abc import Generator
from pathlib import Path

import yaml
import requests
from openai import OpenAI, AuthenticationError, RateLimitError, APIError

CONFIG_PATH = Path("config/models.yaml")


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text()) or {}
    return {}


def _defaults() -> dict:
    return _load_config().get("defaults", {})


DEFAULT_TEXT_MODEL = _defaults().get("text_model", "openai/gpt-4o")
DEFAULT_VISION_MODEL = _defaults().get("vision_model", "anthropic/claude-sonnet-4")
DEFAULT_VIDEO_MODEL = _defaults().get("video_model", "google/gemini-2.5-pro")

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/pforret/promptimizer",
                "X-Title": "Promptimizer",
            },
        )
    return _client


def default_model(has_media: bool = False) -> str:
    return DEFAULT_VIDEO_MODEL if has_media else DEFAULT_TEXT_MODEL


def configured_models(category: str = "text") -> list[str]:
    """Return model IDs for a category (text/vision/video) from config."""
    config = _load_config()
    return config.get("models", {}).get(category, [])


def send_prompt_stream(
    messages: list[dict],
    model: str,
    temperature: float = 1.0,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> Generator[dict, None, None]:
    """Stream a chat completion. Yields dicts with 'type' key:
    - {"type": "delta", "content": str}
    - {"type": "done", "response_id": str, "usage": dict}
    """
    client = get_client()
    kwargs: dict = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
        stream_options={"include_usage": True},
    )
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if response_format:
        kwargs["response_format"] = response_format

    stream = client.chat.completions.create(**kwargs)

    response_id = None
    usage = None
    for chunk in stream:
        if not response_id and chunk.id:
            response_id = chunk.id
        if chunk.usage:
            usage = {
                "prompt_tokens": chunk.usage.prompt_tokens,
                "completion_tokens": chunk.usage.completion_tokens,
                "total_tokens": chunk.usage.total_tokens,
            }
        if chunk.choices and chunk.choices[0].delta.content:
            yield {"type": "delta", "content": chunk.choices[0].delta.content}

    yield {
        "type": "done",
        "response_id": response_id,
        "usage": usage or {},
    }


def send_prompt(
    messages: list[dict],
    model: str,
    temperature: float = 1.0,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> dict:
    """Non-streaming chat completion. Returns dict with response_text, response_id, usage."""
    client = get_client()
    kwargs: dict = dict(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if response_format:
        kwargs["response_format"] = response_format

    response = client.chat.completions.create(**kwargs)
    return {
        "response_text": response.choices[0].message.content or "",
        "response_id": response.id,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        },
    }


def fetch_cost(generation_id: str) -> float | None:
    """Fetch cost for a generation from OpenRouter. Returns USD or None."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key or not generation_id:
        return None

    for attempt in range(2):
        try:
            r = requests.get(
                f"https://openrouter.ai/api/v1/generation?id={generation_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                cost = data.get("total_cost")
                if cost is not None:
                    return float(cost)
        except requests.RequestException:
            pass
        if attempt == 0:
            time.sleep(1)

    return None


def list_models() -> list[dict]:
    """Fetch all models from OpenRouter. Returns list of model dicts."""
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=15)
        r.raise_for_status()
        models = r.json().get("data", [])
        return [
            {
                "id": m["id"],
                "name": m.get("name", m["id"]),
                "context_length": m.get("context_length", 0),
                "pricing_prompt": m.get("pricing", {}).get("prompt", "0"),
                "pricing_completion": m.get("pricing", {}).get("completion", "0"),
            }
            for m in models
        ]
    except requests.RequestException:
        return []
