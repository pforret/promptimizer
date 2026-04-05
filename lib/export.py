import re
from pathlib import Path

OUTPUT_DIR = Path("output")


def _sanitize(name: str) -> str:
    """Replace filesystem-unsafe chars with dashes."""
    return re.sub(r"[/:]+", "-", re.sub(r"[^\w./:-]", "", name)).strip("-")


def export_invocations(invocations: list[dict], output_dir: Path | None = None) -> list[Path]:
    """Export each valid invocation as an individual Markdown file.

    Path: <output>/<topic>/<prompt_name>/<yyyymmdd>.<model>.<uniq>.md
    Skips invocations without a response.
    """
    out = output_dir or OUTPUT_DIR
    created_files = []

    for inv in invocations:
        if inv.get("status") != "success" or not inv.get("full_response"):
            continue

        topic = inv["prompt_topic"]
        name = inv["prompt_name"]
        date_str = inv["created_at"][:10].replace("-", "")
        model_short = _sanitize(inv["model_id"].rsplit("/", 1)[-1])
        uniq = str(inv["id"])

        file_dir = out / topic / name
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / f"{date_str}.{model_short}.{uniq}.md"

        cpmi = f"${inv['cost_usd'] * 1000:.2f}/1Ki" if inv.get("cost_usd") else "pending"
        latency_ms = inv.get("latency_ms")
        latency_str = f"{latency_ms / 1000:.1f}s" if latency_ms else "?"
        lines = [
            f"# {topic} / {name} / {inv['model_id']}",
            "",
            f"- **Date**: {inv['created_at']}",
            f"- **Model**: {inv['model_id']}",
            f"- **Temperature**: {inv.get('temperature', 'N/A')}",
            f"- **Tokens**: {inv.get('prompt_tokens', '?')} / {inv.get('completion_tokens', '?')} / {inv.get('total_tokens', '?')}",
            f"- **CPMI**: {cpmi}",
            f"- **Latency**: {latency_str}",
            f"- **Version**: {inv.get('prompt_version', '?')}",
            "",
            "## Prompt",
            "",
            "```",
            inv.get("full_prompt", ""),
            "```",
            "",
            "## Response",
            "",
            inv["full_response"],
            "",
        ]

        file_path.write_text("\n".join(lines), encoding="utf-8")
        created_files.append(file_path)

    return created_files
