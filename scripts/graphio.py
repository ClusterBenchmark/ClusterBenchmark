"""Reader for the binary CSR format produced by CONVERT.

Every Python solver loads graphs through this module so that parsing cost and
parsing memory are identical across implementations, and are not mistaken for
properties of the clustering method itself.

The arrays are memory mapped, so loading a graph costs no measurable time and
no resident memory beyond what is actually touched.
"""

import os
import numpy as np

MAGIC = b"CBCSRv1"
MAGIC_LEN = 8
HEADER_LEN = 32

FLAG_EDGE_WEIGHTS = 1
FLAG_VERTEX_WEIGHTS = 2


class CSR:
    """Compressed sparse row graph.

    Attributes:
        n, m: vertex count and directed edge count (m == V[n]).
        V: int64 offsets, length n + 1.
        E: int32 neighbors, length m. Each undirected edge appears twice.
        EW, VW: int64 weights, or None when the graph is unweighted.
    """

    __slots__ = ("n", "m", "V", "E", "EW", "VW", "path")

    def __init__(self, n, m, V, E, EW, VW, path):
        self.n = n
        self.m = m
        self.V = V
        self.E = E
        self.EW = EW
        self.VW = VW
        self.path = path

    @property
    def n_edges(self):
        """Number of undirected edges."""
        return self.m // 2

    def degrees(self):
        return np.diff(self.V)

    def sources(self):
        """int32 array of length m giving the tail of each directed edge."""
        return np.repeat(np.arange(self.n, dtype=np.int32), self.degrees())

    def edges_upper(self):
        """(k, 2) int32 array holding each undirected edge exactly once.

        This is the form most graph libraries want for construction. It is the
        only place where we materialise an array proportional to m, and it is
        still an order of magnitude smaller than a Python list of tuples.
        """
        src = self.sources()
        mask = src < self.E
        return np.column_stack((src[mask], self.E[mask]))

    def weights_upper(self):
        """Edge weights aligned with edges_upper(), or None if unweighted."""
        if self.EW is None:
            return None
        src = self.sources()
        mask = src < self.E
        return np.asarray(self.EW)[mask]

    def to_scipy_csr(self):
        from scipy.sparse import csr_matrix

        data = (
            np.ones(self.m, dtype=np.float64)
            if self.EW is None
            else np.asarray(self.EW, dtype=np.float64)
        )
        return csr_matrix(
            (data, np.asarray(self.E), np.asarray(self.V)), shape=(self.n, self.n)
        )

    def to_igraph(self):
        import igraph as ig

        g = ig.Graph(n=self.n, edges=self.edges_upper().tolist())
        w = self.weights_upper()
        if w is not None:
            g.es["weight"] = w.tolist()
        return g


def load_csr(path):
    """Memory maps a binary CSR file."""
    with open(path, "rb") as f:
        header = f.read(HEADER_LEN)

    if len(header) < HEADER_LEN or not header.startswith(MAGIC):
        raise ValueError(
            f"{path} is not a binary CSR file. "
            f"Run CONVERT on the METIS graph first."
        )

    n, m = np.frombuffer(header, dtype=np.int64, count=2, offset=MAGIC_LEN)
    (flags,) = np.frombuffer(header, dtype=np.int32, count=1, offset=MAGIC_LEN + 16)
    n, m, flags = int(n), int(m), int(flags)

    offset = HEADER_LEN
    V = np.memmap(path, dtype=np.int64, mode="r", offset=offset, shape=(n + 1,))
    offset += 8 * (n + 1)
    E = np.memmap(path, dtype=np.int32, mode="r", offset=offset, shape=(m,))
    offset += 4 * m

    EW = None
    if flags & FLAG_EDGE_WEIGHTS:
        EW = np.memmap(path, dtype=np.int64, mode="r", offset=offset, shape=(m,))
        offset += 8 * m

    VW = None
    if flags & FLAG_VERTEX_WEIGHTS:
        VW = np.memmap(path, dtype=np.int64, mode="r", offset=offset, shape=(n,))
        offset += 8 * n

    expected = offset
    actual = os.path.getsize(path)
    if actual < expected:
        raise ValueError(f"{path} is truncated: expected {expected} bytes, found {actual}")

    return CSR(n=n, m=m, V=V, E=E, EW=EW, VW=VW, path=path)


FEAT_MAGIC = b"CBFEAv1"
FEAT_HEADER_LEN = 24


def write_features(path, features):
    """Writes a dense float32 matrix in the binary feature format.

    Header: magic[8], int64 n, int32 dim, int32 reserved, then n*dim float32.
    The text format is unusable at scale: 64 dimensions over 100M vertices is
    tens of gigabytes of ASCII, and reparsing it dominates every run.
    """
    features = np.ascontiguousarray(features, dtype=np.float32)
    n, dim = features.shape
    with open(path, "wb") as f:
        f.write(FEAT_MAGIC.ljust(8, b"\0"))
        f.write(np.int64(n).tobytes())
        f.write(np.int32(dim).tobytes())
        f.write(np.int32(0).tobytes())
        features.tofile(f)


def load_features(path, n=None):
    """Memory maps a dense feature matrix from the binary format, as float32.

    Only the binary .feat format is accepted, mirroring load_csr: a large ASCII
    feature matrix is never parsed on the training hot path. Real features
    usually arrive as text; convert them once with scripts/convert_features.py.
    """
    with open(path, "rb") as f:
        head = f.read(FEAT_HEADER_LEN)

    if not head.startswith(FEAT_MAGIC):
        raise ValueError(
            f"{path} is not a binary feature file. "
            f"Run scripts/convert_features.py on the text features first."
        )

    rows = int(np.frombuffer(head, dtype=np.int64, count=1, offset=8)[0])
    dim = int(np.frombuffer(head, dtype=np.int32, count=1, offset=16)[0])
    if n is not None and rows != n:
        raise ValueError(f"{path}: has {rows} rows, expected n={n}")
    return np.memmap(
        path,
        dtype=np.float32,
        mode="r",
        offset=FEAT_HEADER_LEN,
        shape=(rows, dim),
    )


def load_labels(path, n):
    """Reads one integer cluster id per line."""
    with open(path, "rb") as f:
        arr = np.array(f.read().split(), dtype=np.int32)
    if arr.size != n:
        raise ValueError(f"{path}: expected {n} labels, found {arr.size}")
    return arr


def write_clustering(path, membership):
    """Writes one integer cluster id per line, the format EVAL expects."""
    np.savetxt(path, np.asarray(membership, dtype=np.int64), fmt="%d")
