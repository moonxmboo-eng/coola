from __future__ import annotations

import json
from dataclasses import asdict

from .models import FileEntry, ScanResult


def render(result: ScanResult, output_format: str) -> str:
    if output_format == "json":
        return render_json(result)
    if output_format == "markdown":
        return render_markdown(result)
    raise ValueError(f"Unsupported format: {output_format}")


def render_markdown(result: ScanResult) -> str:
    lines = [
        f"# Project Report: {result.project_name}",
        "",
        "## Summary",
        "",
        f"- Root: `{result.root}`",
        f"- Files: {result.file_count}",
        f"- Directories: {result.dir_count}",
        f"- Total size: {format_bytes(result.total_size_bytes)}",
    ]

    if result.git.branch or result.git.commit:
        lines.extend(
            [
                f"- Git branch: `{result.git.branch or 'unknown'}`",
                f"- Git commit: `{result.git.commit or 'unknown'}`",
                f"- Git dirty: {'yes' if result.git.dirty else 'no'}",
            ]
        )

    lines.extend(["", "## Project Markers", ""])
    if result.markers:
        lines.extend(f"- {marker}" for marker in result.markers)
    else:
        lines.append("- None detected")

    lines.extend(["", "## Languages", ""])
    if result.languages:
        lines.extend(f"- {language}: {count}" for language, count in result.languages.items())
    else:
        lines.append("- No files detected")

    lines.extend(["", "## Largest Files", ""])
    lines.extend(render_entries(result.largest_files))

    lines.extend(["", "## Newest Files", ""])
    lines.extend(render_entries(result.newest_files))

    lines.extend(["", "## Tree Snapshot", ""])
    if result.tree:
        lines.append("```text")
        lines.extend(result.tree)
        lines.append("```")
    else:
        lines.append("No visible files")

    return "\n".join(lines).strip() + "\n"


def render_json(result: ScanResult) -> str:
    payload = {
        "root": result.root,
        "project_name": result.project_name,
        "file_count": result.file_count,
        "dir_count": result.dir_count,
        "total_size_bytes": result.total_size_bytes,
        "languages": result.languages,
        "largest_files": [asdict(entry) for entry in result.largest_files],
        "newest_files": [asdict(entry) for entry in result.newest_files],
        "markers": result.markers,
        "tree": result.tree,
        "git": asdict(result.git),
    }
    return json.dumps(payload, indent=2) + "\n"


def render_entries(entries: list[FileEntry]) -> list[str]:
    if not entries:
        return ["- None"]
    return [
        f"- `{entry.path}` ({format_bytes(entry.size_bytes)}) - {entry.modified_iso}"
        for entry in entries
    ]


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"
