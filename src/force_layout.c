#include "force_layout.h"
#include "util.h"

#include <stdlib.h>
#include <math.h>
#include <string.h>

const float EPS = 0.0001f;
const float MAX_FORCE = 10.0f;

// --- Parameters (tune) ---
const float REST_L = 50.0f;
const float K_SPRING = 0.15f;
const float K_REPEL = 0.1f;
const float K_GRAVITY = 0.1f;
const float SOFTEN_EPS = 0.01f;
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

    fl->Grid = calloc(INNER_WIDTH * INNER_WIDTH, sizeof(cell));

    for (int i = 0; i < g->n; i++)
    {
        fl->X[i] = (rand() % OUTER_WIDTH);
        fl->Y[i] = (rand() % OUTER_WIDTH);

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

    free(fl->Grid);

    free(fl);
}

void force_layout_forces_repel_cell(force_layout *fl, int u, graph *g, int cx, int cy)
{
    if (cx < 0 || cx >= INNER_WIDTH || cy < 0 || cy >= INNER_WIDTH)
        return;

    cell *c = fl->Grid + cx * INNER_WIDTH + cy;

    for (int i = 0; i < c->n; i++)
    {
        int v = c->V[i];
        if (v == u)
            continue;

        float dx = fl->X[u] - fl->X[v];
        float dy = fl->Y[u] - fl->Y[v];

        float d = sqrtf(dx * dx + dy * dy + EPS);
        if (d > 10.0f + EPS)
            d -= 10.0f;

        fl->fX[u] += K_REPEL * (dx / (d * d)) * (float)g->VW[v];
        fl->fY[u] += K_REPEL * (dy / (d * d)) * (float)g->VW[v];
    }
}

void force_layout_forces_repel(force_layout *fl, graph *g)
{
    memset(fl->Grid, 0, sizeof(cell) * INNER_WIDTH * INNER_WIDTH);

    for (int u = 0; u < g->n; u++)
    {
        int gx = fl->X[u] / CELL_WIDTH,
            gy = fl->Y[u] / CELL_WIDTH;

        cell *c = fl->Grid + gx * INNER_WIDTH + gy;

        if (c->n < CELL_MAX)
        {
            c->V[c->n++] = u;
            c->mass += g->VW[u];
        }
    }

    for (int i = 0; i < INNER_WIDTH * INNER_WIDTH; i++)
    {
        cell *c = fl->Grid + i;

        for (int j = 0; j < c->n; j++)
        {
            int u = c->V[j];

            c->cx += fl->X[u] * (float)g->VW[u];
            c->cy += fl->Y[u] * (float)g->VW[u];
        }

        if (c->n > 0)
        {
            c->cx /= c->mass;
            c->cy /= c->mass;
        }
    }

    for (int i = 0; i < INNER_WIDTH * INNER_WIDTH; i++)
    {
        cell *c = fl->Grid + i;

        for (int j = 0; j < INNER_WIDTH * INNER_WIDTH; j++)
        {
            if (i == j)
                continue;

            cell *x = fl->Grid + j;

            float dx = c->cx - x->cx;
            float dy = c->cy - x->cy;

            float _d = dx * dx + dy * dy + EPS;

            c->fx += K_REPEL * (dx / _d) * x->mass;
            c->fy += K_REPEL * (dy / _d) * x->mass;
        }
    }

    for (int u = 0; u < g->n; u++)
    {
        int gx = fl->X[u] / CELL_WIDTH,
            gy = fl->Y[u] / CELL_WIDTH;

        cell *c = fl->Grid + gx * INNER_WIDTH + gy;

        // TODO, adjust so adjacent cells remain unchanged
        fl->fX[u] += c->fx;
        fl->fY[u] += c->fy;

        force_layout_forces_repel_cell(fl, u, g, gx - 1, gy - 1);
        force_layout_forces_repel_cell(fl, u, g, gx - 1, gy);
        force_layout_forces_repel_cell(fl, u, g, gx - 1, gy + 1);
        force_layout_forces_repel_cell(fl, u, g, gx, gy - 1);
        force_layout_forces_repel_cell(fl, u, g, gx, gy);
        force_layout_forces_repel_cell(fl, u, g, gx, gy + 1);
        force_layout_forces_repel_cell(fl, u, g, gx + 1, gy - 1);
        force_layout_forces_repel_cell(fl, u, g, gx + 1, gy);
        force_layout_forces_repel_cell(fl, u, g, gx + 1, gy + 1);
    }
}

void force_layout_forces_spring(force_layout *fl, graph *g)
{
    float gx = OUTER_WIDTH / 2, gy = OUTER_WIDTH / 2;

    for (int u = 0; u < g->n; u++)
    {
        float x = fl->X[u], y = fl->Y[u];

        float dx_g = gx - x,
              dy_g = gy - y;

        float d_g = sqrtf(dx_g * dx_g + dy_g * dy_g);

        if (d_g > 50.0f)
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
    for (int u = 0; u < g->n; u++)
    {
        fl->fX[u] = 0.0f;
        fl->fY[u] = 0.0f;
    }

    force_layout_forces_spring(fl, g);
    force_layout_forces_repel(fl, g);

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

        fl->X[u] = fl->X[u] >= OUTER_WIDTH - 1 ? OUTER_WIDTH - 1 : fl->X[u];
        fl->X[u] = fl->X[u] < 0.0f ? 0.0f : fl->X[u];

        fl->Y[u] = fl->Y[u] >= OUTER_WIDTH - 1 ? OUTER_WIDTH - 1 : fl->Y[u];
        fl->Y[u] = fl->Y[u] < 0.0f ? 0.0f : fl->Y[u];
    }
}