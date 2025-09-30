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

// TODO, fix allocation (need to know max degree)

void graph_sort_edges(graph *g);

void graph_contract(graph *g, graph *gc, int *A, int *FM);

int graph_validate(graph *g);