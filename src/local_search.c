#include "local_search.h"
#include "util.h"

#include <stdlib.h>
#include <assert.h>

#define MAX_QUEUE (1 << 5)
#define TIME_INTERVAL (1 << 7)

local_search *local_search_init(graph *g, unsigned int seed)
{
    local_search *ls = malloc(sizeof(local_search));

    ls->l_sum = 0;
    ls->s = 0;
    ls->n = 0;

    ls->max_queue = MAX_QUEUE;

    ls->K = malloc(sizeof(long long) * g->n);
    ls->Community = malloc(sizeof(int) * g->n);

    ls->seed = seed;

    ls->Temp = malloc(sizeof(int) * g->n);
    ls->Temp_set = malloc(sizeof(long long) * g->n);

    ls->queue_count = g->n;
    ls->Queue = malloc(sizeof(int) * g->n);
    ls->Queue_old = malloc(sizeof(int) * g->n);
    ls->In_queue = malloc(sizeof(int) * g->n);
    ls->In_queue_old = malloc(sizeof(int) * g->n);

    ls->log_count = 0;
    ls->log_alloc = (1 << 10);

    ls->Log_vertex = malloc(sizeof(int) * ls->log_alloc);
    ls->Log_community = malloc(sizeof(int) * ls->log_alloc);

    local_search_reset(ls, g);

    return ls;
}

void local_search_free(local_search *ls)
{
    free(ls->K);
    free(ls->Community);

    free(ls->Temp);
    free(ls->Temp_set);

    free(ls->Queue);
    free(ls->Queue_old);
    free(ls->In_queue);
    free(ls->In_queue_old);

    free(ls->Log_vertex);
    free(ls->Log_community);

    free(ls);
}

void local_search_reset(local_search *ls, graph *g)
{
    ls->l_sum = 0;
    ls->s = 0;
    for (int u = 0; u < g->n; u++)
    {
        ls->K[u] = g->VW[u];
        ls->s += ls->K[u] * ls->K[u];
        ls->Community[u] = u;

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (v == u)
                ls->l_sum += g->EW[i];
        }
    }
    ls->n = 4 * g->m * ls->l_sum - ls->s;

    ls->queue_count = g->n;

    for (int i = 0; i < g->n; i++)
        ls->Queue[i] = i;

    for (int i = 0; i < g->n; i++)
        ls->Queue_old[i] = 0;

    for (int i = 0; i < g->n; i++)
        ls->In_queue[i] = 1;

    for (int i = 0; i < g->n; i++)
        ls->In_queue_old[i] = 0;

    ls->log_count = 0;

    ls->time = 0.0;
    ls->time_ref = util_get_wtime();

    for (int i = 0; i < g->n; i++)
        ls->Temp_set[i] = 0;
}

void local_search_move_vertex(local_search *ls, graph *g, int u, int c, int log, int queue)
{
    int old_c = ls->Community[u];
    if (old_c == c)
        return;

    if (log)
    {
        if (ls->log_alloc == ls->log_count)
        {
            ls->log_alloc *= 2;
            ls->Log_vertex = realloc(ls->Log_vertex, sizeof(int) * ls->log_alloc);
            ls->Log_community = realloc(ls->Log_community, sizeof(int) * ls->log_alloc);
        }
        ls->Log_vertex[ls->log_count] = u;
        ls->Log_community[ls->log_count] = old_c;
        ls->log_count++;
    }

    long long d = g->VW[u];
    ls->s -= ls->K[old_c] * ls->K[old_c] + ls->K[c] * ls->K[c];

    ls->K[old_c] -= d;
    ls->K[c] += d;

    ls->s += ls->K[old_c] * ls->K[old_c] + ls->K[c] * ls->K[c];

    long long old_internal = 0, new_internal = 0;
    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        if (v == u)
            continue;

        if (queue && !ls->In_queue[v])
        {
            ls->Queue[ls->queue_count++] = v;
            ls->In_queue[v] = 1;
        }

        if (ls->Community[v] == old_c)
            old_internal += g->EW[i];
        else if (ls->Community[v] == c)
            new_internal += g->EW[i];
    }

    ls->l_sum += new_internal - old_internal;
    ls->n = 4ll * g->m * ls->l_sum - ls->s;

    ls->Community[u] = c;
}

