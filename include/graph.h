#pragma once

#include <stdio.h>

typedef struct
{
    long long n, m;     // Number of vertices and edges
    long long *V;       // Neighborhood offsets
    int *E;             // Edge list
    long long *EW, *VW; // Weights for vertices or edges (NULL if none)
} graph;

graph *graph_parse(FILE *f);

graph *graph_copy(graph *g);

void graph_free(graph *g);

void graph_sort_edges(graph *g);

// Assums that weight arrays are present
void graph_contract(graph *g, graph *gc, int *A, int *FM);

void graph_default_weights(graph *g);

int graph_validate(graph *g);