#include "graph.h"
#include "util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
    Converts a METIS graph file into the binary CSR format used by the
    benchmarking harness. The graph is parsed, sorted, deduplicated, and
    validated exactly as EVAL does, so the CSR file is the canonical cleaned
    form of the instance. Every solver then loads the same graph through the
    same code path, which removes parsing from the measured differences
    between implementations.
*/

int main(int argc, char **argv)
{
    if (argc != 3)
    {
        fprintf(stderr, "Usage: %s <metis_graph> <output_csr>\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (f == NULL)
    {
        fprintf(stderr, "Failed to open graph file %s\n", argv[1]);
        return 1;
    }

    graph *g = graph_parse(f);
    fclose(f);

    if (g == NULL)
    {
        fprintf(stderr, "Failed to parse graph file %s\n", argv[1]);
        return 1;
    }

    graph_sort_edges(g);

    if (!graph_validate(g))
    {
        fprintf(stderr, "Error in graph %s\n", argv[1]);
        graph_free(g);
        return 1;
    }

    FILE *out = fopen(argv[2], "wb");
    if (out == NULL)
    {
        fprintf(stderr, "Failed to open output file %s\n", argv[2]);
        graph_free(g);
        return 1;
    }

    char magic[GRAPH_CSR_MAGIC_LEN];
    memset(magic, 0, sizeof(magic));
    memcpy(magic, GRAPH_CSR_MAGIC, strlen(GRAPH_CSR_MAGIC));

    int flags = 0;
    if (g->EW != NULL)
        flags |= GRAPH_CSR_FLAG_EDGE_WEIGHTS;
    if (g->VW != NULL)
        flags |= GRAPH_CSR_FLAG_VERTEX_WEIGHTS;
    int reserved = 0;

    fwrite(magic, 1, GRAPH_CSR_MAGIC_LEN, out);
    fwrite(&g->n, sizeof(long long), 1, out);
    fwrite(&g->m, sizeof(long long), 1, out);
    fwrite(&flags, sizeof(int), 1, out);
    fwrite(&reserved, sizeof(int), 1, out);

    fwrite(g->V, sizeof(long long), g->n + 1, out);
    fwrite(g->E, sizeof(int), g->m, out);

    if (g->EW != NULL)
        fwrite(g->EW, sizeof(long long), g->m, out);
    if (g->VW != NULL)
        fwrite(g->VW, sizeof(long long), g->n, out);

    if (ferror(out))
    {
        fprintf(stderr, "Failed while writing %s\n", argv[2]);
        fclose(out);
        graph_free(g);
        return 1;
    }

    fclose(out);

    fprintf(stderr, "%s: n=%lld m=%lld flags=%d\n", argv[2], g->n, g->m / 2, flags);

    graph_free(g);

    return 0;
}
