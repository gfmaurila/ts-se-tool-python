$ErrorActionPreference="Stop"
python -m ruff check src tests
python -m mypy src
python -m pytest -q --cov=src/tsse --cov-report=term-missing
