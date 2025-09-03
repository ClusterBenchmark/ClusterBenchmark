#pragma once

#include "graph.h"

typedef struct
{
    int h, w;
    int *Grid;

    int n;
    float *X, *Y;
} force_layout;

force_layout *force_layout_init(graph *g, int h, int w);

void force_layout_free(force_layout *fl);

void force_layout_step(force_layout *fl, graph *g, double tl, long long il);