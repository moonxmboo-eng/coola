# repolens

`repolens` is a local-first CLI that scans a repository or directory and turns it into a readable project brief.

It is designed for:

- quick codebase onboarding
- README supplements
- repository health snapshots
- local project audits before publishing

## Features

- scans any local directory
- outputs Markdown, JSON, or HTML
- shows file and directory counts
- detects language breakdown by extension
- reports largest files
- highlights newest files
- detects common project markers
- reads basic Git metadata when available
- compares two directories or repositories
- respects the root `.gitignore` by default
- checks repositories against simple release or CI rules

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Usage

Generate a Markdown report:

```bash
repolens scan /path/to/project
```

Generate JSON:

```bash
repolens scan /path/to/project --format json
```

Generate HTML:

```bash
repolens scan /path/to/project --format html --output reports/project-report.html
```

Write the report to a file:

```bash
repolens scan /path/to/project --output reports/project-report.md
```

Include hidden files:

```bash
repolens scan /path/to/project --include-hidden
```

Disable `.gitignore` filtering:

```bash
repolens scan /path/to/project --no-gitignore
```

Compare two repositories:

```bash
repolens compare /path/to/baseline /path/to/candidate
```

Write a JSON comparison report:

```bash
repolens compare repo-a repo-b --format json --output reports/diff.json
```

Write an HTML comparison report:

```bash
repolens compare repo-a repo-b --format html --output reports/diff.html
```

Run repository checks:

```bash
repolens check . --require-readme --require-license --max-files 200
```

Emit machine-readable check output:

```bash
repolens check . --format json --output reports/check.json
```

## Example output

```text
# Project Report: sample_repo

- Root: /tmp/sample_repo
- Files: 6
- Directories: 3
- Total size: 1.8 KB
```

## Development

Run tests:

```bash
. .venv/bin/activate
python -m pytest
```

GitHub Actions will run the same test suite on Python 3.11 and 3.12 for every push to `main` and for pull requests.

Build a source distribution and wheel locally:

```bash
. .venv/bin/activate
python -m build
python -m twine check dist/*
```

Create a GitHub release package build by pushing a tag like `v0.1.0`. The release workflow will build the package and attach the wheel and sdist to the GitHub release.

Run a local scan against the project itself:

```bash
repolens scan .
```
