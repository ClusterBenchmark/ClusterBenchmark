#include "graph.h"
#include "util.h"
#include "difference_core.h"

#include <stdlib.h>

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

    // printf("%lld %lld\n", g->n, g->m / 2);

    // for (int i = 3; i < 11; i++)
    // {
    //     local_search *ls = local_search_init(g, 0);
    //     clustering *c = clustering_init(g);

    //     c->update_max = (1 << i);
    //     c->update_threshold = 2;

    //     local_search_explore(ls, c, g, 300.0, 1);

    //     clustering_free(c);
    //     local_search_free(ls);
    // }

    d_core *d = d_core_init(g, 4, 0);
    d->step_time = 60.0;
    d_core_run(d, g, 600, 0);

    clustering *res = d_core_get_best_clustering(d);

    int offset = util_path_name_offset(argv[1]);

    // printf("%s,%lld,%lld,%lld,%.10lf,%.3lf\n", argv[1] + offset, g->n, g->m / 2, d->best_modularity, clustering_get_modularity(res), d->time);

    // f = fopen("clustering.txt", "w");
    // for (int u = 0; u < g->n; u++)
    // {
    //     fprintf(f, "%d\n", res->Cluster[u]);
    // }
    // fclose(f);

    d_core_free(d);
    graph_free(g);

    return 0;
}