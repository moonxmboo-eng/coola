from __future__ import annotations

from pathlib import Path

from repolens.render import render
from repolens.scanner import scan_path


FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


def test_render_markdown_contains_sections() -> None:
    result = scan_path(FIXTURE)
    output = render(result, "markdown")
    assert "# Project Report: sample_repo" in output
    assert "## Languages" in output
    assert "## Largest Files" in output


def test_render_json_contains_project_name() -> None:
    result = scan_path(FIXTURE)
    output = render(result, "json")
    assert '"project_name": "sample_repo"' in output
