#pragma once

#include "graph.h"

#include <omp.h>

#define INNER_WIDTH 64
#define INNER_MAX 64
#define OUTER_WIDTH 256
#define GRID_WIDTH 16384

#define INNER_SIZE (GRID_WIDTH / INNER_WIDTH)
#define OUTER_SIZE (GRID_WIDTH / OUTER_WIDTH)

typedef struct
{
    float mass;
    float cx, cy;
    float fx, fy;

    int n;
    float _Alignas(32) Vx[INNER_MAX];
    float _Alignas(32) Vy[INNER_MAX];
    float _Alignas(32) Vw[INNER_MAX];
} cell_inner;

typedef struct
{
    float mass;
    float cx, cy;
    float fx, fy;
} cell_outer;

typedef struct
{
    int n;
    float *X, *Y;
    float *fX, *fY, *vX, *vY;

    cell_inner *Grid_inner;
    cell_outer *Grid_outer;

    omp_lock_t *Cell_lock_inner;
    omp_lock_t *Cell_lock_outer;
} force_layout;

force_layout *force_layout_init(graph *g);

void force_layout_free(force_layout *fl);

void force_layout_step(force_layout *fl, graph *g);