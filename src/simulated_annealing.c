#include "simulated_annealing.h"

#include "util.h"

#include <stdlib.h>
#include <math.h>

int greedy_cliques(graph *g, int *Order, int *Clique, int *Clique_size, int *Count)
{
    int nc = 0;

    for (int i = 0; i < g->n; i++)
    {
        int u = Order[i];

        for (long long j = g->V[u]; j < g->V[u + 1]; j++)
        {
            int v = g->E[j];
            Count[Clique[v]]++;
        }

        int best = 0, best_count = 0;

        for (long long j = g->V[u]; j < g->V[u + 1]; j++)
        {
            int v = g->E[j];

            int c = Clique[v];
            if (c > 0 && Count[c] == Clique_size[c] && Count[c] > best_count)
            {
                best = c;
                best_count = Count[c];
            }

            Count[c] = 0;
        }

        if (best > 0)
        {
            Clique[u] = best;
            Clique_size[best]++;
        }
        else
        {
            Clique[u] = nc + 1;
            Clique_size[nc + 1] = 1;
            nc++;
        }
    }

    return nc;
}

void cliques_init(graph *g, clustering_sparse *c)
{
    int *Order = malloc(sizeof(int) * g->n);
    for (int u = 0; u < g->n; u++)
        Order[u] = u;

    int *Clique = calloc(sizeof(int), g->n);
    int *Clique_size = calloc(sizeof(int), g->n);
    int *Count = calloc(sizeof(int), g->n);

    int nc = greedy_cliques(g, Order, Clique, Clique_size, Count);
    // printf("%d\n", nc);

    // for (int i = 0; i < 10; i++)
    // {
    //     qsort_r(Order, g->n, sizeof(int), compare_clique, Clique);

    //     for (int u = 0; u < g->n; u++)
    //     {
    //         Clique[u] = 0;
    //         Clique_size[u] = 0;
    //     }

    //     nc = greedy_cliques(g, Order, Clique, Clique_size, Count);
    //     // printf("%d\n", nc);
    // }

    clustering_sparse_set_clustering(c, g, Clique);

    free(Order);
    free(Clique);
    free(Clique_size);
    free(Count);
}

void simulated_annealing_run(graph *g, clustering_sparse *c)
{
    // printf("%12.8lf\n", clustering_sparse_get_modularity(c));

    // cliques_init(g, c);

    printf("%12.8lf\n", clustering_sparse_get_modularity(c));

    for (int i = 0; i < 5; i++)
    {
        for (int u = 0; u < g->n; u++)
        {
            clustering_sparse_best_move(c, g, u);
        }

        printf("%12.8lf\n", clustering_sparse_get_modularity(c));
    }

    for (int k = 0; k < (1 << 20); k++)
    {
        double t = 1.0 - ((double)(k + 1) / (double)(1 << 20));
        t /= 8.0;

        int u = rand() % g->n;
        int d = g->V[u + 1] - g->V[u];
        if (d == 0)
            continue;

        int v = g->E[g->V[u] + (rand() % d)];
        int old_c = c->Cluster[u];
        int new_c = c->Cluster[v];

        if (old_c == new_c)
            continue;

        long long delta = clustering_sparse_compute_move_delta(c, g, u, new_c);

        double score = delta / 100000.0;
        if (delta > 0 || rand() < exp(score / t) * (double)RAND_MAX)
        {
            clustering_sparse_move_vertex_delta(c, g, u, new_c, delta);
        }

        if ((k % 1028) == 0)
        {
            printf("\r%15d,%12.8lf,%12.8lf", k, t, clustering_sparse_get_modularity(c));
            fflush(stdout);
        }
    }
    printf("\n");

    int *FM = malloc(sizeof(int) * g->n);
    graph *gc = graph_contract_clusters(g, c->Cluster, c->Cluster_degree, FM);

    clustering_sparse *cc = clustering_sparse_init(gc);

    printf("%lld %lld\n", c->edge_weight_sum, (long long)c->modularity);
    printf("%lld %lld\n", cc->edge_weight_sum, (long long)cc->modularity);

    printf("%12.8lf\n", clustering_sparse_get_modularity(cc));

    for (int i = 0; i < 3; i++)
    {
        for (int u = 0; u < gc->n; u++)
        {
            clustering_sparse_best_move(cc, gc, u);
        }

        printf("%12.8lf\n", clustering_sparse_get_modularity(cc));
    }

    free(FM);
    graph_free(gc);
    clustering_sparse_free(cc);
}