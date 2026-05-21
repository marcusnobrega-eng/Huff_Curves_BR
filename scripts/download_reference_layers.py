#!/usr/bin/env python3
"""Download optional reference layers used by map scripts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huff_curves_br.reference import download_file, extract_zip


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download a boundary, biome, or other reference layer.")
    parser.add_argument("--url", required=True, help="Reference-layer URL.")
    parser.add_argument("--output", type=Path, required=True, help="Downloaded file path.")
    parser.add_argument("--extract-to", type=Path, default=None, help="Extract a downloaded zip to this directory.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="Download timeout.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    downloaded = download_file(
        args.url,
        args.output,
        overwrite=args.overwrite,
        timeout_seconds=args.timeout_seconds,
    )
    print(f"Downloaded: {downloaded}")

    if args.extract_to is not None:
        extracted = extract_zip(downloaded, args.extract_to, overwrite=args.overwrite)
        print(f"Extracted {len(extracted)} paths to: {args.extract_to}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
