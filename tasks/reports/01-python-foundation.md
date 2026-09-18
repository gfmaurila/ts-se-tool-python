# Task 01 — Python Foundation

Status: complete on 2026-09-17.

- Added a Python 3.13+ `src` package layout, typed configuration, shared
  logging setup, and a non-invasive `tsse --diagnose` command.
- Configured PySide6, PyInstaller, Ruff, mypy, pytest, pytest-cov, and the
  editable package in `pyproject.toml`.
- Added smoke tests and made test/build scripts use the local `.venv` only.
- The initial Python confirmation used `py -3.13` because `python` still maps
  to the Microsoft Store alias on this machine.

Validation (Python 3.13.15):

- editable install (`.venv\\Scripts\\python.exe -m pip install -e ".[dev]"`): PASS
- Ruff: PASS
- mypy: PASS
- pytest with coverage: 4 passed, 95.35% (threshold 80%): PASS
- `git diff --check`: PASS
