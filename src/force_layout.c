#include "force_layout.h"
#include "util.h"

#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <immintrin.h>

const float EPS = 0.0001f;
const float MAX_FORCE = 1000.0f;

// --- Parameters ---
const float REST_L = 25.0f;
const float K_SPRING = 0.1f;
const float K_REPEL = 0.1f;
const float K_GRAVITY = 0.1f;
const float SOFTEN_EPS = 0.1f;
const float DECAY = 0.999f;

force_layout *force_layout_init(graph *g)
{
    force_layout *fl = malloc(sizeof(force_layout));

    *fl = (force_layout){.n = g->n};

    fl->X = calloc(g->n, sizeof(float));
    fl->Y = calloc(g->n, sizeof(float));

    fl->fX = calloc(g->n, sizeof(float));
    fl->fY = calloc(g->n, sizeof(float));

    fl->vX = calloc(g->n, sizeof(float));
    fl->vY = calloc(g->n, sizeof(float));

    fl->Grid_inner = calloc(INNER_SIZE * INNER_SIZE, sizeof(cell_inner));
    fl->Grid_outer = calloc(OUTER_SIZE * OUTER_SIZE, sizeof(cell_outer));

    fl->Cell_lock_inner = malloc(sizeof(omp_lock_t) * INNER_SIZE * INNER_SIZE);
    fl->Cell_lock_outer = malloc(sizeof(omp_lock_t) * OUTER_SIZE * OUTER_SIZE);

    for (int i = 0; i < INNER_SIZE * INNER_SIZE; i++)
    {
        omp_init_lock(fl->Cell_lock_inner + i);
    }
    for (int i = 0; i < OUTER_SIZE * OUTER_SIZE; i++)
    {
        omp_init_lock(fl->Cell_lock_outer + i);
    }

    for (int i = 0; i < g->n; i++)
    {
        fl->X[i] = (rand() % GRID_WIDTH);
        fl->Y[i] = (rand() % GRID_WIDTH);

        fl->fX[i] = 0.0f;
        fl->fY[i] = 0.0f;

        fl->vX[i] = 0.0f;
        fl->vY[i] = 0.0f;
    }

    return fl;
}

void force_layout_free(force_layout *fl)
{
    free(fl->X);
    free(fl->Y);

    free(fl->fX);
    free(fl->fY);

    free(fl->vX);
    free(fl->vY);

    free(fl->Grid_inner);
    free(fl->Grid_outer);

    for (int i = 0; i < INNER_SIZE * INNER_SIZE; i++)
    {
        omp_destroy_lock(fl->Cell_lock_inner + i);
    }
    for (int i = 0; i < OUTER_SIZE * OUTER_SIZE; i++)
    {
        omp_destroy_lock(fl->Cell_lock_outer + i);
    }

    free(fl->Cell_lock_inner);
    free(fl->Cell_lock_outer);

    free(fl);
}

void force_layout_forces_repel_individual(force_layout *fl, int u, graph *g, int cx, int cy)
{
    if (cx < 0 || cx >= INNER_SIZE || cy < 0 || cy >= INNER_SIZE)
        return;

    cell_inner *c = fl->Grid_inner + cx * INNER_SIZE + cy;

// #pragma omp simd
    for (int i = 0; i < c->n; i++)
    {
        float dx = fl->X[u] - c->Vx[i];
        float dy = fl->Y[u] - c->Vy[i];

        float _d = dx * dx + dy * dy + EPS;

        fl->fX[u] += K_REPEL * (dx / _d) * c->Vw[i];
        fl->fY[u] += K_REPEL * (dy / _d) * c->Vw[i];
    }
}

void force_layout_forces_repel_cell_inner(force_layout *fl, int cx, int cy)
{
    cell_inner *c = fl->Grid_inner + cx * INNER_SIZE + cy;

    const int between_width = OUTER_WIDTH / INNER_WIDTH;

    int sx = (cx & (~(between_width - 1)));
    sx = sx > 0 ? sx - between_width : sx;

    int tx = (cx & (~(between_width - 1))) + between_width;
    tx = tx < INNER_SIZE ? tx + between_width : tx;

    int sy = (cy & (~(between_width - 1)));
    sy = sy > 0 ? sy - between_width : sy;

    int ty = (cy & (~(between_width - 1))) + between_width;
    ty = ty < INNER_SIZE ? ty + between_width : ty;

    for (int x = sx; x < tx; x++)
    {
        for (int y = sy; y < ty; y++)
        {
            if (abs(cx - x) <= 1 && abs(cy - y) <= 1)
                continue;

            cell_inner *ci = fl->Grid_inner + x * INNER_SIZE + y;

            if (ci->n == 0)
                continue;

            float dx = c->cx - ci->cx;
            float dy = c->cy - ci->cy;

            float _d = dx * dx + dy * dy + EPS;

            c->fx += K_REPEL * (dx / _d) * ci->mass;
            c->fy += K_REPEL * (dy / _d) * ci->mass;
        }
    }
}

