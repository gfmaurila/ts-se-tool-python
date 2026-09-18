# Task 00 — Analyze legacy

Status: task deliverable complete; automation gates unavailable in this checkout.

- Mapped the extracted C# 0.3.11.0 entry point, WinForms screens, profile/save
  paths, native decoder, parser/writer, clone behavior, dependencies, and
  resources in `docs/LEGACY-MAPPING.md`.
- Recorded the safety gap: legacy direct writes and typed regeneration are not
  suitable for the new lossless, backed-up, atomic-write contract.
- No Python or fixture files were modified.

Validation:

- `git diff --check`: PASS.
- `ruff check .`: BLOCKED — `ruff` is not installed/on `PATH`.
- `mypy .`: BLOCKED — the Windows Python launcher points to the Microsoft Store;
  no usable Python runtime is on `PATH`.
- `pytest -q`: BLOCKED — `pytest` is not installed/on `PATH`.
