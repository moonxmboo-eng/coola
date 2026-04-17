from __future__ import annotations

from pathlib import Path

from repolens.checks import render_check, run_checks


def make_repo(tmp_path: Path, *, with_readme: bool = True, with_license: bool = False) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    if with_readme:
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    if with_license:
        (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    return root


def test_run_checks_passes_for_valid_repo(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, with_license=True)
    result = run_checks(
        repo,
        max_files=10,
        max_total_size_bytes=2000,
        require_readme=True,
        require_license=True,
    )
    assert result.passed is True
    assert result.failures == []


def test_run_checks_reports_failures(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, with_license=False)
    result = run_checks(
        repo,
        max_files=1,
        require_readme=True,
        require_license=True,
    )
    assert result.passed is False
    assert any("exceeds max" in failure for failure in result.failures)
    assert any("LICENSE is required" in failure for failure in result.failures)


def test_render_check_json_contains_passed_flag(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, with_license=True)
    result = run_checks(repo, require_readme=True, require_license=True)
    output = render_check(result, "json")
    assert '"passed": true' in output
