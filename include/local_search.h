#pragma once

#include <graph.h>

typedef struct
{
    long long l_sum, s, n;

    long long *K;
    int *Community;

    unsigned int seed;

    int *Temp, *Temp_set;

    int queue_count;
    int *Queue, *Queue_old, *In_queue, *In_queue_old;

    int log_count, log_alloc;
    int *Log_vertex, *Log_community;
} local_search;

local_search *local_search_init(graph *g, unsigned int seed);

void local_search_free(local_search *ls);

double local_search_get_modularity_score(local_search *ls, graph *g);

void local_search_explore(local_search *ls, graph *g, double tl, int verbose);