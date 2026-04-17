from __future__ import annotations

import html
import json
from dataclasses import asdict

from .models import CompareResult, FileEntry, ScanResult


def render(result: ScanResult | CompareResult, output_format: str) -> str:
    if output_format == "html":
        return render_html(result)
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


def render_html(result: ScanResult | CompareResult) -> str:
    if isinstance(result, CompareResult):
        return render_compare_html(result)
    return render_scan_html(result)


def render_scan_html(result: ScanResult) -> str:
    summary_items = [
        ("Root", result.root),
        ("Files", str(result.file_count)),
        ("Directories", str(result.dir_count)),
        ("Total size", format_bytes(result.total_size_bytes)),
    ]
    if result.git.branch or result.git.commit:
        summary_items.extend(
            [
                ("Git branch", result.git.branch or "unknown"),
                ("Git commit", result.git.commit or "unknown"),
                ("Git dirty", "yes" if result.git.dirty else "no"),
            ]
        )

    body = [
        section_list("Summary", summary_items),
        section_simple_list("Project Markers", result.markers or ["None detected"]),
        section_simple_list("Languages", [f"{name}: {count}" for name, count in result.languages.items()] or ["No files detected"]),
        section_simple_list("Largest Files", format_entries(result.largest_files) or ["None"]),
        section_simple_list("Newest Files", format_entries(result.newest_files) or ["None"]),
        section_code_block("Tree Snapshot", result.tree or ["No visible files"]),
    ]
    return html_page(f"Project Report: {result.project_name}", body)


def render_compare_html(result: CompareResult) -> str:
    language_lines = [
        f"{language}: {format_signed(delta)}"
        for language, delta in result.language_deltas.items()
        if delta != 0
    ] or ["No language changes"]

    marker_lines = (
        [f"Only left: {marker}" for marker in result.markers_only_left]
        + [f"Only right: {marker}" for marker in result.markers_only_right]
    ) or ["Markers match"]

    body = [
        section_list(
            "Summary",
            [
                ("Left", result.left.root),
                ("Right", result.right.root),
                ("File delta", format_signed(result.file_count_delta)),
                ("Directory delta", format_signed(result.dir_count_delta)),
                ("Size delta", format_signed_bytes(result.total_size_delta_bytes)),
            ],
        ),
        section_simple_list("Language Deltas", language_lines),
        section_simple_list("Marker Differences", marker_lines),
        section_list(
            "Git Snapshot",
            [
                ("Left branch", result.left.git.branch or "unknown"),
                ("Right branch", result.right.git.branch or "unknown"),
                ("Left dirty", "yes" if result.left.git.dirty else "no"),
                ("Right dirty", "yes" if result.right.git.dirty else "no"),
            ],
        ),
    ]
    return html_page(
        f"Project Comparison: {result.left.project_name} vs {result.right.project_name}",
        body,
    )


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


def format_entries(entries: list[FileEntry]) -> list[str]:
    return [
        f"{entry.path} ({format_bytes(entry.size_bytes)}) - {entry.modified_iso}"
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


def html_page(title: str, sections: list[str]) -> str:
    escaped_title = html.escape(title)
    body = "\n".join(sections)
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>{escaped_title}</title>\n"
        "  <style>\n"
        "    :root { color-scheme: light; }\n"
        "    body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #f4efe6; color: #1f2937; }\n"
        "    main { max-width: 920px; margin: 0 auto; padding: 32px 20px 64px; }\n"
        "    h1 { font-size: 2.2rem; margin-bottom: 0.5rem; }\n"
        "    section { background: #fffdf8; border: 1px solid #e5dccf; border-radius: 16px; padding: 18px 20px; margin-top: 18px; box-shadow: 0 8px 24px rgba(39, 32, 24, 0.06); }\n"
        "    h2 { margin-top: 0; font-size: 1.1rem; }\n"
        "    ul { margin: 0; padding-left: 20px; }\n"
        "    li { margin: 6px 0; }\n"
        "    code, pre { font-family: 'JetBrains Mono', 'Consolas', monospace; }\n"
        "    pre { white-space: pre-wrap; background: #f7f1e8; border-radius: 12px; padding: 14px; overflow-x: auto; }\n"
        "    .label { font-weight: 700; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        f"    <h1>{escaped_title}</h1>\n"
        f"{body}\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def section_list(title: str, items: list[tuple[str, str]]) -> str:
    lines = "".join(
        f"      <li><span class=\"label\">{html.escape(label)}:</span> {html.escape(value)}</li>\n"
        for label, value in items
    )
    return f"    <section>\n      <h2>{html.escape(title)}</h2>\n      <ul>\n{lines}      </ul>\n    </section>"


def section_simple_list(title: str, items: list[str]) -> str:
    lines = "".join(f"      <li>{html.escape(item)}</li>\n" for item in items)
    return f"    <section>\n      <h2>{html.escape(title)}</h2>\n      <ul>\n{lines}      </ul>\n    </section>"


def section_code_block(title: str, lines: list[str]) -> str:
    content = "\n".join(html.escape(line) for line in lines)
    return (
        f"    <section>\n"
        f"      <h2>{html.escape(title)}</h2>\n"
        f"      <pre>{content}</pre>\n"
        f"    </section>"
    )
