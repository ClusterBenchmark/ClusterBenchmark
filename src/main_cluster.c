#include "graph.h"
#include "difference_core.h"
#include "local_search.h"
#include "util.h"

#include <stdlib.h>
#include <time.h>
#include <string.h>

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);
    graph_default_weights(g);

    if (!graph_validate(g))
    {
        printf("Error in graph\n");
        return 1;
    }

    printf("%lld %lld\n", g->n, g->m);

    local_search *ls = local_search_init(g, 0);
    local_search_explore(ls, g, 30.0, 1);
    local_search_free(ls);

    d_core *dc = d_core_init(g, 16, 0);
    dc->step_time = 5.0;

    d_core_run(dc, g, 300.0, 1);

    int *FM = malloc(sizeof(int) * g->n);
    for (int i = 0; i < g->n; i++)
        FM[i] = -1;

    int *C = d_core_get_best_clustering(dc);
    int c = 0;
    for (int u = 0; u < g->n; u++)
    {
        if (FM[C[u]] < 0)
            FM[C[u]] = c++;
    }

    char res[256];
    int offset = util_path_name_offset(argv[1]);
    int p = 0;
    while (argv[1][offset + p] != '.')
    {
        res[p] = argv[1][p + offset];
        p++;
    }
    strcpy(res + p, "_clusters.csv");

    f = fopen(res, "w");
    fprintf(f, "id,cluster\n");
    for (int u = 0; u < g->n; u++)
    {
        fprintf(f, "%d,%d\n", u, FM[C[u]]);
    }
    fclose(f);

    free(FM);

    d_core_free(dc);
    graph_free(g);

    return 0;
}