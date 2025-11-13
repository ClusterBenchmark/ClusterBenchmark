#include "clustering.h"

#include <stdlib.h>
#include <assert.h>
#include <math.h>

// clustering *clustering_init(graph *g)
// {
//     clustering *c = malloc(sizeof(clustering));

//     c->Cluster = malloc(sizeof(int) * g->n);
//     c->Cluster_degree = malloc(sizeof(long long) * g->n);

//     c->V_end = malloc(sizeof(long long) * g->n);
//     c->E_cluster = malloc(sizeof(int) * g->m);
//     c->E_count = malloc(sizeof(long long) * g->m);
//     c->Valid = malloc(sizeof(int) * g->n);
//     c->update_threshold = 2;
//     c->update_max = 256;

//     c->Temp_counter = malloc(sizeof(long long) * g->n);

//     for (long long i = 0; i < g->m; i++)
//         c->E_cluster[i] = 0;
//     for (long long i = 0; i < g->m; i++)
//         c->E_count[i] = 0;

//     clustering_reset(c, g);

//     return c;
// }

// void clustering_free(clustering *c)
// {
//     free(c->Cluster);
//     free(c->Cluster_degree);

//     free(c->V_end);
//     free(c->E_cluster);
//     free(c->E_count);
//     free(c->Valid);

//     free(c->Temp_counter);

//     free(c);
// }

// void clustering_reset(clustering *c, graph *g)
// {
//     c->cluster_count = g->n;
//     c->modularity = 0ll;
//     c->edge_weight_sum = 0ll;

//     for (int u = 0; u < g->n; u++)
//     {
//         c->Cluster[u] = u;
//         c->Cluster_degree[u] = g->VW[u];
//         c->Temp_counter[u] = 0;

//         c->V_end[u] = g->V[u];
//         c->Valid[u] = 0;

//         for (long long i = g->V[u]; i < g->V[u + 1]; i++)
//         {
//             c->edge_weight_sum += g->EW[i];
//         }

//         c->modularity -= g->VW[u] * g->VW[u];
//     }

//     c->edge_weight_sum /= 2ll;

//     for (int u = 0; u < g->n; u++)
//     {
//         for (long long i = g->V[u]; i < g->V[u + 1]; i++)
//         {
//             if (g->E[i] == u)
//                 c->modularity += 2ll * c->edge_weight_sum * g->EW[i];
//         }
//     }
// }

// void clustering_update(clustering *c, graph *g, clustering *cd, int *FM)
// {
//     c->cluster_count = cd->cluster_count;
//     c->modularity = cd->modularity;
//     c->edge_weight_sum = cd->edge_weight_sum;

//     for (int u = 0; u < g->n; u++)
//     {
//         int cluster = cd->Cluster[FM[u]];
//         c->Cluster[u] = cluster;
//         c->Cluster_degree[cluster] = cd->Cluster_degree[cluster];
//         c->Valid[u] = 0;
//     }
// }

// double clustering_get_modularity(clustering *c)
// {
//     return (double)c->modularity / (double)(4ll * c->edge_weight_sum * c->edge_weight_sum);
// }

// /*  Decrease the counter for c_dec and increase the counter for c_inc. */
// void clustering_update_vertex(clustering *c, graph *g, int u, int c_dec, int c_inc, long long amount)
// {
//     long long p_dec = g->V[u];
//     while (p_dec < c->V_end[u] && c->E_cluster[p_dec] != c_dec)
//         p_dec++;

//     c->E_count[p_dec] -= amount;

//     // Fill gap left after c_dec
//     if (c->E_count[p_dec] == 0)
//     {
//         c->E_cluster[p_dec] = c->E_cluster[c->V_end[u] - 1];
//         c->E_count[p_dec] = c->E_count[c->V_end[u] - 1];
//         c->V_end[u]--;
//     }

//     long long p_new = g->V[u];
//     while (p_new < c->V_end[u] && c->E_cluster[p_new] != c_inc)
//         p_new++;

//     // Make space for c_inc
//     if (p_new == c->V_end[u])
//     {
//         c->V_end[u]++;
//         c->E_cluster[p_new] = c_inc;
//         c->E_count[p_new] = 0;
//     }

//     c->E_count[p_new] += amount;
// }

// void clustering_move_vertex(clustering *c, graph *g, int u, int c_new)
// {
//     int c_old = c->Cluster[u];
//     if (c_old == c_new)
//         return;

//     long long internal_old = 0, internal_new = 0;

//     for (long long i = g->V[u]; i < g->V[u + 1]; i++)
//     {
//         int v = g->E[i];
//         if (v == u)
//             continue;

//         int d = g->V[v + 1] - g->V[v], dc = c->V_end[v] - g->V[v];

