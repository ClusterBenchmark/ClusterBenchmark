#include "graph.h"
#include "util.h"
#include "simulated_annealing.h"

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

    printf("%lld %lld\n", g->n, g->m / 2);

    clustering_sparse *c = clustering_sparse_init(g);

    simulated_annealing_run(g, c);

    f = fopen("test.txt", "w");
    for (int u = 0; u < g->n; u++)
    {
        fprintf(f, "%d\n", c->Cluster[u]);
    }
    fclose(f);

    graph_free(g);
    clustering_sparse_free(c);

    // local_search *ls = local_search_init(g, 0);
    // clustering *c = clustering_init(g);

    // graph *gc = graph_copy(g);
    // int *A = malloc(sizeof(int) * g->m);
    // int *FM = malloc(sizeof(int) * g->n);

    // for (int i = 0; i < 10; i++)
    // {
    //     local_search_explore(ls, c, g, 10.0, 1);

    //     for (int u = 0; u < g->n; u++)
    //     {
    //         for (long long j = g->V[u]; j < g->V[u + 1]; j++)
    //         {
    //             A[j] = c->Cluster[u] == c->Cluster[g->E[j]];
    //         }
    //     }

    //     graph_contract(g, gc, A, FM);

    //     local_search *lsc = local_search_init(gc, 0);
    //     clustering *cc = clustering_init(gc);

    //     local_search_explore(lsc, cc, gc, 5.0, 1);

    //     clustering_update(c, g, cc, FM);

    //     local_search_free(lsc);
    //     clustering_free(cc);
    // }

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

    // d_core *d = d_core_init(g, 4, 0);
    // d->step_time = 60.0;
    // d_core_run(d, g, 600, 1);

    // clustering *res = d_core_get_best_clustering(d);

    // int offset = util_path_name_offset(argv[1]);

    // printf("%s,%lld,%lld,%lld,%.10lf,%.3lf\n", argv[1] + offset, g->n, g->m / 2, d->best_modularity, clustering_get_modularity(res), d->time);

    // f = fopen("clustering.txt", "w");
    // for (int u = 0; u < g->n; u++)
    // {
    //     fprintf(f, "%d\n", res->Cluster[u]);
    // }
    // fclose(f);

    // d_core_free(d);
    // graph_free(g);

    return 0;
}