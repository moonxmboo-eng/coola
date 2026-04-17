from __future__ import annotations

import json
from dataclasses import asdict

from .models import CompareResult, FileEntry, ScanResult


def render(result: ScanResult | CompareResult, output_format: str) -> str:
    if output_format == "json":
        return render_json(result)
    if output_format == "markdown":
        return render_markdown(result)
    raise ValueError(f"Unsupported format: {output_format}")


def render_markdown(result: ScanResult | CompareResult) -> str:
    if isinstance(result, CompareResult):
        return render_compare_markdown(result)
    return render_scan_markdown(result)


def render_scan_markdown(result: ScanResult) -> str:
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


def render_compare_markdown(result: CompareResult) -> str:
    lines = [
        f"# Project Comparison: {result.left.project_name} vs {result.right.project_name}",
        "",
        "## Summary",
        "",
        f"- Left: `{result.left.root}`",
        f"- Right: `{result.right.root}`",
        f"- File delta: {format_signed(result.file_count_delta)}",
        f"- Directory delta: {format_signed(result.dir_count_delta)}",
        f"- Size delta: {format_signed_bytes(result.total_size_delta_bytes)}",
        "",
        "## Language Deltas",
        "",
    ]

    if result.language_deltas:
        lines.extend(
            f"- {language}: {format_signed(delta)}"
            for language, delta in result.language_deltas.items()
            if delta != 0
        )
        if lines[-1] == "":
            lines.append("- No language changes")
    else:
        lines.append("- No language changes")

    if lines[-1] == "":
        lines.append("- No language changes")

    lines.extend(["", "## Marker Differences", ""])
    if result.markers_only_left:
        lines.extend(f"- Only left: {marker}" for marker in result.markers_only_left)
    if result.markers_only_right:
        lines.extend(f"- Only right: {marker}" for marker in result.markers_only_right)
    if not result.markers_only_left and not result.markers_only_right:
        lines.append("- Markers match")

    lines.extend(["", "## Git Snapshot", ""])
    lines.extend(
        [
            f"- Left branch: `{result.left.git.branch or 'unknown'}`",
            f"- Right branch: `{result.right.git.branch or 'unknown'}`",
            f"- Left dirty: {'yes' if result.left.git.dirty else 'no'}",
            f"- Right dirty: {'yes' if result.right.git.dirty else 'no'}",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def render_json(result: ScanResult | CompareResult) -> str:
    if isinstance(result, CompareResult):
        payload = {
            "left": asdict(result.left),
            "right": asdict(result.right),
            "file_count_delta": result.file_count_delta,
            "dir_count_delta": result.dir_count_delta,
            "total_size_delta_bytes": result.total_size_delta_bytes,
            "language_deltas": result.language_deltas,
            "markers_only_left": result.markers_only_left,
            "markers_only_right": result.markers_only_right,
        }
        return json.dumps(payload, indent=2) + "\n"

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


def format_signed(value: int) -> str:
    return f"{value:+d}"


def format_signed_bytes(size: int) -> str:
    sign = "+" if size >= 0 else "-"
    return f"{sign}{format_bytes(abs(size))}"
