#include "graph.h"
#include "local_search.h"
#include "util.h"
#include "dynamic_clustering.h"

#include <stdlib.h>
#include <time.h>
#include <string.h>
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

    printf("%lld %lld\n", g->n, g->m / 2);

    clustering *c = clustering_init(g);

    printf("%lld %lf\n", c->modularity, clustering_get_modularity(c));

    local_search *ls = local_search_init(g, 0);

    local_search_explore(ls, c, g, 2.0, 1);

    graph *gc = graph_copy(g);
    int *FM = malloc(sizeof(int) * g->n);
    int *A = malloc(sizeof(int) * g->m);
    for (int u = 0; u < g->n; u++)
    {
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            A[i] = c->Cluster[u] == c->Cluster[v];
        }
    }

    graph_contract(g, gc, A, FM);

    clustering *cc = clustering_init(gc);

    local_search *lsc = local_search_init(gc, 0);

    local_search_explore(lsc, cc, gc, 30.0, 1);

    local_search_free(ls);
    clustering_free(c);

    return 0;

    // local_search *ls = local_search_init(g, 0);
    // local_search_explore(ls, g, 30.0, 1);

    // long long max_degree = 0, max_clusters = 0;

    // for (int u = 0; u < g->n; u++)
    // {
    //     long long degree = g->V[u + 1] - g->V[u];
    //     if (degree > max_degree)
    //         max_degree = degree;

    //     long long cluster_c = 0;
    //     for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    //     {
    //         int v = g->E[i];

    //         int c = ls->Community[v];
    //         if (ls->Temp_set[c] == 0)
    //             cluster_c++;

    //         ls->Temp_set[c]++;
    //     }

    //     if (cluster_c > max_clusters)
    //         max_clusters = cluster_c;

    //     for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    //     {
    //         int v = g->E[i];

    //         int c = ls->Community[v];

    //         ls->Temp_set[c] = 0;
    //     }
    // }

    // printf("%lld %lld\n", max_degree, max_clusters);

    // local_search_free(ls);

    // d_core *dc = d_core_init(g, 6, 0);
    // dc->step_time = 10.0;

    // d_core_run(dc, g, 300.0, 1);

    // int *FM = malloc(sizeof(int) * g->n);
    // for (int i = 0; i < g->n; i++)
    //     FM[i] = -1;

    // int *C = d_core_get_best_clustering(dc);
    // int c = 0;
    // for (int u = 0; u < g->n; u++)
    // {
    //     if (FM[C[u]] < 0)
    //         FM[C[u]] = c++;
    // }

    // char res[256];
    // int offset = util_path_name_offset(argv[1]);
    // int p = 0;
    // while (argv[1][offset + p] != '.')
    // {
    //     res[p] = argv[1][p + offset];
    //     p++;
    // }
    // strcpy(res + p, "_clusters.csv");

    // f = fopen(res, "w");
    // fprintf(f, "id,cluster\n");
    // for (int u = 0; u < g->n; u++)
    // {
    //     fprintf(f, "%d,%d\n", u, FM[C[u]]);
    // }
    // fclose(f);

    // free(FM);

    // d_core_free(dc);
    // graph_free(g);

    // return 0;
}