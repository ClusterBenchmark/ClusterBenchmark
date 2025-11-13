#pragma once

#include "graph.h"

#define INNER_WIDTH 16
#define GRID_WIDTH 32768

typedef struct
{
    int m, l;
    double *CX, *CY, *Mass, *S, *Ri;
    int **Queue, **Queue_mark;

    int n;
    float *X, *Y;
    int *R;
    float *fX, *fY, *vX, *vY;

    float rest_l;
    float k_spring, k_repel, k_gravity;
    float theta;
} barnes_hut;

barnes_hut *barnes_hut_init(graph *g);

void barnes_hut_free(barnes_hut *bh);

void barnes_hut_step(barnes_hut *bh, graph *g);