//         if (c->Valid[v] && dc <= d / c->update_threshold && dc <= c->update_max)
//             clustering_update_vertex(c, g, v, c_old, c_new, g->EW[i]);
//         else
//             c->Valid[v] = 0;

//         internal_old += (c->Cluster[v] == c_old) * g->EW[i];
//         internal_new += (c->Cluster[v] == c_new) * g->EW[i];
//     }

//     c->modularity += 4ll * c->edge_weight_sum * (internal_new - internal_old) +
//                      2ll * g->VW[u] * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - g->VW[u]);

//     c->cluster_count -= (c->Cluster_degree[c_old] == g->VW[u]);
//     c->cluster_count += (c->Cluster_degree[c_new] == 0);

//     c->Cluster[u] = c_new;
//     c->Cluster_degree[c_old] -= g->VW[u];
//     c->Cluster_degree[c_new] += g->VW[u];
// }

// int clustering_best_move(clustering *c, graph *g, int u)
// {
//     int c_old = c->Cluster[u];
//     int c_best = -1;

//     long long delta_best = 0;
//     long long internal_best = 0;
//     long long internal_old = 0;

//     if (c->Valid[u])
//     {
//         long long p_old = g->V[u];
//         while (p_old < c->V_end[u] && c->E_cluster[p_old] != c_old)
//             p_old++;

//         if (p_old < c->V_end[u])
//             internal_old = c->E_count[p_old];

//         for (long long i = g->V[u]; i < c->V_end[u]; i++)
//         {
//             int c_new = c->E_cluster[i];
//             if (c_new == c_old)
//                 continue;

//             long long internal_new = c->E_count[i];

//             long long delta = 4ll * c->edge_weight_sum * (internal_new - internal_old) +
//                               2ll * g->VW[u] * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - g->VW[u]);

//             if (delta > delta_best)
//             {
//                 delta_best = delta;
//                 c_best = c_new;
//                 internal_best = internal_new;
//             }
//         }
//     }
//     else
//     {
//         for (long long i = g->V[u]; i < g->V[u + 1]; i++)
//         {
//             int v = g->E[i];
//             if (v == u)
//                 continue;
//             c->Temp_counter[c->Cluster[v]] += g->EW[i];
//         }

//         internal_old = c->Temp_counter[c_old];
//         c->Temp_counter[c_old] = 0;

//         c->V_end[u] = g->V[u];
//         if (internal_old > 0)
//         {
//             c->E_cluster[c->V_end[u]] = c_old;
//             c->E_count[c->V_end[u]] = internal_old;
//             c->V_end[u]++;
//         }

//         for (long long i = g->V[u]; i < g->V[u + 1]; i++)
//         {
//             int v = g->E[i];
//             int c_new = c->Cluster[v];

//             if (c->Temp_counter[c_new] == 0)
//                 continue;

//             long long internal_new = c->Temp_counter[c_new];
//             c->Temp_counter[c_new] = 0;

//             long long delta = 4ll * c->edge_weight_sum * (internal_new - internal_old) +
//                               2ll * g->VW[u] * (c->Cluster_degree[c_old] - c->Cluster_degree[c_new] - g->VW[u]);

//             if (delta > delta_best)
//             {
//                 delta_best = delta;
//                 c_best = c_new;
//                 internal_best = internal_new;
//             }

//             c->E_cluster[c->V_end[u]] = c_new;
//             c->E_count[c->V_end[u]] = internal_new;
//             c->V_end[u]++;
//         }

//         c->Valid[u] = 1;
//     }

//     long long delta_new = 4ll * c->edge_weight_sum * (0ll - internal_old) +
//                           2ll * g->VW[u] * (c->Cluster_degree[c_old] - 0ll - g->VW[u]);

//     if (delta_new > delta_best)
//     {
//         int c_new = 0;
//         while (c->Cluster_degree[c_new] != 0)
//             c_new++;

//         delta_best = delta_new;
//         c_best = c_new;
//         internal_best = 0;
//     }

//     if (delta_best == 0)
//         return 0;

//     c->modularity += delta_best;

//     c->cluster_count -= (c->Cluster_degree[c_old] == g->VW[u]);
//     c->cluster_count += (c->Cluster_degree[c_best] == 0);

//     c->Cluster[u] = c_best;
//     c->Cluster_degree[c_old] -= g->VW[u];
//     c->Cluster_degree[c_best] += g->VW[u];

//     for (long long i = g->V[u]; i < g->V[u + 1]; i++)
//     {
//         int v = g->E[i];
//         if (v == u)
//             continue;

//         int d = g->V[v + 1] - g->V[v], dc = c->V_end[v] - g->V[v];

//         if (c->Valid[v] && dc <= d / c->update_threshold && dc <= c->update_max)
//             clustering_update_vertex(c, g, v, c_old, c_best, g->EW[i]);
//         else
//             c->Valid[v] = 0;
//     }

