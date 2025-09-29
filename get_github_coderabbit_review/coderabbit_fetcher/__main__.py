"""Entry point for running coderabbit_fetcher as a module."""

import sys

from .cli.main import main

if __name__ == "__main__":
    sys.exit(main())
