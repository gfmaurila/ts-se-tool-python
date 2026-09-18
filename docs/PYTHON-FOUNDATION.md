# Python foundation

Task 01 establishes a typed `src/tsse` layout. `core` remains independent of
PySide6 and infrastructure; game-specific behavior is isolated below
`games/ats` and `games/ets2`.

The `tsse --diagnose` command intentionally reports only local runtime state.
It does not discover, read, or modify game profiles. Save discovery and
filesystem access start in later tasks.

Development dependencies are isolated in `.venv`; use `py -3.13 -m venv .venv`
and `.venv\Scripts\python.exe -m pip install -e ".[dev]"` on Windows.
