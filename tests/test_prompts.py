from pathlib import Path

from lib.prompts import (
    list_topics,
    list_prompts,
    read_prompt,
    write_prompt,
    delete_prompt,
    prompt_version,
    parse_frontmatter,
    extract_variables,
    render_template,
    PROMPTS_DIR,
)
import lib.prompts as prompts_mod


def _setup_prompts(tmp_path: Path):
    """Temporarily redirect PROMPTS_DIR to tmp_path."""
    prompts_mod.PROMPTS_DIR = tmp_path
    # Create sample prompts
    (tmp_path / "topic_a").mkdir()
    (tmp_path / "topic_a" / "prompt1.md").write_text("Hello {{name}}")
    (tmp_path / "topic_b").mkdir()
    (tmp_path / "topic_b" / "prompt2.md").write_text(
        "---\ndescription: test\ntemperature: 0.5\nsystem: Be helpful\n---\nContent {{x}}"
    )
    return tmp_path


def _teardown(original_dir):
    prompts_mod.PROMPTS_DIR = original_dir


def test_list_topics(tmp_path):
    original = prompts_mod.PROMPTS_DIR
    _setup_prompts(tmp_path)
    try:
        topics = list_topics()
        assert "topic_a" in topics
        assert "topic_b" in topics
    finally:
        _teardown(original)


def test_list_prompts(tmp_path):
    original = prompts_mod.PROMPTS_DIR
    _setup_prompts(tmp_path)
    try:
        all_prompts = list_prompts()
        assert len(all_prompts) == 2

        topic_a = list_prompts("topic_a")
        assert len(topic_a) == 1
        assert topic_a[0]["name"] == "prompt1"
    finally:
        _teardown(original)


def test_read_write_prompt(tmp_path):
    original = prompts_mod.PROMPTS_DIR
    prompts_mod.PROMPTS_DIR = tmp_path
    try:
        write_prompt("new_topic", "new_prompt", "Test content")
        content = read_prompt("new_topic", "new_prompt")
        assert content == "Test content"
    finally:
        _teardown(original)


def test_delete_prompt(tmp_path):
    original = prompts_mod.PROMPTS_DIR
    prompts_mod.PROMPTS_DIR = tmp_path
    try:
        write_prompt("del_topic", "del_prompt", "To delete")
        assert delete_prompt("del_topic", "del_prompt") is True
        assert delete_prompt("del_topic", "del_prompt") is False
    finally:
        _teardown(original)


def test_prompt_version():
    v1 = prompt_version("Hello world")
    v2 = prompt_version("Hello world")
    v3 = prompt_version("Different")
    assert v1 == v2
    assert v1 != v3
    assert len(v1) == 8


def test_parse_frontmatter():
    content = "---\ndescription: test\ntemperature: 0.5\nsystem: Be helpful\n---\nBody here"
    meta, body = parse_frontmatter(content)
    assert meta["description"] == "test"
    assert meta["temperature"] == 0.5
    assert meta["system"] == "Be helpful"
    assert body == "Body here"


def test_parse_frontmatter_none():
    content = "No frontmatter here"
    meta, body = parse_frontmatter(content)
    assert meta == {}
    assert body == content


def test_extract_variables():
    body = "Hello {{name}}, your {{item}} is ready. {{name}} again."
    vars = extract_variables(body)
    assert vars == ["name", "item"]  # unique, in order


def test_extract_variables_none():
    assert extract_variables("No variables here") == []


def test_render_template():
    body = "Hello {{name}}, your {{item}} is ready."
    result = render_template(body, {"name": "Alice", "item": "order"})
    assert result == "Hello Alice, your order is ready."
