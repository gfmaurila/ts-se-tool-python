# Task 05 — Profile Cloner

Status: complete on 2026-09-17.

- Added an application-level full-profile cloner using a sibling staging
  directory and publish-on-success behavior.
- The source profile is validated but never written; the destination must be
  new, and staging is rolled back on failure.
- Preserves all source files and makes the target independently discoverable.
- Internal profile identity/name fields are deliberately not changed because
  available real `profile.sii` fixtures remain opaque containers.

Validation (Python 3.13.15):

- Ruff: PASS
- mypy: PASS
- pytest with coverage: 19 passed, 93.21% (threshold 80%): PASS
- `git diff --check`: PASS
