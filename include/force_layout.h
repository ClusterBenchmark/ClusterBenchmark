#pragma once

#include "graph.h"

#define CELL_WIDTH 32
#define CELL_MAX 1024
#define OUTER_WIDTH 1024
#define INNER_WIDTH 32

typedef struct
{
    float mass;
    float cx, cy;
    float fx, fy;

    int n;
    int V[CELL_MAX];
} cell;

typedef struct
{
    int n;
    float *X, *Y;
    float *fX, *fY, *vX, *vY;

    cell *Grid;
} force_layout;

force_layout *force_layout_init(graph *g);

void force_layout_free(force_layout *fl);

void force_layout_step(force_layout *fl, graph *g);