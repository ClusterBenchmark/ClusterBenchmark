#pragma once

#include <graph.h>

typedef struct
{
    long long l_sum, s, n;

    long long *L, *K;
    int *Community;

    int *best_c;
    long long best_n;
} simulated_annealing;

simulated_annealing *simulated_annealing_init(graph *g);

void simulated_annealing_free(simulated_annealing *sa);

double simulated_annealing_get_modularity_score(simulated_annealing *sa, graph *g);

void simulated_annealing_run(simulated_annealing *sa, graph *g);