from __future__ import annotations

import datetime as dt
import os
import subprocess
from collections import Counter
from pathlib import Path

from pathspec import PathSpec

from .models import CompareResult, FileEntry, GitInfo, ScanResult

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "dist",
    "build",
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".json": "JSON",
    ".md": "Markdown",
    ".toml": "TOML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".html": "HTML",
    ".css": "CSS",
    ".sh": "Shell",
    ".txt": "Text",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".c": "C",
    ".h": "C Header",
    ".cpp": "C++",
}

MARKER_FILES = {
    "pyproject.toml": "Python package",
    "package.json": "Node package",
    "Cargo.toml": "Rust crate",
    "go.mod": "Go module",
    "Dockerfile": "Docker",
    ".github": "GitHub automation",
    "Makefile": "Make automation",
    "README.md": "Project README",
    "LICENSE": "License file",
}


def scan_path(
    root: str | Path,
    *,
    include_hidden: bool = False,
    respect_gitignore: bool = True,
    max_files: int = 5000,
    top_n: int = 5,
) -> ScanResult:
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Path does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root_path}")

    file_count = 0
    dir_count = 0
    total_size = 0
    language_counter: Counter[str] = Counter()
    file_entries: list[tuple[Path, int, float]] = []
    markers = detect_markers(root_path)
    gitignore_spec = load_gitignore_spec(root_path) if respect_gitignore else None
    tree = build_tree(root_path, include_hidden=include_hidden, gitignore_spec=gitignore_spec)

    for current_root, dirs, files in os.walk(root_path):
        current = Path(current_root)
        dirs[:] = [
            name
            for name in sorted(dirs)
            if should_include_name(name, include_hidden=include_hidden)
            and not is_ignored_dir(name)
            and not should_ignore_path(
                (current / name).relative_to(root_path),
                gitignore_spec=gitignore_spec,
                is_dir=True,
            )
        ]

        if current != root_path:
            dir_count += 1

        for file_name in sorted(files):
            if not should_include_name(file_name, include_hidden=include_hidden):
                continue

            path = current / file_name
            if not path.is_file():
                continue
            if should_ignore_path(path.relative_to(root_path), gitignore_spec=gitignore_spec, is_dir=False):
                continue

            stat = path.stat()
            file_count += 1
            total_size += stat.st_size
            file_entries.append((path, stat.st_size, stat.st_mtime))
            language_counter[detect_language(path)] += 1

            if file_count > max_files:
                raise ValueError(f"Directory exceeds max_files={max_files}")

    largest = sorted(file_entries, key=lambda item: item[1], reverse=True)[:top_n]
    newest = sorted(file_entries, key=lambda item: item[2], reverse=True)[:top_n]

    return ScanResult(
        root=str(root_path),
        project_name=root_path.name,
        file_count=file_count,
        dir_count=dir_count,
        total_size_bytes=total_size,
        languages=dict(sorted(language_counter.items(), key=lambda item: (-item[1], item[0]))),
        largest_files=[to_file_entry(root_path, item) for item in largest],
        newest_files=[to_file_entry(root_path, item) for item in newest],
        markers=markers,
        tree=tree,
        git=read_git_info(root_path),
    )


def compare_paths(
    left: str | Path,
    right: str | Path,
    *,
    include_hidden: bool = False,
    respect_gitignore: bool = True,
    max_files: int = 5000,
    top_n: int = 5,
) -> CompareResult:
    left_result = scan_path(
        left,
        include_hidden=include_hidden,
        respect_gitignore=respect_gitignore,
        max_files=max_files,
        top_n=top_n,
    )
    right_result = scan_path(
        right,
        include_hidden=include_hidden,
        respect_gitignore=respect_gitignore,
        max_files=max_files,
        top_n=top_n,
    )

    all_languages = sorted(set(left_result.languages) | set(right_result.languages))
    language_deltas = {
        language: right_result.languages.get(language, 0) - left_result.languages.get(language, 0)
        for language in all_languages
    }

    return CompareResult(
        left=left_result,
        right=right_result,
        file_count_delta=right_result.file_count - left_result.file_count,
        dir_count_delta=right_result.dir_count - left_result.dir_count,
        total_size_delta_bytes=right_result.total_size_bytes - left_result.total_size_bytes,
        language_deltas=language_deltas,
        markers_only_left=sorted(set(left_result.markers) - set(right_result.markers)),
        markers_only_right=sorted(set(right_result.markers) - set(left_result.markers)),
    )


def should_include_name(name: str, *, include_hidden: bool) -> bool:
    if include_hidden:
        return True
    return not name.startswith(".")


def is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIRS or name.endswith(".egg-info")


def detect_language(path: Path) -> str:
    return LANGUAGE_MAP.get(path.suffix.lower(), "Other")


def detect_markers(root: Path) -> list[str]:
    found: list[str] = []
    for name, label in MARKER_FILES.items():
        if (root / name).exists():
            found.append(label)
    return found


def build_tree(
    root: Path,
    *,
    include_hidden: bool,
    gitignore_spec: PathSpec | None,
    max_entries: int = 40,
) -> list[str]:
    lines: list[str] = []
    for path in sorted(root.rglob("*")):
        if len(lines) >= max_entries:
            lines.append("... truncated ...")
            break

        rel = path.relative_to(root)
        parts = rel.parts
        if any(is_ignored_dir(part) for part in parts):
            continue
        if not include_hidden and any(part.startswith(".") for part in parts):
            continue
        if should_ignore_path(rel, gitignore_spec=gitignore_spec, is_dir=path.is_dir()):
            continue

        depth = len(parts) - 1
        prefix = "  " * depth
        suffix = "/" if path.is_dir() else ""
        lines.append(f"{prefix}- {parts[-1]}{suffix}")
    return lines


def load_gitignore_spec(root: Path) -> PathSpec | None:
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return None
    lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    return PathSpec.from_lines("gitignore", lines)


def should_ignore_path(
    rel_path: Path,
    *,
    gitignore_spec: PathSpec | None,
    is_dir: bool,
) -> bool:
    if gitignore_spec is None:
        return False
    normalized = rel_path.as_posix()
    if gitignore_spec.match_file(normalized):
        return True
    if is_dir and gitignore_spec.match_file(f"{normalized}/"):
        return True
    return False


def to_file_entry(root: Path, item: tuple[Path, int, float]) -> FileEntry:
    path, size_bytes, mtime = item
    modified_iso = dt.datetime.fromtimestamp(mtime, tz=dt.timezone.utc).isoformat()
    return FileEntry(
        path=str(path.relative_to(root)),
        size_bytes=size_bytes,
        modified_iso=modified_iso,
    )


def read_git_info(root: Path) -> GitInfo:
    if not (root / ".git").exists():
        return GitInfo()

    branch = run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    commit = run_git(root, ["rev-parse", "--short", "HEAD"])
    status = run_git(root, ["status", "--porcelain"])
    return GitInfo(
        branch=branch or None,
        commit=commit or None,
        dirty=bool(status.strip()) if status else False,
    )


def run_git(root: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return ""
    return completed.stdout.strip()
