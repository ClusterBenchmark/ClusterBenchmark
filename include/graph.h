#pragma once

#include <stdio.h>

typedef struct
{
    int n, m;           // Number of vertices and edges
    long long *V;       // Neighborhood offsets
    int *E;             // Edge list
    long long *EW, *VW; // Weights for vertices or edges (NULL if none)
} graph;

graph *graph_parse(FILE *f);

void graph_free(graph *g);

int graph_validate(graph *g);