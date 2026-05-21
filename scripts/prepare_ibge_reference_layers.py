#!/usr/bin/env python3
"""Download and normalize official IBGE reference layers."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huff_curves_br.geodata import download_ibge_reference_layers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download Brazil, state, municipality, and biome IBGE layers.")
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=ROOT / "data" / "reference" / "ibge",
        help="Reference-layer cache directory.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Redownload and rebuild layers.")
    parser.add_argument(
        "--quality",
        default="intermediaria",
        choices=["minima", "intermediaria", "maxima"],
        help="IBGE malhas simplification quality.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = download_ibge_reference_layers(args.reference_dir, quality=args.quality, overwrite=args.overwrite)
    for name, path in paths.items():
        print(f"Wrote {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