void force_layout_forces_repel(force_layout *fl, graph *g)
{

#pragma omp for
    for (int i = 0; i < INNER_SIZE * INNER_SIZE; i++)
    {
        cell_inner *c = fl->Grid_inner + i;

        c->mass = 0.0f;
        c->cx = 0.0f;
        c->cy = 0.0f;
        c->fx = 0.0f;
        c->fy = 0.0f;
        c->n = 0;
    }

#pragma omp for
    for (int i = 0; i < OUTER_SIZE * OUTER_SIZE; i++)
    {
        cell_outer *c = fl->Grid_outer + i;

        c->mass = 0.0f;
        c->cx = 0.0f;
        c->cy = 0.0f;
        c->fx = 0.0f;
        c->fy = 0.0f;
    }

#pragma omp for
    for (int u = 0; u < g->n; u++)
    {
        int cx = fl->X[u] / INNER_WIDTH,
            cy = fl->Y[u] / INNER_WIDTH;

        cell_inner *c = fl->Grid_inner + cx * INNER_SIZE + cy;

        omp_set_lock(fl->Cell_lock_inner + cx * INNER_SIZE + cy);

        if (c->n < INNER_MAX)
        {
            c->Vx[c->n] = fl->X[u];
            c->Vy[c->n] = fl->Y[u];
            c->Vw[c->n] = g->VW[u];
            c->n++;
        }

        c->mass += g->VW[u];
        c->cx += fl->X[u] * (float)g->VW[u];
        c->cy += fl->Y[u] * (float)g->VW[u];

        omp_unset_lock(fl->Cell_lock_inner + cx * INNER_SIZE + cy);
    }

#pragma omp for
    for (int u = 0; u < g->n; u++)
    {
        int cx = fl->X[u] / OUTER_WIDTH,
            cy = fl->Y[u] / OUTER_WIDTH;

        cell_outer *c = fl->Grid_outer + cx * OUTER_SIZE + cy;

        omp_set_lock(fl->Cell_lock_outer + cx * OUTER_SIZE + cy);

        c->mass += g->VW[u];
        c->cx += fl->X[u] * (float)g->VW[u];
        c->cy += fl->Y[u] * (float)g->VW[u];

        omp_unset_lock(fl->Cell_lock_outer + cx * OUTER_SIZE + cy);
    }

#pragma omp for
    for (int i = 0; i < INNER_SIZE * INNER_SIZE; i++)
    {
        cell_inner *c = fl->Grid_inner + i;

        if (c->mass > 0.0f)
        {
            c->cx /= c->mass;
            c->cy /= c->mass;
        }
    }

#pragma omp for
    for (int i = 0; i < OUTER_SIZE * OUTER_SIZE; i++)
    {
        cell_outer *c = fl->Grid_outer + i;

        if (c->mass > 0.0f)
        {
            c->cx /= c->mass;
            c->cy /= c->mass;
        }
    }

#pragma omp for schedule(dynamic, 32)
    for (int i = 0; i < INNER_SIZE * INNER_SIZE; i++)
    {
        cell_inner *c = fl->Grid_inner + i;
        if (c->n == 0)
            continue;

        int cx = i / INNER_SIZE,
            cy = i % INNER_SIZE;

        force_layout_forces_repel_cell_inner(fl, cx, cy);
    }

#pragma omp for
    for (int i = 0; i < OUTER_SIZE * OUTER_SIZE; i++)
    {
        cell_outer *c = fl->Grid_outer + i;
        if (c->mass == 0.0f)
            continue;

        int cx = i / OUTER_SIZE,
            cy = i % OUTER_SIZE;

        for (int j = 0; j < OUTER_SIZE * OUTER_SIZE; j++)
        {
            int _cx = j / OUTER_SIZE,
                _cy = j % OUTER_SIZE;

            if (abs(cx - _cx) <= 1 && abs(cy - _cy) <= 1)
                continue;

            cell_outer *_c = fl->Grid_outer + j;

            float dx = c->cx - _c->cx;
            float dy = c->cy - _c->cy;

            float _d = dx * dx + dy * dy + EPS;

            c->fx += K_REPEL * (dx / _d) * _c->mass;
            c->fy += K_REPEL * (dy / _d) * _c->mass;
        }
    }

#pragma omp for schedule(dynamic, 32)
    for (int u = 0; u < g->n; u++)
    {
        int ci_x = fl->X[u] / INNER_WIDTH,
            ci_y = fl->Y[u] / INNER_WIDTH;

        force_layout_forces_repel_individual(fl, u, g, ci_x - 1, ci_y - 1);
        force_layout_forces_repel_individual(fl, u, g, ci_x - 1, ci_y);
        force_layout_forces_repel_individual(fl, u, g, ci_x - 1, ci_y + 1);
        force_layout_forces_repel_individual(fl, u, g, ci_x, ci_y - 1);
        force_layout_forces_repel_individual(fl, u, g, ci_x, ci_y);
        force_layout_forces_repel_individual(fl, u, g, ci_x, ci_y + 1);
        force_layout_forces_repel_individual(fl, u, g, ci_x + 1, ci_y - 1);
        force_layout_forces_repel_individual(fl, u, g, ci_x + 1, ci_y);
        force_layout_forces_repel_individual(fl, u, g, ci_x + 1, ci_y + 1);

        cell_inner *ci = fl->Grid_inner + ci_x * INNER_SIZE + ci_y;

        fl->fX[u] += ci->fx;
        fl->fY[u] += ci->fy;

        int co_x = fl->X[u] / OUTER_WIDTH,
            co_y = fl->Y[u] / OUTER_WIDTH;

        cell_outer *co = fl->Grid_outer + co_x * OUTER_SIZE + co_y;

        fl->fX[u] += co->fx;
        fl->fY[u] += co->fy;
    }
}

