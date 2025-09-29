#include "clustering.h"
#include "util.h"

#include <stdlib.h>
#include <assert.h>

clustering *clustering_init(graph *g)
{
    clustering *c = malloc(sizeof(clustering));

    c->cluster_count = 1;
    c->modularity = 0;
    c->edge_weight_sum = 0;

    c->Cluster = malloc(sizeof(int) * g->n);
    c->Cluster_degree = malloc(sizeof(long long) * g->n);

    c->Temp = malloc(sizeof(long long) * g->n);

    c->Ci = malloc(sizeof(int) * g->V[g->n]);
    c->Cc = malloc(sizeof(int) * g->V[g->n]);

    c->Cs = malloc(sizeof(int) * g->n);
    c->Ct = malloc(sizeof(int) * g->n);

    long long ci = 0;

    for (int u = 0; u < g->n; u++)
    {
        long long degree = g->V[u + 1] - g->V[u];

        c->Cluster[u] = 0;
        c->Cluster_degree[u] = 0;
        c->Cluster_degree[0] += degree;
        c->Temp[u] = 0;

        c->Cs[u] = ci;
        c->Ci[ci] = 0;
        c->Cc[ci] = degree;
        c->Ct[u] = ci + 1;
        ci += degree;

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            // c->Ci[ci] = g->E[i];
            // c->Cc[ci] = 1;
            // ci++;

            c->edge_weight_sum += g->EW[i];
        }

        // c->Ct[u] = ci;

        // c->modularity -= degree * degree;
    }

    c->edge_weight_sum /= 2ll;

    c->modularity = (4ll * c->edge_weight_sum * c->edge_weight_sum) - (c->Cluster_degree[0] * c->Cluster_degree[0]);

    printf("%lld %lld\n", c->Cluster_degree[0], c->modularity);

    return c;
}

void clustering_free(clustering *c)
{
    free(c->Cluster);
    free(c->Cluster_degree);

    free(c->Ci);
    free(c->Cc);
    free(c->Cs);
    free(c->Ct);

    free(c);
}

double clustering_get_modularity(clustering *c)
{
    return (double)c->modularity / (double)(4ll * c->edge_weight_sum * c->edge_weight_sum);
}

void clustering_move_vertex_old(clustering *c, graph *g, int u, int c_new)
{
    int c_old = c->Cluster[u];
    if (c_old == c_new)
        return;

    long long degree = g->V[u + 1] - g->V[u];
    long long internal_old = 0, internal_new = 0;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];

        if (c->Cluster[v] == c_old)
            internal_old++;
        else if (c->Cluster[v] == c_new)
            internal_new++;
    }

    c->modularity += 4ll * c->edge_weight_sum * (internal_new - internal_old) +
                     2ll * degree * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - degree);

    c->Cluster[u] = c_new;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_new] += degree;
}

void clustering_move_vertex(clustering *c, graph *g, int u, int c_new)
{
    int c_old = c->Cluster[u];
    if (c_old == c_new)
        return;

    long long degree = g->V[u + 1] - g->V[u];
    long long internal_old = 0, internal_new = 0;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];

        if (c->Cluster[v] == c_old)
            internal_old++;
        else if (c->Cluster[v] == c_new)
            internal_new++;
    }

    c->modularity += 4ll * c->edge_weight_sum * (internal_new - internal_old) +
                     2ll * degree * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - degree);

    c->Cluster[u] = c_new;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_new] += degree;
}

