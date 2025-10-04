#include "difference_core.h"

#include <omp.h>
#include <limits.h>
#include <stdlib.h>

#define STEP_TIME 10.0

d_core *d_core_init(graph *g, int p, unsigned int seed)
{
    d_core *c = malloc(sizeof(d_core));

    c->p = p;
    c->step_time = STEP_TIME;

    c->time = 0.0;

    c->C = malloc(sizeof(clustering *) * p);
    c->C_core = malloc(sizeof(clustering *) * p);

    c->LS = malloc(sizeof(local_search *) * p);
    c->LS_core = malloc(sizeof(local_search *) * p);

    c->d_core = graph_copy(g);

    c->FM = malloc(sizeof(int) * g->n);
    c->A = malloc(sizeof(int) * g->m * 2);

    c->V = malloc(sizeof(int) * g->n);
    c->E = malloc(sizeof(int) * g->n);
    c->T = malloc(sizeof(int) * 3);
    c->S = malloc(sizeof(long long) * g->n);

#pragma omp parallel
    {
        int nt = omp_get_num_threads();
        int tid = omp_get_thread_num();

#pragma omp single
        {
            c->Dt = malloc(sizeof(long long *) * nt);
            c->Comm = malloc(sizeof(int) * nt);
        }

        c->Dt[tid] = malloc(sizeof(long long) * g->n);
        for (int u = 0; u < g->n; u++)
            c->Dt[tid][u] = 0;

#pragma omp for
        for (int i = 0; i < p; i++)
        {
            c->C[i] = clustering_init(g);
            c->C_core[i] = clustering_init(g);
        }
#pragma omp for
        for (int i = 0; i < p; i++)
        {
            c->LS[i] = local_search_init(g, seed + i);
            c->LS_core[i] = local_search_init(g, seed + p + i);
        }
#pragma omp for
        for (int i = 0; i < g->n; i++)
        {
            c->FM[i] = -1;
            c->A[i] = 0;
        }
    }

    c->best_modularity = c->C[0]->modularity;
    c->time = 0.0;

    return c;
}

void d_core_free(d_core *c)
{
    if (c == NULL)
        return;

    graph_free(c->d_core);

    for (int i = 0; i < c->p; i++)
    {
        local_search_free(c->LS[i]);
        local_search_free(c->LS_core[i]);
    }

#pragma omp parallel
    {
        int tid = omp_get_thread_num();
        free(c->Dt[tid]);
    }

    free(c->LS);
    free(c->LS_core);

    free(c->FM);
    free(c->A);

    free(c->V);
    free(c->E);
    free(c->Comm);
    free(c->T);
    free(c->S);
    free(c->Dt);

    free(c);
}

static inline int d_core_find_overall_best(d_core *c)
{
    int best = 0;
    for (int i = 1; i < c->p; i++)
        if (c->C[i]->modularity > c->C[best]->modularity ||
            (c->C[i]->modularity == c->C[best]->modularity && c->LS[i]->time < c->LS[best]->time))
            best = i;
    return best;
}

static inline int d_core_find_first_best(d_core *c)
{
    int best = 0;
    for (int i = 1; i < c->p; i++)
        if (c->C[i]->modularity > c->C[best]->modularity)
            best = i;
    return best;
}

static inline int d_core_find_first_worst(d_core *c)
{
    int worst = 0;
    for (int i = 1; i < c->p; i++)
        if (c->C[i]->modularity < c->C[worst]->modularity)
            worst = i;
    return worst;
}

void d_core_print(d_core *c, graph *g, long long it, double elapsed)
{
    int best = d_core_find_overall_best(c), worst = d_core_find_first_worst(c);
    printf("%6lld: %12.8lf (%3d %8.2lf) %12.8lf (%3d %8.2lf) %8.2lf %9lld %9lld\n",
           it, clustering_get_modularity(c->C[best]), best, c->LS[best]->time,
           clustering_get_modularity(c->C[worst]), worst, c->LS[worst]->time,
           elapsed, c->d_core->n, c->d_core->V[c->d_core->n]);
    // fflush(stdout);
}

void d_core_update_best(d_core *c)
{
    int best = d_core_find_overall_best(c);
    c->best_modularity = c->C[best]->modularity;
    c->time = c->LS[best]->time;
}