void force_layout_forces_spring(force_layout *fl, graph *g)
{
    float gx = GRID_WIDTH / 2, gy = GRID_WIDTH / 2;

#pragma omp for
    for (int u = 0; u < g->n; u++)
    {
        float x = fl->X[u], y = fl->Y[u];

        float dx_g = gx - x,
              dy_g = gy - y;

        float d_g = sqrtf(sqrtf(dx_g * dx_g + dy_g * dy_g));

        if (d_g > 1.0f)
        {
            fl->fX[u] += (dx_g / d_g) * K_GRAVITY;
            fl->fY[u] += (dy_g / d_g) * K_GRAVITY;
        }

        for (int i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];

            float dx = fl->X[v] - fl->X[u];
            float dy = fl->Y[v] - fl->Y[u];

            float d = sqrtf(dx * dx + dy * dy) + EPS;
            float s = K_SPRING * (d - REST_L);

            fl->fX[u] += s * (dx / d);
            fl->fY[u] += s * (dy / d);
        }
    }
}

void force_layout_step(force_layout *fl, graph *g)
{
#pragma omp parallel
    {
#pragma omp for
        for (int u = 0; u < g->n; u++)
        {
            fl->fX[u] = 0.0f;
            fl->fY[u] = 0.0f;
        }

        force_layout_forces_spring(fl, g);
        force_layout_forces_repel(fl, g);

#pragma omp for
        for (int u = 0; u < g->n; u++)
        {
            fl->fX[u] = fl->fX[u] != fl->fX[u] ? 0.0f : fl->fX[u];
            fl->fY[u] = fl->fY[u] != fl->fY[u] ? 0.0f : fl->fY[u];

            fl->fX[u] = fl->fX[u] > MAX_FORCE ? MAX_FORCE : fl->fX[u];
            fl->fX[u] = fl->fX[u] < -MAX_FORCE ? -MAX_FORCE : fl->fX[u];

            fl->fY[u] = fl->fY[u] > MAX_FORCE ? MAX_FORCE : fl->fY[u];
            fl->fY[u] = fl->fY[u] < -MAX_FORCE ? -MAX_FORCE : fl->fY[u];

            fl->vX[u] = fl->vX[u] * (1.0f - SOFTEN_EPS) + fl->fX[u] * SOFTEN_EPS;
            fl->vY[u] = fl->vY[u] * (1.0f - SOFTEN_EPS) + fl->fY[u] * SOFTEN_EPS;

            fl->vX[u] *= DECAY;
            fl->vY[u] *= DECAY;

            fl->X[u] += fl->vX[u];
            fl->Y[u] += fl->vY[u];

            fl->X[u] = fl->X[u] >= GRID_WIDTH - 1 ? GRID_WIDTH - 1 : fl->X[u];
            fl->X[u] = fl->X[u] < 0.0f ? 0.0f : fl->X[u];

            fl->Y[u] = fl->Y[u] >= GRID_WIDTH - 1 ? GRID_WIDTH - 1 : fl->Y[u];
            fl->Y[u] = fl->Y[u] < 0.0f ? 0.0f : fl->Y[u];
        }
    }
}