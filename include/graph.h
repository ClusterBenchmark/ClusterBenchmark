#pragma once

#include <stdio.h>

typedef struct
{
    long long n, m;     // Number of vertices and edges
    long long *V;       // Neighborhood offsets
    int *E;             // Edge list
    long long *VW, *EW; // Weights for vertices and edges
} graph;

graph *graph_parse(FILE *f);

graph *graph_copy(graph *g);

void graph_free(graph *g);

void graph_sort_edges(graph *g);

int graph_validate(graph *g);

graph *graph_contract_clusters(graph *g, int nc, int *C);

// void graph_contract(graph *g, graph *gc, int *A, int *FM);

// void graph_contract_par(graph *g, graph *gc, int *A, int *FM);

// /*  V, E, and S must be at least n long.
//     C must be at least nt long.
//     Dt must be nt x n.
//     T must hold at least 3 elements. */
// void graph_contract_par_internal(graph *g, graph *gc, int *A, int *FM,
//                                  int *V, int *E, long long *S, long long **Dt, int *C, int *T);