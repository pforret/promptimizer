from pathlib import Path

from lib.export import export_invocations


def _sample_invocations():
    return [
        {
            "id": 1,
            "prompt_topic": "test",
            "prompt_name": "hello",
            "prompt_version": "abc12345",
            "full_prompt": "Say hello",
            "model_id": "openai/gpt-4o",
            "temperature": 0.7,
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15,
            "cost_usd": 0.001,
            "latency_ms": 200,
            "full_response": "Hello there!",
            "status": "success",
            "created_at": "2026-04-05 12:00:00",
        },
        {
            "id": 2,
            "prompt_topic": "test",
            "prompt_name": "hello",
            "prompt_version": "abc12345",
            "full_prompt": "Say hello",
            "model_id": "anthropic/claude-sonnet-4",
            "temperature": 0.5,
            "prompt_tokens": 5,
            "completion_tokens": 12,
            "total_tokens": 17,
            "cost_usd": None,
            "latency_ms": 300,
            "full_response": "Hi! How can I help?",
            "status": "success",
            "created_at": "2026-04-05 12:01:00",
        },
        {
            "id": 3,
            "prompt_topic": "other",
            "prompt_name": "summarize",
            "prompt_version": "def67890",
            "full_prompt": "Summarize this",
            "model_id": "openai/gpt-4o",
            "temperature": 0.3,
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
            "cost_usd": 0.002,
            "latency_ms": 400,
            "full_response": "Summary here.",
            "status": "success",
            "created_at": "2026-04-05 12:02:00",
        },
    ]


def test_export_creates_files(tmp_path):
    files = export_invocations(_sample_invocations(), output_dir=tmp_path)
    assert len(files) == 3  # test/hello.md, other/summarize.md, index.md

    # Check index
    index = tmp_path / "index.md"
    assert index.exists()
    content = index.read_text()
    assert "test/hello" in content
    assert "other/summarize" in content


def test_export_content(tmp_path):
    export_invocations(_sample_invocations(), output_dir=tmp_path)

    hello_file = tmp_path / "test" / "hello.md"
    assert hello_file.exists()
    content = hello_file.read_text()
    assert "Run #1" in content
    assert "Run #2" in content
    assert "openai/gpt-4o" in content
    assert "anthropic/claude-sonnet-4" in content
    assert "Hello there!" in content
    assert "pending" in content  # cost_usd=None for run #2


def test_export_empty(tmp_path):
    files = export_invocations([], output_dir=tmp_path)
    assert len(files) == 1  # just index
    index = tmp_path / "index.md"
    assert index.exists()