//     return 1;
// }

/* Clustering Sparse */

clustering_sparse *clustering_sparse_init(graph *g)
{
    clustering_sparse *c = malloc(sizeof(clustering_sparse));

    c->Cluster = malloc(sizeof(int) * g->n);
    c->Cluster_weight = malloc(sizeof(long long) * g->n);
    c->Temp_counter = malloc(sizeof(long long) * g->n);

    clustering_sparse_reset(c, g);

    return c;
}

void clustering_sparse_free(clustering_sparse *c)
{
    free(c->Cluster);
    free(c->Cluster_weight);
    free(c->Temp_counter);

    free(c);
}

void clustering_sparse_reset(clustering_sparse *c, graph *g)
{
    c->cluster_count = g->n;
    c->modularity = 0;
    c->edge_weight_sum = 0;

    for (int u = 0; u < g->n; u++)
    {
        c->Cluster[u] = u;
        c->Temp_counter[u] = 0;
    }

    if (g->EW == NULL)
    {
        for (int u = 0; u < g->n; u++)
        {
            long long degree = g->V[u + 1] - g->V[u];
            c->Cluster_weight[u] = degree;
            c->edge_weight_sum += degree;
            c->modularity -= degree * degree;
        }
    }
    else
    {
        long long l_sum = 0;
        for (int u = 0; u < g->n; u++)
        {
            c->Cluster_weight[u] = g->VW[u];
            l_sum += g->VW[u];

            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                c->Cluster_weight[u] += g->EW[i];
            }
            c->modularity -= (__int128_t)c->Cluster_weight[u] * (__int128_t)c->Cluster_weight[u];
            c->edge_weight_sum += c->Cluster_weight[u];
        }
        c->modularity += (__int128_t)c->edge_weight_sum * (__int128_t)l_sum;
    }
}

void clustering_sparse_set_clustering(clustering_sparse *c, graph *g, int *C)
{
    c->cluster_count = 0;
    c->modularity = 0;
    long long l_sum = 0;

    for (int u = 0; u < g->n; u++)
    {
        c->Cluster_weight[u] = 0;
    }

    if (g->EW == NULL)
    {
        for (int u = 0; u < g->n; u++)
        {
            c->Cluster[u] = C[u];
            c->Cluster_weight[C[u]] += g->V[u + 1] - g->V[u];

            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                int v = g->E[i];
                if (C[u] == C[v])
                    l_sum++;
            }
        }
    }
    else
    {
        for (int u = 0; u < g->n; u++)
        {
            c->Cluster[u] = C[u];
            l_sum += g->VW[u];
            c->Cluster_weight[C[u]] += g->VW[u];

            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                c->Cluster_weight[C[u]] += g->EW[i];
                if (C[u] == C[g->E[i]])
                    l_sum += g->EW[i];
            }
        }
    }

    for (int u = 0; u < g->n; u++)
    {
        if (c->Cluster_weight[u] == 0)
            continue;

        c->modularity -= (__int128_t)c->Cluster_weight[u] * (__int128_t)c->Cluster_weight[u];
        c->cluster_count++;
    }

    c->modularity += (__int128_t)c->edge_weight_sum * (__int128_t)l_sum;
}

void clustering_sparse_set_clustering_from_overlay(clustering_sparse *c, graph *g, clustering_sparse *cd)
{
    c->cluster_count = cd->cluster_count;
    c->modularity = cd->modularity;

    for (int i = 0; i < g->n; i++)
    {
        c->Cluster_weight[i] = 0;
    }

    for (int u = 0; u < g->n; u++)
    {
        int cluster = cd->Cluster[c->Cluster[u]];
        c->Cluster[u] = cluster;
        c->Cluster_weight[cluster] = cd->Cluster_weight[cluster];
    }
}

double clustering_sparse_get_modularity(clustering_sparse *c)
{
    __int128_t den = (__int128_t)c->edge_weight_sum * (__int128_t)c->edge_weight_sum;
    __int128_t num = (__int128_t)10000000 * c->modularity;
    double q = (double)(num / den) / 10000000.0;
    return q;
}

void clustering_sparse_move_vertex(clustering_sparse *c, graph *g, int u, int c_new)
{
    int c_old = c->Cluster[u];
    if (c_old == c_new)
        return;

    long long internal_old = 0, internal_new = 0;
    long long vertex_weight = 0;

    if (g->EW == NULL)
    {
        vertex_weight = g->V[u + 1] - g->V[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            internal_old += (c->Cluster[v] == c_old);
            internal_new += (c->Cluster[v] == c_new);
        }
    }
    else
    {
        vertex_weight = g->VW[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            vertex_weight += g->EW[i];
            internal_old += (c->Cluster[v] == c_old) * g->EW[i];
            internal_new += (c->Cluster[v] == c_new) * g->EW[i];
        }
    }

    c->modularity += 2ll * c->edge_weight_sum * (internal_new - internal_old) +
                     2ll * vertex_weight * (c->Cluster_weight[c_old] - c->Cluster_weight[c_new] - vertex_weight);

    c->cluster_count -= (c->Cluster_weight[c_old] == vertex_weight);
    c->cluster_count += (c->Cluster_weight[c_new] == 0);

    c->Cluster[u] = c_new;
    c->Cluster_weight[c_old] -= vertex_weight;
    c->Cluster_weight[c_new] += vertex_weight;
}

