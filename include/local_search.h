#pragma once

#include <graph.h>

typedef struct
{
    long long l_sum, s, n;
    int max_queue;

    long long *K;
    int *Community;

    unsigned int seed;

    double time, time_ref;

    int *Temp;
    long long *Temp_set;

    int queue_count;
    int *Queue, *Queue_old, *In_queue, *In_queue_old;

    int log_count, log_alloc;
    int *Log_vertex, *Log_community;
} local_search;

local_search *local_search_init(graph *g, unsigned int seed);

void local_search_free(local_search *ls);

void local_search_reset(local_search *ls, graph *g);

double local_search_get_modularity_score(local_search *ls, graph *g);

void local_search_move_vertex(local_search *ls, graph *g, int u, int c, int log, int queue);

void local_search_explore(local_search *ls, graph *g, double tl, int verbose);