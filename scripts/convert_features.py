#!/usr/bin/env python3
"""Converts a text feature file to the binary feature format, streaming.

Provided (real) node features arrive as text: an `n dim` header followed by one
whitespace-separated row per vertex. The Python path does not load text at all
(graphio.load_features accepts only the binary format, just as load_csr accepts
only binary CSR), so a large ASCII matrix is never parsed on the training hot
path -- the parse-time spike and peak-memory cost the binary formats removed.

This is the CONVERT step for features, the counterpart to CONVERT for graphs:
run it once per instance and hand the resulting .feat to the harness via
--features, where load_features memory-maps it with no parsing. Conversion
itself streams one row at a time, so it does not hold the matrix in memory
either.

Usage:
    python3 scripts/convert_features.py cora.features --out cora.feat
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import graphio  # noqa: E402


def convert(text_path, out_path):
    """Streams a text `n dim` feature file into the binary format."""
    with open(text_path, "r") as src:
        # First non-empty line is the 'n dim' header.
        header = ""
        for line in src:
            if line.strip():
                header = line
                break
        parts = header.split()
        if len(parts) < 2:
            raise ValueError(f"{text_path}: missing 'n dim' header")
        n, dim = int(parts[0]), int(parts[1])

        with open(out_path, "wb") as dst:
            dst.write(graphio.FEAT_MAGIC.ljust(8, b"\0"))
            dst.write(np.int64(n).tobytes())
            dst.write(np.int32(dim).tobytes())
            dst.write(np.int32(0).tobytes())

            zeros = np.zeros(dim, dtype=np.float32)
            rows = 0
            for line in src:
                stripped = line.strip()
                if not stripped:
                    # A vertex with no listed features is an all-zero row.
                    zeros.tofile(dst)
                    rows += 1
                    continue
                row = np.array(stripped.split(), dtype=np.float32)
                if row.size != dim:
                    raise ValueError(
                        f"{text_path}: row {rows} has {row.size} values, expected dim={dim}"
                    )
                row.tofile(dst)
                rows += 1

    if rows != n:
        raise ValueError(f"{text_path}: header says n={n} but found {rows} rows")
    return n, dim


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("features", help="text feature file with an 'n dim' header")
    p.add_argument("--out", default=None, help="output path (default: <features>.feat)")
    args = p.parse_args()

    src = Path(args.features)
    out = Path(args.out) if args.out else src.with_suffix(".feat")
    n, dim = convert(src, out)
    print(f"{out}: n={n} dim={dim}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
