"""CLI module."""

import logging
from pathlib import Path

from jsonargparse import auto_cli

ROOT_DIR = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)


def hello() -> None:
    """Say hello to the user."""
    print('Hello, user!')


def main() -> None:
    """Main entrypoint for the CLI application."""
    auto_cli(
        {
            'hello': hello,
        }
    )


if __name__ == '__main__':
    main()
