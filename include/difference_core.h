#pragma once

#include "local_search.h"

typedef struct
{
    int p;
    double step_time;

    long long best_modularity;
    double time;

    clustering **C, **C_core;
    local_search **LS, **LS_core;

    graph *d_core;
    int *FM, *A;

    // Memory for the overlay clustering
    int *V, *E, *Comm, *T;
    long long *S, **Dt;
} d_core;

d_core *d_core_init(graph *g, int p, unsigned int seed);

void d_core_free(d_core *d);

void d_core_run(d_core *d, graph *g, double tl, int verbose);

int *d_core_get_best_clustering(d_core *d);