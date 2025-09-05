#include "graph.h"

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);

    printf("%lld %lld\n", g->n, g->m);

    f = fopen(argv[2], "w");
    fprintf(f, "source,target\n");

    for (int u = 0; u < g->n; u++)
    {
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (u < v)
                fprintf(f, "%d,%d\n", u, v);
        }
    }

    fclose(f);

    if (!graph_validate(g))
        printf("Error in graph\n");

    graph_free(g);

    return 0;
}