from __future__ import annotations

from pathlib import Path

from repolens.render import render
from repolens.scanner import compare_paths, scan_path


FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"
FIXTURE_VARIANT = Path(__file__).parent / "fixtures" / "sample_repo_variant"


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


def test_render_html_contains_title_and_sections() -> None:
    result = scan_path(FIXTURE)
    output = render(result, "html")
    assert "<!DOCTYPE html>" in output
    assert "<title>Project Report: sample_repo</title>" in output
    assert "Tree Snapshot" in output


def test_render_compare_markdown_contains_sections() -> None:
    result = compare_paths(FIXTURE, FIXTURE_VARIANT)
    output = render(result, "markdown")
    assert "# Project Comparison: sample_repo vs sample_repo_variant" in output
    assert "## Language Deltas" in output
    assert "Only right: Node package" in output


def test_render_compare_json_contains_deltas() -> None:
    result = compare_paths(FIXTURE, FIXTURE_VARIANT)
    output = render(result, "json")
    assert '"file_count_delta": -1' in output
    assert '"JavaScript": 1' in output


def test_render_compare_html_contains_title_and_delta() -> None:
    result = compare_paths(FIXTURE, FIXTURE_VARIANT)
    output = render(result, "html")
    assert "<title>Project Comparison: sample_repo vs sample_repo_variant</title>" in output
    assert "Language Deltas" in output
    assert "Only right: Node package" in output
