#pragma once

#include <stdio.h>

typedef struct
{
    int n;
    int *V, *E;
    long long *W;
} graph;

graph *graph_parse(FILE *f);

void graph_free(graph *g);

int graph_validate(graph *g);