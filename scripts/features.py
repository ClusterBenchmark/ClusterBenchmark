#!/usr/bin/env python3
"""Synthetic input features for graphs that have no node attributes.

Learning-based methods need a feature matrix. When an instance provides none,
the choice of substitute materially changes what the method can do, so it must
be explicit, identical across methods, and reported.

Available representations:

  ones      A single constant 1.0 per vertex. Every vertex is identical, so a
            GNN's first layer receives no vertex-distinguishing signal at all.
            Included because it is the weakest defensible choice and therefore
            a useful lower bound, not because it is a good one.

  ldp       Local Degree Profile: a vertex's degree together with the min, max,
            mean and standard deviation of its neighbours' degrees, log scaled
            and standardised. Five dimensions of genuine structural signal that
            a message-passing network would otherwise spend layers computing.

  rni       Random Node Initialisation: a fixed Gaussian vector per vertex.
            This acts as a distributed unique identifier, recovering the
            expressiveness of a one-hot identity encoding at O(n*d) rather than
            O(n^2) memory. Seeded, so it is reproducible and auditable.

  ldp+rni   Concatenation of the two. The default.

Deliberately excluded: spectral embeddings and random-walk embeddings such as
DeepWalk or node2vec. Both already separate communities before the method
runs, so they would measure the quality of the preprocessing rather than of the
clustering method under evaluation.

Usage:
    python3 scripts/features.py graph.csr --kind ldp+rni --seed 0 --out graph.feat
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import graphio  # noqa: E402

KINDS = ("ones", "ldp", "rni", "ldp+rni")
LDP_DIM = 5
DEFAULT_RNI_DIM = 64

# Vertices are processed in blocks holding at most this many edges, so peak
# memory stays bounded on graphs with billions of edges.
CHUNK_EDGES = 32_000_000


def local_degree_profile(csr, chunk_edges=CHUNK_EDGES):
    """Returns an (n, 5) float32 array of raw LDP values.

    Columns: degree, min, max, mean, std of neighbour degrees.
    """
    V = np.asarray(csr.V)
    E = np.asarray(csr.E)
    n, m = csr.n, csr.m

    out = np.zeros((n, LDP_DIM), dtype=np.float32)
    if n == 0:
        return out

    deg = (V[1:] - V[:-1]).astype(np.float32)
    out[:, 0] = deg
    if m == 0:
        return out

    start = 0
    while start < n:
        # Largest block of vertices whose edges fit in the chunk budget.
        stop = int(np.searchsorted(V, V[start] + chunk_edges, side="right")) - 1
        stop = max(stop, start + 1)
        stop = min(stop, n)

        lo, hi = int(V[start]), int(V[stop])
        if hi > lo:
            nd = deg[E[lo:hi]]
            offsets = (V[start:stop] - lo).astype(np.intp)
            idx = np.clip(offsets, 0, hi - lo - 1)

            block_deg = deg[start:stop]
            nonempty = block_deg > 0

            total = np.add.reduceat(nd, idx)
            total_sq = np.add.reduceat(nd * nd, idx)
            lo_vals = np.minimum.reduceat(nd, idx)
            hi_vals = np.maximum.reduceat(nd, idx)

            safe_deg = np.where(nonempty, block_deg, 1.0)
            mean = total / safe_deg
            var = np.maximum(total_sq / safe_deg - mean * mean, 0.0)

            out[start:stop, 1] = np.where(nonempty, lo_vals, 0.0)
            out[start:stop, 2] = np.where(nonempty, hi_vals, 0.0)
            out[start:stop, 3] = np.where(nonempty, mean, 0.0)
            out[start:stop, 4] = np.where(nonempty, np.sqrt(var), 0.0)

        start = stop

    return out


def standardise(x):
    """log1p to tame heavy-tailed degrees, then zero mean and unit variance."""
    x = np.log1p(np.maximum(x, 0.0, dtype=np.float32), dtype=np.float32)
    mean = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    std[std < 1e-8] = 1.0
    return ((x - mean) / std).astype(np.float32)


def random_node_features(n, dim, seed):
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n, dim), dtype=np.float32)


def build(csr, kind="ldp+rni", seed=0, rni_dim=DEFAULT_RNI_DIM):
    """Builds the feature matrix for a graph with no node attributes."""
    if kind not in KINDS:
        raise ValueError(f"unknown feature kind '{kind}', expected one of {KINDS}")

    n = csr.n
    parts = []

    if kind == "ones":
        return np.ones((n, 1), dtype=np.float32)

    if kind in ("ldp", "ldp+rni"):
        parts.append(standardise(local_degree_profile(csr)))

    if kind in ("rni", "ldp+rni"):
        parts.append(random_node_features(n, rni_dim, seed))

    return parts[0] if len(parts) == 1 else np.concatenate(parts, axis=1)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("graph", help="binary CSR graph file")
    p.add_argument("--kind", default="ldp+rni", choices=KINDS)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--rni-dim", type=int, default=DEFAULT_RNI_DIM)
    p.add_argument("--out", default=None, help="default: <graph>.<kind>.feat")
    p.add_argument("--force", action="store_true", help="regenerate even if cached")
    args = p.parse_args()

    csr = graphio.load_csr(args.graph)

    stem = str(Path(args.graph).with_suffix(""))
    out = Path(args.out) if args.out else Path(f"{stem}.{args.kind.replace('+', '_')}.feat")

    if out.exists() and not args.force:
        print(f"{out} exists, use --force to regenerate", file=sys.stderr)
        return 0

    features = build(csr, kind=args.kind, seed=args.seed, rni_dim=args.rni_dim)
    graphio.write_features(out, features)

    # Provenance, so a cached feature matrix is never anonymous.
    meta = {
        "graph": Path(args.graph).name,
        "n": csr.n,
        "m": csr.m,
        "kind": args.kind,
        "seed": args.seed,
        "rni_dim": args.rni_dim if "rni" in args.kind else None,
        "dim": int(features.shape[1]),
    }
    out.with_suffix(out.suffix + ".meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(
        f"{out}: n={csr.n} dim={features.shape[1]} kind={args.kind} seed={args.seed}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
