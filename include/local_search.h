#pragma once

#include "graph.h"
#include "clustering.h"

typedef struct
{
    int max_queue;

    unsigned int seed;

    double time, time_ref;

    int queue_count;
    int *Queue, *Queue_old, *In_queue, *In_queue_old;

    int log_count, log_alloc;
    int *Log_vertex, *Log_community;
} local_search;

local_search *local_search_init(graph *g, unsigned int seed);

void local_search_free(local_search *ls);

void local_search_queue_all(local_search *ls, graph *g);

void local_search_move_vertex(local_search *ls, clustering *c, graph *g, int u, int c_new, int log, int queue);

void local_search_perturbe(local_search *ls, clustering *c, graph *g, int log);

void local_search_explore(local_search *ls, clustering *c, graph *g, double time_limit, int verbose);