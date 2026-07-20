#!/usr/bin/env python3
"""Deterministically extracts the code cells of a Jupyter notebook to a script.

Some methods are published only as a notebook. To keep the same provenance
chain as the other solvers, we clone upstream at a pinned commit, extract the
code mechanically here, and apply a small patch on top. The extraction must be
byte stable or the patch rots, which is why this does not use nbconvert:
nbconvert emits `# In[n]:` markers and version dependent headers that change
between releases.

A notebook is just JSON, so no third party dependency is needed.

Usage:
    python3 scripts/nbextract.py GNNS.ipynb --out GNNS.py --expect-sha256 <hex>
"""

import argparse
import hashlib
import json
import sys


def extract(notebook, comment_magics=True):
    """Returns the concatenated source of every code cell."""
    cells = notebook.get("cells", [])
    chunks = []

    for index, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue

        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        if not source.strip():
            continue

        lines = []
        for line in source.split("\n"):
            stripped = line.lstrip()
            # IPython magics and shell escapes are not valid Python. Comment
            # them out rather than dropping them, so the patch context and the
            # relationship to the original cell stay visible.
            if comment_magics and (stripped.startswith("!") or stripped.startswith("%")):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}# nbextract: {stripped}")
            else:
                lines.append(line)

        chunks.append(f"# nbextract: cell {index}\n" + "\n".join(lines).rstrip() + "\n")

    return "\n".join(chunks)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("notebook")
    p.add_argument("--out", required=True)
    p.add_argument(
        "--expect-sha256",
        default=None,
        help="fail if the notebook does not hash to this, catching upstream drift",
    )
    p.add_argument("--keep-magics", action="store_true")
    args = p.parse_args()

    raw = open(args.notebook, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()

    if args.expect_sha256 and digest != args.expect_sha256:
        print(
            f"error: {args.notebook} has sha256 {digest},\n"
            f"       expected {args.expect_sha256}.\n"
            f"       Upstream changed; review the diff and update the patch.",
            file=sys.stderr,
        )
        return 1

    notebook = json.loads(raw)
    code = extract(notebook, comment_magics=not args.keep_magics)

    header = (
        "# Extracted from a Jupyter notebook by scripts/nbextract.py.\n"
        "# This file is the authors' code, mechanically converted. Our changes\n"
        "# are applied separately as a patch; see the solver's build.sh.\n"
        f"# source: {args.notebook}\n"
        f"# sha256: {digest}\n\n"
    )

    with open(args.out, "w") as f:
        f.write(header + code)

    n_code = sum(1 for c in notebook.get("cells", []) if c.get("cell_type") == "code")
    print(
        f"{args.out}: {n_code} code cells, {len(code.splitlines())} lines "
        f"(notebook sha256 {digest[:12]})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
