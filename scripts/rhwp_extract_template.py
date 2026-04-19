#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Template wrapper for future rhwp text extraction integration."
    )
    parser.add_argument("--input", required=True, help="Absolute path to a .hwp or .hwpx file")
    parser.add_argument(
        "--include-tables",
        default="true",
        help="Whether table text should be included (true/false)",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    print(
        "rhwp_extract_template.py is a placeholder. Replace the subprocess section with the real rhwp extraction command.",
        file=sys.stderr,
    )

    # Example shape only — replace with the real extractor call once rhwp integration is available.
    # result = subprocess.run([...], capture_output=True, text=True, check=False)
    # if result.returncode != 0:
    #     print(result.stderr, file=sys.stderr)
    #     return result.returncode
    # print(result.stdout)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