void d_core_run(d_core *c, graph *g, double tl, int verbose)
{
    double start = omp_get_wtime();
    double end = omp_get_wtime();
    double elapsed = end - start;

    if (verbose)
    {
        printf("Running D-core for %.2lf seconds\n", tl);
        printf("%7s %12s (%3s %8s) %12s (%3s %8s) %8s %9s %9s\n", "It.",
               "Best Q", "id", "time",
               "Worst Q", "id", "time",
               "time", "d-core V", "d-core E");
        d_core_print(c, g, 0, elapsed);
    }

#pragma omp parallel
    {
        int tid = omp_get_thread_num();

        long long ci = 0;
        while (elapsed < tl)
        {
            /* Full graph LS */
#pragma omp for
            for (int i = 0; i < c->p; i++)
            {
                double remaining_time = tl - (omp_get_wtime() - start);
                double duration = c->step_time;
                if (remaining_time < duration)
                    duration = remaining_time;
                if (duration > 0.0)
                    local_search_explore(c->LS[i], c->C[i], g, duration, 0);
            }

            /* Mark the D-core */
#pragma omp for
            for (int u = 0; u < g->n; u++)
            {
                for (long long i = g->V[u]; i < g->V[u + 1]; i++)
                {
                    int v = g->E[i];
                    int t = 0;
                    for (int j = 0; j < c->p; j++)
                        t += c->C[j]->Cluster[u] == c->C[j]->Cluster[v];

                    c->A[i] = t == c->p;
                }
            }

#pragma omp single
            {
                end = omp_get_wtime();
                elapsed = end - start;
                d_core_update_best(c);
                if (verbose)
                    d_core_print(c, g, ci, elapsed);
            }

            /* Construct the D-core */
            graph_contract_par_internal(g, c->d_core, c->A, c->FM, c->V, c->E, c->S, c->Dt, c->Comm, c->T);

#pragma omp single
            {
                end = omp_get_wtime();
                elapsed = end - start;
                d_core_update_best(c);
                if (verbose)
                    d_core_print(c, g, ci, elapsed);
            }

            /* D-core LS */
#pragma omp for
            for (int i = 0; i < c->p; i++)
            {
                if (c->d_core->n == 0)
                    continue;

                double remaining_time = tl - (omp_get_wtime() - start);
                double duration = c->step_time * 0.1;
                if (remaining_time < duration)
                    duration = remaining_time;

                if (duration < 0.0)
                    continue;

                long long ref = c->C[i]->modularity;
                clustering_reset(c->C_core[i], c->d_core);
                local_search_queue_all(c->LS_core[i], c->d_core);

                c->LS_core[i]->time_ref = c->LS[i]->time_ref;

                local_search_explore(c->LS_core[i], c->C_core[i], c->d_core, duration, 0);

                // TODO, use the V and E structure to only change the cluster of some vertices

                if (ref < c->C_core[i]->modularity)
                {
                    clustering_update(c->C[i], g, c->C_core[i], c->FM);
                    local_search_queue_all(c->LS[i], g);
                    // for (int u = 0; u < g->n; u++)
                    //     local_search_move_vertex(c->LS[i], c->C[i], g, u, c->C_core[i]->Cluster[c->FM[u]], 0, 1); // c->C_core[i]->Cluster[c->FM[u]]

                    if (c->C[i]->modularity != c->C_core[i]->modularity)
                    {
                        printf("%lf %lf\n", clustering_get_modularity(c->C[i]), clustering_get_modularity(c->C_core[i]));
                        exit(0);
                    }
                }

                if (ref < c->C_core[i]->modularity)
                    c->LS[i]->time = c->LS_core[i]->time;
            }

#pragma omp single
            {
                end = omp_get_wtime();
                elapsed = end - start;
                d_core_update_best(c);
                if (verbose)
                    d_core_print(c, g, ci, elapsed);
            }
            ci++;
        }
    }

    if (verbose)
        printf("\n");
}

int *d_core_get_best_clustering(d_core *d)
{
    int best = d_core_find_overall_best(d);
    return d->C[best]->Cluster;
}