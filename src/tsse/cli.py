"""Minimal diagnostics CLI; game discovery and save edits belong to later tasks."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from tsse.config import AppSettings
from tsse.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    """Create the command parser."""
    parser = argparse.ArgumentParser(prog="tsse", description="TS SE Tool diagnostics")
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="print non-invasive runtime diagnostics as JSON",
    )
    parser.add_argument("--log-level", default="INFO", help="logging level (default: INFO)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the diagnostics command without reading or changing game data."""
    arguments = build_parser().parse_args(argv)
    configure_logging(arguments.log_level)
    if not arguments.diagnose:
        build_parser().print_help()
        return 0

    settings = AppSettings.defaults()
    print(
        json.dumps(
            {
                "data_directory": str(settings.data_directory),
                "python_version": ".".join(map(str, sys.version_info[:3])),
                "status": "foundation-ready",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
