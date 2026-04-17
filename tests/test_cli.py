from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample_repo"
FIXTURE_VARIANT = ROOT / "tests" / "fixtures" / "sample_repo_variant"
GITIGNORE_FIXTURE = ROOT / "tests" / "fixtures" / "gitignore_repo"


def test_cli_markdown_stdout() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "repolens.cli", "scan", str(FIXTURE)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "# Project Report: sample_repo" in completed.stdout


def test_cli_json_output_file(tmp_path: Path) -> None:
    target = tmp_path / "report.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "repolens.cli",
            "scan",
            str(FIXTURE),
            "--format",
            "json",
            "--output",
            str(target),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = target.read_text(encoding="utf-8")
    assert '"project_name": "sample_repo"' in payload


def test_cli_compare_markdown_stdout() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "repolens.cli", "compare", str(FIXTURE), str(FIXTURE_VARIANT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "# Project Comparison: sample_repo vs sample_repo_variant" in completed.stdout


def test_cli_compare_json_output_file(tmp_path: Path) -> None:
    target = tmp_path / "compare.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "repolens.cli",
            "compare",
            str(FIXTURE),
            str(FIXTURE_VARIANT),
            "--format",
            "json",
            "--output",
            str(target),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = target.read_text(encoding="utf-8")
    assert '"file_count_delta": -1' in payload


def test_cli_scan_respects_gitignore_by_default() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "repolens.cli", "scan", str(GITIGNORE_FIXTURE), "--include-hidden"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ignored.txt" not in completed.stdout


def test_cli_scan_can_disable_gitignore() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "repolens.cli",
            "scan",
            str(GITIGNORE_FIXTURE),
            "--include-hidden",
            "--no-gitignore",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ignored.txt" in completed.stdout
