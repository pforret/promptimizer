import hashlib
import re
from pathlib import Path

import yaml

PROMPTS_DIR = Path("input/prompts")


def list_topics() -> list[str]:
    if not PROMPTS_DIR.exists():
        return []
    return sorted(d.name for d in PROMPTS_DIR.iterdir() if d.is_dir())


def list_prompts(topic: str | None = None) -> list[dict]:
    results = []
    if topic:
        dirs = [PROMPTS_DIR / topic]
    else:
        dirs = [d for d in PROMPTS_DIR.iterdir() if d.is_dir()] if PROMPTS_DIR.exists() else []

    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.stem == "system":
                continue
            results.append({
                "topic": d.name,
                "name": f.stem,
                "path": str(f),
            })
    return results


def read_prompt(topic: str, name: str) -> str:
    path = PROMPTS_DIR / topic / f"{name}.md"
    return path.read_text(encoding="utf-8")


def write_prompt(topic: str, name: str, content: str) -> Path:
    path = PROMPTS_DIR / topic / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def delete_prompt(topic: str, name: str) -> bool:
    path = PROMPTS_DIR / topic / f"{name}.md"
    if path.exists():
        path.unlink()
        # Remove empty topic dir
        if not any(path.parent.iterdir()):
            path.parent.rmdir()
        return True
    return False


def get_system_prompt(topic: str) -> str | None:
    """Read system.md from a topic folder, if it exists."""
    path = PROMPTS_DIR / topic / "system.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return None


def prompt_version(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from prompt content. Returns (metadata, body)."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}, content

    body = parts[2].strip()
    return meta, body


def extract_variables(body: str) -> list[str]:
    """Find all {{variable}} placeholders in prompt body. Returns unique names in order."""
    seen = set()
    result = []
    for match in re.findall(r"\{\{(\w+)\}\}", body):
        if match not in seen:
            seen.add(match)
            result.append(match)
    return result


def render_template(body: str, variables: dict[str, str]) -> str:
    """Replace {{variable}} placeholders with values."""
    result = body
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", value)
    return result
