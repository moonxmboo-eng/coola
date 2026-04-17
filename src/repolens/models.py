from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GitInfo:
    branch: str | None = None
    commit: str | None = None
    dirty: bool = False


@dataclass(slots=True)
class FileEntry:
    path: str
    size_bytes: int
    modified_iso: str


@dataclass(slots=True)
class ScanResult:
    root: str
    project_name: str
    file_count: int
    dir_count: int
    total_size_bytes: int
    languages: dict[str, int] = field(default_factory=dict)
    largest_files: list[FileEntry] = field(default_factory=list)
    newest_files: list[FileEntry] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    tree: list[str] = field(default_factory=list)
    git: GitInfo = field(default_factory=GitInfo)
