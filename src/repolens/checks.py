from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import CheckResult
from .scanner import scan_path

README_MARKER = "Project README"
LICENSE_MARKER = "License file"


def run_checks(
    root: str | Path,
    *,
    include_hidden: bool = False,
    respect_gitignore: bool = True,
    max_files: int | None = None,
    max_total_size_bytes: int | None = None,
    require_readme: bool = False,
    require_license: bool = False,
    fail_if_dirty: bool = False,
) -> CheckResult:
    scan_limit = max(5000, max_files or 0)
    scan = scan_path(
        root,
        include_hidden=include_hidden,
        respect_gitignore=respect_gitignore,
        max_files=scan_limit,
    )

    failures: list[str] = []
    checked_rules: list[str] = []

    if max_files is not None:
        checked_rules.append(f"max-files<={max_files}")
        if scan.file_count > max_files:
            failures.append(f"File count {scan.file_count} exceeds max {max_files}.")

    if max_total_size_bytes is not None:
        checked_rules.append(f"max-total-size-bytes<={max_total_size_bytes}")
        if scan.total_size_bytes > max_total_size_bytes:
            failures.append(
                f"Total size {scan.total_size_bytes} bytes exceeds max {max_total_size_bytes} bytes."
            )

    if require_readme:
        checked_rules.append("require-readme")
        if README_MARKER not in scan.markers:
            failures.append("README.md is required but was not detected.")

    if require_license:
        checked_rules.append("require-license")
        if LICENSE_MARKER not in scan.markers:
            failures.append("LICENSE is required but was not detected.")

    if fail_if_dirty:
        checked_rules.append("fail-if-dirty")
        if scan.git.dirty:
            failures.append("Git working tree is dirty.")

    return CheckResult(
        root=scan.root,
        passed=not failures,
        failures=failures,
        checked_rules=checked_rules,
        scan=scan,
    )


def render_check(result: CheckResult, output_format: str) -> str:
    if output_format == "json":
        payload = {
            "root": result.root,
            "passed": result.passed,
            "failures": result.failures,
            "checked_rules": result.checked_rules,
            "scan": asdict(result.scan) if result.scan else None,
        }
        return json.dumps(payload, indent=2) + "\n"

    if output_format == "text":
        lines = [
            f"{'PASS' if result.passed else 'FAIL'}: {result.root}",
        ]
        if result.checked_rules:
            lines.append(f"Rules: {', '.join(result.checked_rules)}")
        if result.scan:
            lines.append(
                f"Stats: files={result.scan.file_count}, dirs={result.scan.dir_count}, size={result.scan.total_size_bytes} bytes"
            )
        if result.failures:
            lines.append("Failures:")
            lines.extend(f"- {failure}" for failure in result.failures)
        return "\n".join(lines) + "\n"

    raise ValueError(f"Unsupported format: {output_format}")
