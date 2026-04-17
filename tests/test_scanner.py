from __future__ import annotations

from pathlib import Path

from repolens.scanner import scan_path


FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


def test_scan_counts_and_markers() -> None:
    result = scan_path(FIXTURE)
    assert result.project_name == "sample_repo"
    assert result.file_count == 5
    assert result.dir_count >= 3
    assert "Project README" in result.markers
    assert "Python package" in result.markers
    assert result.languages["Python"] == 2
    assert result.languages["JSON"] == 1


def test_scan_tree_contains_expected_entries() -> None:
    result = scan_path(FIXTURE)
    tree_blob = "\n".join(result.tree)
    assert "src/" in tree_blob
    assert "app.py" in tree_blob
    assert "config.json" in tree_blob