int clustering_best_move_old(clustering *c, graph *g, int u)
{
    int c_old = c->Cluster[u];
    int c_best = -1;

    long long degree = g->V[u + 1] - g->V[u];
    long long delta_best = 0;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];

        c->Temp[c->Cluster[v]]++;
    }

    long long internal_old = c->Temp[c_old];
    c->Temp[c_old] = 0;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        int c_new = c->Cluster[v];

        if (c->Temp[c_new] == 0)
            continue;

        long long internal_new = c->Temp[c_new];
        c->Temp[c_new] = 0;

        long long delta = 4ll * c->edge_weight_sum * (internal_new - internal_old) +
                          2ll * degree * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - degree);

        if (delta > delta_best)
        {
            delta_best = delta;
            c_best = c_new;
        }
    }

    long long delta_new = 4ll * c->edge_weight_sum * (0ll - internal_old) +
                          2ll * degree * (c->Cluster_degree[c_old] - degree - degree);

    if (delta_new > delta_best)
    {
        int c_new = 0;
        while (c->Cluster_degree[c_new] != 0)
            c_new++;

        delta_best = delta_new;
        c_best = c_new;
    }

    if (delta_best == 0)
        return 0;

    c->modularity += delta_best;

    c->Cluster[u] = c_best;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_best] += degree;

    return 1;
}

int clustering_best_move(clustering *c, graph *g, int u)
{
    int c_old = c->Cluster[u];
    int c_best = -1;

    long long degree = g->V[u + 1] - g->V[u];
    long long delta_best = 0;

    long long p_old = c->Cs[u] + lower_bound(c->Ci + c->Cs[u], c->Ct[u] - c->Cs[u], c_old);
    long long internal_old = 0;
    if (p_old < c->Ct[u] && c->Ci[p_old] == c_old)
        internal_old = c->Cc[p_old];

    long long internal_best = 0;

    for (long long i = c->Cs[u]; i < c->Ct[u]; i++)
    {
        int c_new = c->Ci[i];

        if (c_new == c_old)
            continue;

        long long internal_new = c->Cc[i];

        long long delta = 4ll * c->edge_weight_sum * (internal_new - internal_old) +
                          2ll * degree * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - degree);

        if (delta > delta_best)
        {
            delta_best = delta;
            c_best = c_new;
            internal_best = internal_new;
        }
    }

    long long delta_new = 4ll * c->edge_weight_sum * (0ll - internal_old) +
                          2ll * degree * (c->Cluster_degree[c_old] - degree - degree);

    if (delta_new > delta_best)
    {
        int c_new = 0;
        while (c->Cluster_degree[c_new] != 0)
            c_new++;

        delta_best = delta_new;
        c_best = c_new;
        internal_best = 0;
    }

    if (delta_best == 0)
        return 0;

    c->modularity += delta_best;

    c->Cluster[u] = c_best;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_best] += degree;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];

        int pv_old = c->Cs[v] + lower_bound(c->Ci + c->Cs[v], c->Ct[v] - c->Cs[v], c_old);

        if (!(pv_old < c->Ct[v] && c->Ci[pv_old] == c_old))
        {
            printf("%d %d %d %lld\n", v, c->Cluster[v], c_old, g->V[v + 1] - g->V[v]);
            for (long long j = c->Cs[v]; j < c->Ct[v]; j++)
            {
                printf("(%d %d), ", c->Ci[j], c->Cc[j]);
            }
            printf("\n");
        }

        assert(pv_old < c->Ct[v] && c->Ci[pv_old] == c_old);

        c->Cc[pv_old]--; // Assert
        if (c->Cc[pv_old] == 0)
        {
            for (long long j = pv_old + 1; j < c->Ct[v]; j++)
            {
                c->Ci[j - 1] = c->Ci[j];
                c->Cc[j - 1] = c->Cc[j];
            }
            c->Ct[v]--;
        }

        int pv_new = c->Cs[v] + lower_bound(c->Ci + c->Cs[v], c->Ct[v] - c->Cs[v], c_best);
        if (pv_new >= c->Ct[v] || c->Ci[pv_new] != c_best)
        {
            for (long long j = c->Ct[v]; j > pv_new; j--)
            {
                c->Ci[j] = c->Ci[j - 1];
                c->Cc[j] = c->Cc[j - 1];
            }
            c->Ct[v]++;

            c->Ci[pv_new] = c_best;
            c->Cc[pv_new] = 0;
        }
        c->Cc[pv_new]++;
    }

    return 1;
}