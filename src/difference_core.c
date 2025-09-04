#include "difference_core.h"

#include <omp.h>
#include <limits.h>
#include <stdlib.h>

#define STEP_TIME 5.0

d_core *d_core_init(graph *g, int p, unsigned int seed)
{
    d_core *c = malloc(sizeof(d_core));

    c->p = p;
    c->step_time = STEP_TIME;

    c->time = 0.0;

    c->LS = malloc(sizeof(local_search *) * p);
    c->LS_core = malloc(sizeof(local_search *) * p);

    c->d_core = graph_copy(g);

    c->FM = malloc(sizeof(int) * g->n);
    c->A = malloc(sizeof(int) * g->m * 2);

    int nt;
#pragma omp parallel
    {
#pragma omp master
        {
            nt = omp_get_num_threads();
        }
    }

#pragma omp parallel
    {
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

    c->best_n = c->LS[0]->n;
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

    free(c->LS);
    free(c->LS_core);

    free(c->FM);
    free(c->A);

    free(c);
}

static inline int d_core_find_overall_best(d_core *c)
{
    int best = 0;
    for (int i = 1; i < c->p; i++)
        if (c->LS[i]->n > c->LS[best]->n ||
            (c->LS[i]->n == c->LS[best]->n && c->LS[i]->time < c->LS[best]->time))
            best = i;
    return best;
}

static inline int d_core_find_first_best(d_core *c)
{
    int best = 0;
    for (int i = 1; i < c->p; i++)
        if (c->LS[i]->n > c->LS[best]->n)
            best = i;
    return best;
}

static inline int d_core_find_first_worst(d_core *c)
{
    int worst = 0;
    for (int i = 1; i < c->p; i++)
        if (c->LS[i]->n < c->LS[worst]->n)
            worst = i;
    return worst;
}

void d_core_print(d_core *c, graph *g, long long it, double elapsed)
{
    int best = d_core_find_overall_best(c), worst = d_core_find_first_worst(c);
    printf("\r%6lld: %12.8lf (%3d %8.2lf) %12.8lf (%3d %8.2lf) %8.2lf %9lld %9lld",
           it, local_search_get_modularity_score(c->LS[best], g), best, c->LS[best]->time,
           local_search_get_modularity_score(c->LS[worst], g), worst, c->LS[worst]->time,
           elapsed, c->d_core->n, c->d_core->V[c->d_core->n]);
    fflush(stdout);
}

void d_core_update_best(d_core *c)
{
    int best = d_core_find_overall_best(c);
    c->best_n = c->LS[best]->n;
    c->time = c->LS[best]->time;
}

void d_core_run(d_core *c, graph *g, double tl, int verbose)
{
    double start = omp_get_wtime();
    double end = omp_get_wtime();
    double elapsed = end - start;

    if (verbose)
    {
        printf("Running chils for %.2lf seconds\n", tl);
        printf("%7s %12s (%3s %8s) %12s (%3s %8s) %8s %9s %9s\n", "It.",
               "Best Q", "id", "time",
               "Worst Q", "id", "time",
               "time", "d-core V", "d-core E");
        d_core_print(c, g, 0, elapsed);
    }

#pragma omp parallel
    {
#pragma omp for
        for (int i = 0; i < c->p; i++)
        {
            local_search_explore(c->LS[i], g, 1.0, 0);
        }

#pragma omp single
        {
            end = omp_get_wtime();
            elapsed = end - start;
            d_core_update_best(c);
            if (verbose)
                d_core_print(c, g, 0, elapsed);
        }

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
                    local_search_explore(c->LS[i], g, duration, 0);
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
                        t += c->LS[j]->Community[u] == c->LS[j]->Community[v];

                    c->A[i] = t == c->p;
                }
            }

            /* Construct the D-core */
#pragma omp single
            {
                d_core_update_best(c);
                graph_contract(g, c->d_core, c->A, c->FM);

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
                double duration = c->step_time * 1.0;
                if (remaining_time < duration)
                    duration = remaining_time;

                if (duration < 0.0)
                    continue;

                long long ref = c->LS[i]->n;

                local_search_reset(c->LS_core[i], c->d_core);
                c->LS_core[i]->time_ref = c->LS[i]->time_ref;

                local_search_explore(c->LS_core[i], c->d_core, duration, 0);

                if (ref < c->LS_core[i]->n)
                {
                    for (int u = 0; u < g->n; u++)
                        local_search_move_vertex(c->LS[i], g, u, c->LS_core[i]->Community[c->FM[u]], 0, 1);
                }

                if (ref < c->LS_core[i]->n)
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
    return d->LS[best]->Community;
}