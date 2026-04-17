from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .checks import render_check, run_checks
from .render import render
from .scanner import compare_paths, scan_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repolens",
        description="Generate a readable project report for a local repository or directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a directory and generate a report.")
    scan_parser.add_argument("path", nargs="?", default=".", help="Directory to scan.")
    scan_parser.add_argument(
        "--format",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format.",
    )
    scan_parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to write the report to.",
    )
    scan_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories.",
    )
    scan_parser.add_argument(
        "--gitignore",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Respect the root .gitignore file when scanning.",
    )
    scan_parser.add_argument(
        "--max-files",
        type=int,
        default=5000,
        help="Abort if the directory contains more than this many files.",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two directories and generate a delta report.",
    )
    compare_parser.add_argument("left", help="Baseline directory.")
    compare_parser.add_argument("right", help="Directory to compare against the baseline.")
    compare_parser.add_argument(
        "--format",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format.",
    )
    compare_parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to write the report to.",
    )
    compare_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories.",
    )
    compare_parser.add_argument(
        "--gitignore",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Respect the root .gitignore file in both directories.",
    )
    compare_parser.add_argument(
        "--max-files",
        type=int,
        default=5000,
        help="Abort if either directory contains more than this many files.",
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Run policy checks against a directory and exit non-zero on failure.",
    )
    check_parser.add_argument("path", nargs="?", default=".", help="Directory to check.")
    check_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    check_parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to write the check result to.",
    )
    check_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories.",
    )
    check_parser.add_argument(
        "--gitignore",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Respect the root .gitignore file when checking.",
    )
    check_parser.add_argument(
        "--max-files",
        type=int,
        help="Fail if file count exceeds this value.",
    )
    check_parser.add_argument(
        "--max-total-size-bytes",
        type=int,
        help="Fail if total size exceeds this many bytes.",
    )
    check_parser.add_argument(
        "--require-readme",
        action="store_true",
        help="Fail if README.md is not detected.",
    )
    check_parser.add_argument(
        "--require-license",
        action="store_true",
        help="Fail if LICENSE is not detected.",
    )
    check_parser.add_argument(
        "--fail-if-dirty",
        action="store_true",
        help="Fail if the Git working tree is dirty.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        result = scan_path(
            args.path,
            include_hidden=args.include_hidden,
            respect_gitignore=args.gitignore,
            max_files=args.max_files,
        )
        payload = render(result, args.format)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0

    if args.command == "compare":
        result = compare_paths(
            args.left,
            args.right,
            include_hidden=args.include_hidden,
            respect_gitignore=args.gitignore,
            max_files=args.max_files,
        )
        payload = render(result, args.format)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0

    if args.command == "check":
        result = run_checks(
            args.path,
            include_hidden=args.include_hidden,
            respect_gitignore=args.gitignore,
            max_files=args.max_files,
            max_total_size_bytes=args.max_total_size_bytes,
            require_readme=args.require_readme,
            require_license=args.require_license,
            fail_if_dirty=args.fail_if_dirty,
        )
        payload = render_check(result, args.format)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
        return 0 if result.passed else 1

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
