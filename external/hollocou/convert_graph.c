#include <stdio.h>

#include "graph.h"

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);

    f = fopen(argv[2], "w");
    for (int u = 0; u < g->n; u++)
    {
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (u < v)
                fprintf(f, "%d %d\n", u, v);
        }
    }
    fclose(f);

    graph_free(g);

    return 0;
}