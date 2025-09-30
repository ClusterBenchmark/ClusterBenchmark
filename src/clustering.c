#include "clustering.h"
#include "util.h"

#include <stdlib.h>
#include <assert.h>

clustering *clustering_init(graph *g)
{
    clustering *c = malloc(sizeof(clustering));

    c->Cluster = malloc(sizeof(int) * g->n);
    c->Cluster_degree = malloc(sizeof(long long) * g->n);

    c->Temp = malloc(sizeof(int) * g->n);

    clustering_reset(c, g);

    return c;
}

void clustering_free(clustering *c)
{
    free(c->Cluster);
    free(c->Cluster_degree);

    free(c);
}

void clustering_reset(clustering *c, graph *g)
{
    c->cluster_count = g->n;
    c->modularity = 0;
    c->edge_weight_sum = 0;

    for (int u = 0; u < g->n; u++)
    {
        long long degree = g->V[u + 1] - g->V[u];

        c->Cluster[u] = u;
        c->Cluster_degree[u] = degree;
        c->Temp[u] = 0;

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            c->edge_weight_sum += g->EW[i];
            if (g->E[i] == u)
                c->edge_weight_sum += g->EW[i];
        }

        c->modularity -= degree * degree;
    }

    c->edge_weight_sum /= 2ll;
}

double clustering_get_modularity(clustering *c)
{
    return (double)c->modularity / (double)(4ll * c->edge_weight_sum * c->edge_weight_sum);
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

        internal_old += (c->Cluster[v] == c_old);
        internal_new += (c->Cluster[v] == c_new);
    }

    c->modularity += 4ll * c->edge_weight_sum * (internal_new - internal_old) +
                     2ll * degree * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - degree);

    c->cluster_count -= (c->Cluster_degree[c_old] == degree);
    c->cluster_count += (c->Cluster_degree[c_new] == 0);

    c->Cluster[u] = c_new;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_new] += degree;
}

int clustering_best_move(clustering *c, graph *g, int u)
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

        if (delta > delta_best || (delta == delta_best && c_new < c_best))
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

    c->cluster_count -= (c->Cluster_degree[c_old] == degree);
    c->cluster_count += (c->Cluster_degree[c_best] == 0);

    c->Cluster[u] = c_best;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_best] += degree;

    return 1;
}

/* Clustering Graph Structure */

clustering_graph *clustering_graph_init(clustering *c, graph *g)
{
    clustering_graph *cg = malloc(sizeof(clustering_graph));

    cg->V_end = malloc(sizeof(long long) * g->n);

    cg->E_cluster = malloc(sizeof(int) * g->V[g->n]);
    cg->E_count = malloc(sizeof(int) * g->V[g->n]);

    for (int i = 0; i < g->n; i++)
        cg->V_end[i] = 0;

    for (long long i = 0; i < g->V[g->n]; i++)
        cg->E_cluster[i] = 0;

    for (long long i = 0; i < g->V[g->n]; i++)
        cg->E_count[i] = 0;

    return cg;
}

void clustering_graph_free(clustering_graph *cg)
{
    free(cg->V_end);
    free(cg->E_cluster);
    free(cg->E_count);

    free(cg);
}

void clustering_graph_populate(clustering_graph *cg, clustering *c, graph *g)
{
    for (int u = 0; u < g->n; u++)
    {
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            cg->E_cluster[i] = c->Cluster[v];
        }

        qsort(cg->E_cluster + g->V[u], g->V[u + 1] - g->V[u], sizeof(int), util_compare);

        long long i = g->V[u], j = g->V[u];
        while (j < g->V[u + 1])
        {
            cg->E_cluster[i] = cg->E_cluster[j++];
            cg->E_count[i] = 1;
            while (j < g->V[u + 1] && cg->E_cluster[j] == cg->E_cluster[i])
            {
                cg->E_count[i]++;
                j++;
            }
            i++;
        }
        cg->V_end[u] = i;
    }
}

/*  Decrease the counter for c_dec and increase the counter for c_inc. */
void clustering_graph_update_vertex(clustering_graph *cg, graph *g, int u, int c_dec, int c_inc)
{
    int p_dec = g->V[u] + lower_bound(cg->E_cluster + g->V[u], cg->V_end[u] - g->V[u], c_dec);

    assert(p_dec < cg->V_end[u] && cg->E_cluster[p_dec] == c_dec);

    cg->E_count[p_dec]--;

    // Fill gap left after c_dec
    if (cg->E_count[p_dec] == 0)
    {
        for (long long j = p_dec + 1; j < cg->V_end[u]; j++)
        {
            cg->E_cluster[j - 1] = cg->E_cluster[j];
            cg->E_count[j - 1] = cg->E_count[j];
        }
        cg->V_end[u]--;
    }

    int p_new = g->V[u] + lower_bound(cg->E_cluster + g->V[u], cg->V_end[u] - g->V[u], c_inc);

    // Make space for c_inc
    if (p_new >= cg->V_end[u] || cg->E_cluster[p_new] != c_inc)
    {
        for (long long j = cg->V_end[u]; j > p_new; j--)
        {
            cg->E_cluster[j] = cg->E_cluster[j - 1];
            cg->E_count[j] = cg->E_count[j - 1];
        }
        cg->V_end[u]++;

        cg->E_cluster[p_new] = c_inc;
        cg->E_count[p_new] = 0;
    }
    cg->E_count[p_new]++;
}

void clustering_graph_move_vertex(clustering_graph *cg, clustering *c, graph *g, int u, int c_new)
{
    int c_old = c->Cluster[u];
    if (c_old == c_new)
        return;

    long long degree = g->V[u + 1] - g->V[u];
    long long internal_old = 0, internal_new = 0;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];

        clustering_graph_update_vertex(cg, g, v, c_old, c_new);

        internal_old += (c->Cluster[v] == c_old);
        internal_new += (c->Cluster[v] == c_new);
    }

    c->modularity += 4ll * c->edge_weight_sum * (internal_new - internal_old) +
                     2ll * degree * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - degree);

    c->cluster_count -= (c->Cluster_degree[c_old] == degree);
    c->cluster_count += (c->Cluster_degree[c_new] == 0);

    c->Cluster[u] = c_new;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_new] += degree;
}

int clustering_graph_best_move(clustering_graph *cg, clustering *c, graph *g, int u)
{
    int c_old = c->Cluster[u];
    int c_best = -1;

    long long degree = g->V[u + 1] - g->V[u];
    long long delta_best = 0;

    long long p_old = g->V[u] + lower_bound(cg->E_cluster + g->V[u], cg->V_end[u] - g->V[u], c_old);
    long long internal_old = 0;
    if (p_old < cg->V_end[u] && cg->E_cluster[p_old] == c_old)
        internal_old = cg->E_count[p_old];

    long long internal_best = 0;
    for (long long i = g->V[u]; i < cg->V_end[u]; i++)
    {
        int c_new = cg->E_cluster[i];
        if (c_new == c_old)
            continue;

        long long internal_new = cg->E_count[i];

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

    c->cluster_count -= (c->Cluster_degree[c_old] == degree);
    c->cluster_count += (c->Cluster_degree[c_best] == 0);

    c->Cluster[u] = c_best;
    c->Cluster_degree[c_old] -= degree;
    c->Cluster_degree[c_best] += degree;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];

        clustering_graph_update_vertex(cg, g, v, c_old, c_best);
    }

    return 1;
}
