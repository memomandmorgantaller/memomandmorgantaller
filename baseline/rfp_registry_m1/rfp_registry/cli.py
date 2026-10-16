"""Local intake and evidence CLI. Exit 0=complete, 2=exceptions, 1=fatal."""

import argparse
import json
import sys
from pathlib import Path

from .engine import Limits, Processor
from .pipeline import register


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local RFP Registry: intake and source-linked evidence"
    )
    parser.add_argument(
        "--source", type=Path, help="ZIP file or source directory (required unless --resume)"
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="New/empty package output directory"
    )
    parser.add_argument(
        "--project", help="Explicitly selected project ID (required unless --resume)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume extraction from existing manifest, verifying hashes",
    )
    parser.add_argument(
        "--intake-only",
        action="store_true",
        help="Only preserve/inventory input (baseline workflow)",
    )
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--max-total-gb", type=float, default=5)
    args = parser.parse_args()
    if args.max_depth < 0 or not 0 < args.max_total_gb <= 100:
        parser.error("Limits must be positive (depth may be zero); total must be <=100 GB")
    if not args.resume and (args.source is None or not args.project):
        parser.error("--source and --project are required for a new intake")
    if args.resume and (args.source or args.project or args.intake_only):
        parser.error("--resume uses the existing package; omit source/project/intake-only")
    try:
        if args.resume:
            result = json.loads((args.output / "manifest.json").read_text(encoding="utf-8"))[
                "summary"
            ]
        else:
            limits = Limits(
                max_depth=args.max_depth, max_total_bytes=int(args.max_total_gb * 1_000_000_000)
            )
            result = Processor(args.source, args.output, args.project, limits).run()
        if not args.intake_only:
            result["extraction"] = register(args.output)
        print(json.dumps(result, indent=2))
        if result["failed_entries"] or result.get("extraction", {}).get("exceptions"):
            print(
                "Exceptions require review; inspect manifest.json and extractions.json",
                file=sys.stderr,
            )
            raise SystemExit(2)
    except (OSError, ValueError) as error:
        print(f"Registry failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
