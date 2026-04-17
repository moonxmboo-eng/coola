from __future__ import annotations

from pathlib import Path

from repolens.scanner import compare_paths, scan_path


FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"
FIXTURE_VARIANT = Path(__file__).parent / "fixtures" / "sample_repo_variant"


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


def test_compare_paths_detects_deltas() -> None:
    result = compare_paths(FIXTURE, FIXTURE_VARIANT)
    assert result.file_count_delta == -1
    assert result.language_deltas["JavaScript"] == 1
    assert "Node package" in result.markers_only_right
    assert "Python package" in result.markers_only_left
