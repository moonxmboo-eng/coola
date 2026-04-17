from __future__ import annotations

import argparse
from pathlib import Path
import sys

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
        choices=["markdown", "json"],
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
        choices=["markdown", "json"],
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

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