static inline void local_search_best_move(local_search *ls, graph *g, int u, int log)
{
    long long d = g->VW[u], old_internal = 0;
    int cu = ls->Community[u];

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        if (v == u)
            continue;

        int cv = ls->Community[v];
        if (cv == cu)
            old_internal += g->EW[i];
        else
            ls->Temp_set[cv] += g->EW[i];
    }

    int best_c = -1;
    long long best_diff = 0, best_new_internal = 0;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        int cv = ls->Community[v];

        if (v == u || ls->Community[v] == ls->Community[u] || ls->Temp_set[cv] == 0)
            continue;

        long long new_internal = ls->Temp_set[cv];

        long long sd = (ls->K[cu] - d) * (ls->K[cu] - d) +
                       (ls->K[cv] + d) * (ls->K[cv] + d) -
                       (ls->K[cu] * ls->K[cu] + ls->K[cv] * ls->K[cv]);

        long long diff = 4ll * g->m * (new_internal - old_internal) - sd;

        if (diff > best_diff)
        {
            best_diff = diff;
            best_c = cv;
            best_new_internal = new_internal;
        }

        ls->Temp_set[cv] = 0;
    }

    if (best_c >= 0)
    {
        ls->l_sum += best_new_internal - old_internal;
        ls->s += (ls->K[cu] - d) * (ls->K[cu] - d) +
                 (ls->K[best_c] + d) * (ls->K[best_c] + d) -
                 (ls->K[cu] * ls->K[cu] + ls->K[best_c] * ls->K[best_c]);

        ls->K[best_c] += d;
        ls->K[cu] -= d;

        ls->n = 4ll * g->m * ls->l_sum - ls->s;

        ls->Community[u] = best_c;

        if (log)
        {
            if (ls->log_alloc == ls->log_count)
            {
                ls->log_alloc *= 2;
                ls->Log_vertex = realloc(ls->Log_vertex, sizeof(int) * ls->log_alloc);
                ls->Log_community = realloc(ls->Log_community, sizeof(int) * ls->log_alloc);
            }
            ls->Log_vertex[ls->log_count] = u;
            ls->Log_community[ls->log_count] = cu;
            ls->log_count++;
        }

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (v != u && !ls->In_queue[v])
            {
                ls->Queue[ls->queue_count++] = v;
                ls->In_queue[v] = 1;
            }
        }
    }
}

double local_search_get_modularity_score(local_search *ls, graph *g)
{
    return (double)ls->n / (4.0 * g->m * g->m);
}

void local_search_greedy(local_search *ls, graph *g, int log)
{
    while (ls->queue_count > 0)
    {
        int count = ls->queue_count;
        ls->queue_count = 0;

        util_swap_int(&ls->Queue, &ls->Queue_old);
        util_swap_int(&ls->In_queue, &ls->In_queue_old);

        util_shuffle(ls->Queue_old, count, &ls->seed);

        for (int i = 0; i < count; i++)
        {
            int u = ls->Queue_old[i];
            ls->In_queue_old[u] = 0;

            local_search_best_move(ls, g, u, log);
        }
    }
}

void local_search_bfs_perturbe(local_search *ls, graph *g, int log)
{
    int u = rand_r(&ls->seed) % g->n;
    int c = rand_r(&ls->seed) % g->n;

    local_search_move_vertex(ls, g, u, c, log, 1);

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        local_search_move_vertex(ls, g, v, c, log, 1);
    }
}

void local_search_perturbe(local_search *ls, graph *g, int log)
{
    int u = rand_r(&ls->seed) % g->n;

    long long best = ls->n;

    int c = rand_r(&ls->seed) % g->n;

    local_search_move_vertex(ls, g, u, c, log, 1);

    int size = rand_r(&ls->seed) % ls->max_queue;

    for (int i = 0; i < ls->max_queue &&
                    ls->queue_count > 0 &&
                    ls->queue_count < size &&
                    ls->n <= best;
         i++)
    {
        int v = ls->Queue[rand_r(&ls->seed) % ls->queue_count];

        local_search_move_vertex(ls, g, v, c, log, 1);
    }
}

void local_search_unwind(local_search *ls, graph *g, int t)
{
    while (ls->log_count > t)
    {
        ls->log_count--;
        int u = ls->Log_vertex[ls->log_count];
        int c = ls->Log_community[ls->log_count];

        local_search_move_vertex(ls, g, u, c, 0, 0);
    }
}

void local_search_report(local_search *ls, graph *g, long long it)
{
    printf("\r%10lld: %12.8lf %8.2lf", it,
           local_search_get_modularity_score(ls, g), ls->time);
    fflush(stdout);
}

void local_search_print_header(local_search *ls, graph *g, double tl)
{
    printf("Running baseline local search for %.2lf seconds\n", tl);
    printf("%11s %12s %8s\n", "It.", "Q", "Time");
    local_search_report(ls, g, 0);
}

void local_search_explore(local_search *ls, graph *g, double tl, int verbose)
{
    long long best = ls->n, c = 0;
    double start = util_get_wtime();

    if (verbose)
        local_search_print_header(ls, g, tl);

    local_search_greedy(ls, g, 0);

    if (ls->n > best)
    {
        best = ls->n;
        ls->time = util_get_wtime() - ls->time_ref;
        if (verbose)
            local_search_report(ls, g, 0);
    }

    while (1)
    {
        if ((c++ & (TIME_INTERVAL - 1)) == 0)
        {
            if (util_get_wtime() - start > tl)
                break;

            if (verbose)
                local_search_report(ls, g, c);
        }

        ls->log_count = 0;

        if (0 && (rand_r(&ls->seed) % 32) == 0)
            local_search_bfs_perturbe(ls, g, 1);
        else
            local_search_perturbe(ls, g, 1);

        local_search_greedy(ls, g, 1);

        if (ls->n > best)
        {
            best = ls->n;
            ls->time = util_get_wtime() - ls->time_ref;
            ls->log_count = 0;
            if (verbose)
                local_search_report(ls, g, c);
        }
        if (ls->n < best)
        {
            local_search_unwind(ls, g, 0);
        }
    }
    if (verbose)
        printf("\n");
}