void clustering_sparse_compute_move_delta(clustering_sparse *c, graph *g, int u, int c_new, long long *delta, long long *vertex_weight)
{
    int c_old = c->Cluster[u];
    if (c_old == c_new)
        return;

    long long internal_old = 0, internal_new = 0;
    *vertex_weight = 0;

    if (g->EW == NULL)
    {
        *vertex_weight = g->V[u + 1] - g->V[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            internal_old += (c->Cluster[v] == c_old);
            internal_new += (c->Cluster[v] == c_new);
        }
    }
    else
    {
        *vertex_weight = g->VW[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            *vertex_weight += g->EW[i];
            internal_old += (c->Cluster[v] == c_old) * g->EW[i];
            internal_new += (c->Cluster[v] == c_new) * g->EW[i];
        }
    }

    *delta = 2ll * c->edge_weight_sum * (internal_new - internal_old) +
             2ll * *vertex_weight * (c->Cluster_weight[c_old] - c->Cluster_weight[c_new] - *vertex_weight);
}

void clustering_sparse_move_vertex_delta(clustering_sparse *c, graph *g, int u, int c_new, long long delta, long long vertex_weight)
{
    int c_old = c->Cluster[u];

    c->modularity += delta;

    c->cluster_count -= (c->Cluster_weight[c_old] == vertex_weight);
    c->cluster_count += (c->Cluster_weight[c_new] == 0);

    c->Cluster[u] = c_new;
    c->Cluster_weight[c_old] -= vertex_weight;
    c->Cluster_weight[c_new] += vertex_weight;
}

int clustering_sparse_best_move(clustering_sparse *c, graph *g, int u)
{
    int c_old = c->Cluster[u];
    int c_best = -1;

    long long delta_best = 0;
    long long internal_best = 0;
    long long internal_old = 0;

    long long vertex_weight = 0;

    if (g->EW == NULL)
    {
        vertex_weight = g->V[u + 1] - g->V[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            c->Temp_counter[c->Cluster[g->E[i]]]++;
        }
    }
    else
    {
        vertex_weight = g->VW[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            vertex_weight += g->EW[i];
            c->Temp_counter[c->Cluster[g->E[i]]] += g->EW[i];
        }
    }

    internal_old = c->Temp_counter[c_old];
    c->Temp_counter[c_old] = 0;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        int c_new = c->Cluster[v];

        if (c->Temp_counter[c_new] == 0)
            continue;

        long long internal_new = c->Temp_counter[c_new];
        c->Temp_counter[c_new] = 0;

        long long delta = 2ll * c->edge_weight_sum * (internal_new - internal_old) +
                          2ll * vertex_weight * (c->Cluster_weight[c_old] - c->Cluster_weight[c_new] - vertex_weight);

        if (delta > delta_best)
        {
            delta_best = delta;
            c_best = c_new;
            internal_best = internal_new;
        }
    }

    if (delta_best == 0)
        return 0;

    c->modularity += delta_best;

    c->cluster_count -= (c->Cluster_weight[c_old] == vertex_weight);
    c->cluster_count += (c->Cluster_weight[c_best] == 0);

    c->Cluster[u] = c_best;
    c->Cluster_weight[c_old] -= vertex_weight;
    c->Cluster_weight[c_best] += vertex_weight;

    return 1;
}

void clustering_sparse_renumber_clusters(clustering_sparse *c, graph *g)
{
    int ci = 0;
    for (int i = 0; i < g->n; i++)
    {
        if (c->Cluster_weight[i] == 0)
            continue;

        c->Temp_counter[i] = ci + 1;
        c->Cluster_weight[ci] = c->Cluster_weight[i];
        if (ci != i)
            c->Cluster_weight[i] = 0;
        ci++;
    }

    for (int u = 0; u < g->n; u++)
    {
        int new_c = c->Temp_counter[c->Cluster[u]];
        if (g->V[u + 1] - g->V[u] == 0 && new_c == 0)
        {
            c->Cluster[u] = ci++;
        }
        else
        {
            c->Cluster[u] = new_c - 1;
        }
    }
    
    for (int i = 0; i < g->n; i++)
    {
        c->Temp_counter[i] = 0;
    }
}
