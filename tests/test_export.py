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


def test_export_creates_individual_files(tmp_path):
    files = export_invocations(_sample_invocations(), output_dir=tmp_path)
    assert len(files) == 3  # one per invocation

    # Check file paths match expected pattern
    assert (tmp_path / "test" / "hello" / "20260405.gpt-4o.1.md").exists()
    assert (tmp_path / "test" / "hello" / "20260405.claude-sonnet-4.2.md").exists()
    assert (tmp_path / "other" / "summarize" / "20260405.gpt-4o.3.md").exists()


def test_export_content(tmp_path):
    export_invocations(_sample_invocations(), output_dir=tmp_path)

    f = tmp_path / "test" / "hello" / "20260405.gpt-4o.1.md"
    content = f.read_text()
    assert "openai/gpt-4o" in content
    assert "Hello there!" in content
    assert "$0.001000" in content

    f2 = tmp_path / "test" / "hello" / "20260405.claude-sonnet-4.2.md"
    content2 = f2.read_text()
    assert "pending" in content2  # cost_usd=None


def test_export_skips_failures(tmp_path):
    invocations = [
        {
            "id": 10,
            "prompt_topic": "t",
            "prompt_name": "p",
            "prompt_version": "v1",
            "full_prompt": "test",
            "model_id": "x/y",
            "full_response": None,
            "status": "error",
            "created_at": "2026-04-05 12:00:00",
        },
    ]
    files = export_invocations(invocations, output_dir=tmp_path)
    assert len(files) == 0


def test_export_empty(tmp_path):
    files = export_invocations([], output_dir=tmp_path)
    assert len(files) == 0
