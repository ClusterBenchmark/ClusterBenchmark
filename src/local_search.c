#include "local_search.h"
#include "util.h"

#include <stdlib.h>
#include <assert.h>

#define MAX_QUEUE (1 << 5)
#define TIME_INTERVAL (1 << 7)

local_search *local_search_init(graph *g, unsigned int seed)
{
    local_search *ls = malloc(sizeof(local_search));

    ls->max_queue = MAX_QUEUE;

    ls->seed = seed;

    ls->queue_count = g->n;
    ls->Queue = malloc(sizeof(int) * g->n);
    ls->Queue_old = malloc(sizeof(int) * g->n);
    ls->In_queue = malloc(sizeof(int) * g->n);
    ls->In_queue_old = malloc(sizeof(int) * g->n);

    ls->log_count = 0;
    ls->log_alloc = (1 << 10);

    ls->Log_vertex = malloc(sizeof(int) * ls->log_alloc);
    ls->Log_community = malloc(sizeof(int) * ls->log_alloc);

    local_search_queue_all(ls, g);

    return ls;
}

void local_search_free(local_search *ls)
{
    free(ls->Queue);
    free(ls->Queue_old);
    free(ls->In_queue);
    free(ls->In_queue_old);

    free(ls->Log_vertex);
    free(ls->Log_community);

    free(ls);
}

void local_search_queue_all(local_search *ls, graph *g)
{
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
}

void local_search_move_vertex(local_search *ls, clustering_graph *cg, clustering *c, graph *g, int u, int c_new, int log, int queue)
{
    int c_old = c->Cluster[u];

    clustering_graph_move_vertex(cg, c, g, u, c_new);

    if (log)
    {
        if (ls->log_alloc == ls->log_count)
        {
            ls->log_alloc *= 2;
            ls->Log_vertex = realloc(ls->Log_vertex, sizeof(int) * ls->log_alloc);
            ls->Log_community = realloc(ls->Log_community, sizeof(int) * ls->log_alloc);
        }
        ls->Log_vertex[ls->log_count] = u;
        ls->Log_community[ls->log_count] = c_old;
        ls->log_count++;
    }

    if (!queue)
        return;

    for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        if (!ls->In_queue[v])
        {
            ls->Queue[ls->queue_count++] = v;
            ls->In_queue[v] = 1;
        }
    }
}

static inline void local_search_best_move(local_search *ls, clustering_graph *cg, clustering *c, graph *g, int u, int log)
{
    int c_old = c->Cluster[u];

    if (clustering_graph_best_move(cg, c, g, u))
    {
        if (log)
        {
            if (ls->log_alloc == ls->log_count)
            {
                ls->log_alloc *= 2;
                ls->Log_vertex = realloc(ls->Log_vertex, sizeof(int) * ls->log_alloc);
                ls->Log_community = realloc(ls->Log_community, sizeof(int) * ls->log_alloc);
            }
            ls->Log_vertex[ls->log_count] = u;
            ls->Log_community[ls->log_count] = c_old;
            ls->log_count++;
        }

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (!ls->In_queue[v])
            {
                ls->Queue[ls->queue_count++] = v;
                ls->In_queue[v] = 1;
            }
        }
    }
}

void local_search_greedy(local_search *ls, clustering_graph *cg, clustering *c, graph *g, int log)
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

            local_search_best_move(ls, cg, c, g, u, log);
        }
    }
}

void local_search_perturbe(local_search *ls, clustering_graph *cg, clustering *c, graph *g, int log)
{
    int u = rand_r(&ls->seed) % g->n;

    int it = 0;
    while (it < 32 && (cg->V_end[u] - g->V[u]) == 1)
        u = rand_r(&ls->seed) % g->n;

    long long best = c->modularity;

    long long degree = g->V[u + 1] - g->V[u];
    long long cluster_degree = cg->V_end[u] - g->V[u];
    int c_new;

    if (degree == 0)
        return;

    if ((rand_r(&ls->seed) & 63) == 0)
        c_new = rand_r(&ls->seed) % g->n;
    else
        c_new = cg->E_cluster[g->V[u] + (rand_r(&ls->seed) % cluster_degree)];

    local_search_move_vertex(ls, cg, c, g, u, c_new, log, 1);

    int size = rand_r(&ls->seed) % ls->max_queue;

    for (int i = 0; i < ls->max_queue &&
                    ls->queue_count > 0 &&
                    ls->queue_count < size &&
                    c->modularity <= best;
         i++)
    {
        int v = ls->Queue[rand_r(&ls->seed) % ls->queue_count];

        local_search_move_vertex(ls, cg, c, g, v, c_new, log, 1);
    }
}

void local_search_unwind(local_search *ls, clustering_graph *cg, clustering *c, graph *g, int t)
{
    while (ls->log_count > t)
    {
        ls->log_count--;
        int u = ls->Log_vertex[ls->log_count];
        int c_old = ls->Log_community[ls->log_count];

        local_search_move_vertex(ls, cg, c, g, u, c_old, 0, 0);
    }
}

void local_search_report(local_search *ls, clustering *c, long long it)
{
    printf("\r%10lld: %12.8lf %8.2lf", it,
           clustering_get_modularity(c), ls->time);
    fflush(stdout);
}

void local_search_print_header(local_search *ls, clustering *c, double tl)
{
    printf("Running baseline local search for %.2lf seconds\n", tl);
    printf("%11s %12s %8s\n", "It.", "Q", "Time");
    local_search_report(ls, c, 0);
}

void local_search_explore(local_search *ls, clustering_graph *cg, clustering *c, graph *g, double time_limit, int verbose)
{
    long long best = c->modularity, it = 0;
    double start = util_get_wtime();

    if (verbose)
        local_search_print_header(ls, c, time_limit);

    local_search_greedy(ls, cg, c, g, 0);

    if (c->modularity > best)
    {
        best = c->modularity;
        ls->time = util_get_wtime() - ls->time_ref;
        if (verbose)
            local_search_report(ls, c, 0);
    }

    while (1)
    {
        if ((it++ & (TIME_INTERVAL - 1)) == 0)
        {
            if (util_get_wtime() - start > time_limit)
                break;

            if (verbose)
                local_search_report(ls, c, it);
        }

        ls->log_count = 0;

        local_search_perturbe(ls, cg, c, g, 1);

        local_search_greedy(ls, cg, c, g, 1);

        if (c->modularity > best)
        {
            best = c->modularity;
            ls->time = util_get_wtime() - ls->time_ref;
            ls->log_count = 0;
            if (verbose)
                local_search_report(ls, c, it);
        }
        if (c->modularity < best)
        {
            local_search_unwind(ls, cg, c, g, 0);
        }
    }
    if (verbose)
        printf("\n");
}