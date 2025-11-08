#include "graph.h"
#include "util.h"
#include "clustering.h"
#include "local_search.h"

#include <stdlib.h>
#include <omp.h>

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);

    if (!graph_validate(g))
    {
        printf("Error in graph\n");
        return 1;
    }

    for (int i = 0; i < 100; i++)
    {
        local_search *ls = local_search_init(g, 0);

        clustering *c = clustering_init(g);
        c->update_threshold = 2;
        c->update_max = (1 << i);

        double t0 = omp_get_wtime();

        local_search_explore(ls, c, g, 30.0, 1);

        // int imp = 1;
        // while (imp)
        // {
        //     imp = 0;
        //     for (int u = 0; u < g->n; u++)
        //         imp |= clustering_best_move(c, g, u);
        // }

        double t1 = omp_get_wtime();
        printf("%d,%lf\n", (1 << i), t1 - t0);
        clustering_free(c);
        local_search_free(ls);
    }

    // int offset = util_path_name_offset(argv[1]);

    // printf("%s,%lld,%lld,%lld,%.10lf,%.3lf\n", argv[1] + offset, g->n, g->m / 2, d->best_modularity, clustering_get_modularity(res), d->time);

    // f = fopen("clustering.txt", "w");
    // for (int u = 0; u < g->n; u++)
    // {
    //     fprintf(f, "%d\n", res->Cluster[u]);
    // }
    // fclose(f);

    graph_free(g);

    return 0;
}