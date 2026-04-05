from pathlib import Path

OUTPUT_DIR = Path("docs/output")


def export_invocations(invocations: list[dict], output_dir: Path | None = None) -> list[Path]:
    """Export invocations grouped by topic/name as Markdown files. Returns list of created files."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[dict]] = {}
    for inv in invocations:
        key = f"{inv['prompt_topic']}/{inv['prompt_name']}"
        grouped.setdefault(key, []).append(inv)

    created_files = []
    for key, runs in sorted(grouped.items()):
        topic, name = key.split("/", 1)
        file_dir = out / topic
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / f"{name}.md"

        lines = [
            f"# {topic}/{name}",
            "",
            f"Total runs: {len(runs)}",
            "",
        ]

        for run in runs:
            cost_str = f"${run['cost_usd']:.6f}" if run.get("cost_usd") else "pending"
            lines.extend([
                f"## Run #{run['id']} - {run['created_at']}",
                "",
                f"- **Model**: {run['model_id']}",
                f"- **Temperature**: {run.get('temperature', 'N/A')}",
                f"- **Tokens**: {run.get('prompt_tokens', '?')} / {run.get('completion_tokens', '?')} / {run.get('total_tokens', '?')}",
                f"- **Cost**: {cost_str}",
                f"- **Latency**: {run.get('latency_ms', '?')} ms",
                f"- **Status**: {run.get('status', 'unknown')}",
                "",
                "<details><summary>Prompt</summary>",
                "",
                "```",
                run.get("full_prompt", ""),
                "```",
                "",
                "</details>",
                "",
                "<details><summary>Response</summary>",
                "",
                run.get("full_response", "") or "_No response_",
                "",
                "</details>",
                "",
                "---",
                "",
            ])

        file_path.write_text("\n".join(lines), encoding="utf-8")
        created_files.append(file_path)

    # Generate index
    index_path = out / "index.md"
    index_lines = ["# Promptimizer Exports", ""]
    for key in sorted(grouped.keys()):
        topic, name = key.split("/", 1)
        count = len(grouped[key])
        index_lines.append(f"- [{topic}/{name}]({topic}/{name}.md) ({count} runs)")
    index_lines.append("")
    index_path.write_text("\n".join(index_lines), encoding="utf-8")
    created_files.append(index_path)

    return created_files
