"""Logging setup shared by command-line and desktop entry points."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure concise process logging once."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
