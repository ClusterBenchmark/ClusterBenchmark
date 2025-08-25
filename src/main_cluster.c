#include "graph.h"
#include "difference_core.h"
#include "local_search.h"

#include <stdlib.h>
#include <time.h>

int path_name_offset(char *path)
{
    int offset = 0;
    for (int i = 0; path[i] != '\0'; i++)
    {
        if (path[i] == '/')
            offset = i + 1;
    }
    return offset;
}

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);
    graph_default_weights(g);

    if (!graph_validate(g))
        printf("Error in graph\n");

    d_core *dc = d_core_init(g, 16, 0);
    dc->step_time = 10.0;

    d_core_run(dc, g, 600.0, 1);

    d_core_free(dc);

    // int *FM = malloc(sizeof(int) * g->n);
    // for (int i = 0; i < g->n; i++)
    //     FM[i] = -1;

    // int c = 0;
    // for (int u = 0; u < g->n; u++)
    // {
    //     if (FM[ls->Community[u]] < 0)
    //         FM[ls->Community[u]] = c++;
    // }

    // f = fopen("clusters.csv", "w");
    // fprintf(f, "id,cluster\n");
    // for (int u = 0; u < g->n; u++)
    // {
    //     fprintf(f, "%d,%d\n", u, FM[ls->Community[u]]);
    // }
    // fclose(f);

    // free(FM);

    graph_free(g);

    return 0;
}