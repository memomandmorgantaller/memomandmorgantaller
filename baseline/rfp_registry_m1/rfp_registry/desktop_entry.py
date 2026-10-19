"""Executable entry point: dispatch parser workers before importing the window UI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--parse-worker":
        from rfp_registry.extraction import worker_main

        worker_main(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "--smoke-test":
        parser = argparse.ArgumentParser()
        parser.add_argument("--smoke-test", action="store_true")
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--result", type=Path, required=True)
        args = parser.parse_args()
        from rfp_registry.desktop_smoke import smoke_test

        smoke_test(args.output, args.result)
    else:
        from rfp_registry.desktop import launch

        launch()


if __name__ == "__main__":
    main()
