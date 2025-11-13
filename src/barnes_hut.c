#include "barnes_hut.h"

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <omp.h>

const float EPS = 0.0001f;
const float MAX_FORCE = 1000.0f;

// --- Parameters ---
const float SOFTEN_EPS = 0.1f;
const float DECAY = 0.99f;

barnes_hut *barnes_hut_init(graph *g)
{
    barnes_hut *bh = malloc(sizeof(barnes_hut));

    bh->l = 0;

    int size = 1, count = 0, width = GRID_WIDTH;
    while (width >= INNER_WIDTH)
    {
        count += size;
        size *= 4;
        width /= 2;
        bh->l++;
    }

    bh->m = count;
    bh->CX = malloc(sizeof(double) * count);
    bh->CY = malloc(sizeof(double) * count);
    bh->Mass = malloc(sizeof(double) * count);
    bh->S = malloc(sizeof(double) * count);
    bh->Ri = malloc(sizeof(double) * count);

    size = 1, count = 0, width = GRID_WIDTH;
    while (width >= INNER_WIDTH)
    {
        for (int i = count; i < count + size; i++)
            bh->S[i] = width;

        count += size;
        size *= 4;
        width /= 2;
    }

#pragma omp parallel
    {
#pragma omp single
        {
            bh->Queue = malloc(sizeof(int *) * omp_get_num_threads());
            bh->Queue_mark = malloc(sizeof(int *) * omp_get_num_threads());
        }
        bh->Queue[omp_get_thread_num()] = malloc(sizeof(int) * count);
        bh->Queue_mark[omp_get_thread_num()] = malloc(sizeof(int) * count);
    }

    bh->Tabu = malloc(sizeof(int) * g->n);

    bh->n = g->n;
    bh->X = malloc(sizeof(float) * g->n);
    bh->Y = malloc(sizeof(float) * g->n);
    bh->R = malloc(sizeof(int) * g->n);
    bh->fX = malloc(sizeof(float) * g->n);
    bh->fY = malloc(sizeof(float) * g->n);
    bh->vX = malloc(sizeof(float) * g->n);
    bh->vY = malloc(sizeof(float) * g->n);

    for (int i = 0; i < g->n; i++)
    {
        bh->Tabu[i] = 0;

        bh->X[i] = (rand() % GRID_WIDTH);
        bh->Y[i] = (rand() % GRID_WIDTH);

        bh->R[i] = 1;

        bh->fX[i] = 0.0f;
        bh->fY[i] = 0.0f;

        bh->vX[i] = 0.0f;
        bh->vY[i] = 0.0f;
    }

    bh->rest_l = 50.0f;
    bh->k_spring = 1.0f;
    bh->k_repel = 1.0f;
    bh->k_gravity = 1.0f;
    bh->theta = 1.0f;

    return bh;
}

void barnes_hut_free(barnes_hut *bh)
{
    free(bh->CX);
    free(bh->CY);
    free(bh->Mass);
    free(bh->S);
    free(bh->Ri);

#pragma omp parallel
    {
        free(bh->Queue[omp_get_thread_num()]);
        free(bh->Queue_mark[omp_get_thread_num()]);
    }
    free(bh->Queue);
    free(bh->Queue_mark);

    free(bh->Tabu);

    free(bh->X);
    free(bh->Y);
    free(bh->R);
    free(bh->fX);
    free(bh->fY);
    free(bh->vX);
    free(bh->vY);

    free(bh);
}

void barnes_hut_populate(barnes_hut *bh, graph *g)
{
    memset(bh->CX, 0, sizeof(double) * bh->m);
    memset(bh->CY, 0, sizeof(double) * bh->m);
    memset(bh->Mass, 0, sizeof(double) * bh->m);
    memset(bh->Ri, 0, sizeof(double) * bh->m);

    // TODO, make par that splits work based on quadrant

    for (int u = 0; u < g->n; u++)
    {
        int p = 0;
        float x = bh->X[u], y = bh->Y[u];
        double area = M_PI * (double)(bh->R[u] * bh->R[u]);
        for (int i = 0; i < bh->l; i++)
        {
            bh->CX[p] += bh->X[u] * area; // * (double)g->VW[u];
            bh->CY[p] += bh->Y[u] * area; // * (double)g->VW[u];
            bh->Mass[p] += area;          // (double)g->VW[u];
            bh->Ri[p] += (double)bh->R[u] * area;

            float w = bh->S[p] / 2;

            // Bot left
            if (x < w && y < w)
            {
                p = (p * 4) + 1;
            }
            // Top left
            else if (x < w)
            {
                p = (p * 4) + 2;
                y -= w;
            }
            // Bot right
            else if (y < w)
            {
                p = (p * 4) + 3;
                x -= w;
            }
            // Top right
            else
            {
                p = (p * 4) + 4;
                x -= w;
                y -= w;
            }
        }
    }
}

void barnes_hut_forces_repell(barnes_hut *bh, graph *g)
{
    // for (int u = 0; u < g->n; u++)
    // {
    //     float x = bh->X[u], y = bh->Y[u];
    //     for (int v = 0; v < g->n; v++)
    //     {
    //         if (v == u)
    //             continue;

    //         double mass = M_PI * (double)(bh->R[v] * bh->R[v]);
    //         float dx = x - bh->X[v], dy = y - bh->Y[v];
    //         float d = sqrtf(dx * dx + dy * dy) + EPS;

    //         float d_eff = d - ((float)bh->R[u] + (float)bh->R[v]);
    //         d_eff = d_eff > 1.0f ? d_eff : 1.0f;

    //         float force = bh->k_repel * mass / (d_eff);
    //         bh->fX[u] += force * dx / d;
    //         bh->fY[u] += force * dy / d;
    //     }
    // }

    // return;

#pragma omp parallel for
    for (int u = 0; u < g->n; u++)
    {
        int *Queue = bh->Queue[omp_get_thread_num()];
        int *Queue_width = bh->Queue_mark[omp_get_thread_num()];

        int s = 0, t = 0;
        Queue[t] = 0;
        Queue_width[t] = GRID_WIDTH;
        t++;

        float x = bh->X[u], y = bh->Y[u];
        float _x = bh->X[u], _y = bh->Y[u];
        double area = M_PI * (double)(bh->R[u] * bh->R[u]);

        while (s < t)
        {
            int p = Queue[s];
            int w = Queue_width[s];
            s++;

            double sum_x = bh->CX[p], sum_y = bh->CY[p], mass = bh->Mass[p], ri = bh->Ri[p];

            if (w > 0)
            {
                sum_x -= x * area; // * (double)g->VW[u];
                sum_y -= y * area; // * (double)g->VW[u];
                mass -= area;      // (double)g->VW[u];
                ri -= (double)bh->R[u] * area;
            }

            if (mass < 1.0f)
                continue;

            ri /= mass;

            float cx = sum_x / mass, cy = sum_y / mass;
            float dx = x - cx, dy = y - cy;
            float d = sqrtf(dx * dx + dy * dy) + 1e-8f;

            // if (d < 1.0f)
            //     continue;

            float d_eff = d - ((float)bh->R[u] + ri); // If p is smalle, add bh->S[p] / 2
            d_eff = d_eff > 1.0f ? d_eff : 1.0f;      // clamp

            if ((bh->S[p] / d_eff) < bh->theta || ((p * 4) + 1) >= bh->m)
            {
                float force = bh->k_repel * mass / d_eff;
                bh->fX[u] += force * dx / d;
                bh->fY[u] += force * dy / d;
            }
            else
            {
                Queue_width[t] = 0;
                Queue_width[t + 1] = 0;
                Queue_width[t + 2] = 0;
                Queue_width[t + 3] = 0;

                // Bot left
                if (_x < w && _y < w)
                {
                    Queue_width[t] = w / 2;
                }
                // Top left
                else if (_x < w)
                {
                    Queue_width[t + 1] = w / 2;
                    _y -= w;
                }
                // Bot right
                else if (_y < w)
                {
                    Queue_width[t + 2] = w / 2;
                    _x -= w;
                }
                // Top right
                else
                {
                    Queue_width[t + 3] = w / 2;
                    _x -= w;
                    _y -= w;
                }

                Queue[t] = (p * 4) + 1;
                Queue[t + 1] = (p * 4) + 2;
                Queue[t + 2] = (p * 4) + 3;
                Queue[t + 3] = (p * 4) + 4;

                t += 4;
            }
        }
    }
}

void barnes_hut_forces_spring(barnes_hut *bh, graph *g)
{
    float gx = GRID_WIDTH / 2, gy = GRID_WIDTH / 2;

#pragma omp parallel for
    for (int u = 0; u < g->n; u++)
    {
        float x = bh->X[u], y = bh->Y[u];

        float dx_g = gx - x,
              dy_g = gy - y;

        float d_g = sqrtf(dx_g * dx_g + dy_g * dy_g) + EPS;

        bh->fX[u] += (dx_g / d_g) * bh->k_gravity;
        bh->fY[u] += (dy_g / d_g) * bh->k_gravity;

        float degree = g->V[u + 1] - g->V[u];

        for (int i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (v == u)
                continue;

            float dx = bh->X[v] - bh->X[u];
            float dy = bh->Y[v] - bh->Y[u];

            float d = sqrtf(dx * dx + dy * dy) + EPS;
            float rest_l = bh->rest_l + bh->R[u] + bh->R[v];
            float s = bh->k_spring * (d - rest_l);

            bh->fX[u] += s * (dx / d) / degree;
            bh->fY[u] += s * (dy / d) / degree;
        }
    }
}

void barnes_hut_step(barnes_hut *bh, graph *g)
{
    for (int u = 0; u < g->n; u++)
    {
        bh->fX[u] = 0.0f;
        bh->fY[u] = 0.0f;
    }

    barnes_hut_forces_spring(bh, g);
    barnes_hut_populate(bh, g);
    barnes_hut_forces_repell(bh, g);

#pragma omp parallel for
    for (int u = 0; u < g->n; u++)
    {
        if (bh->Tabu[u])
        {
            bh->vX[u] = 0.0f;
            bh->vY[u] = 0.0f;
            continue;
        }

        bh->fX[u] = bh->fX[u] != bh->fX[u] ? 0.0f : bh->fX[u];
        bh->fY[u] = bh->fY[u] != bh->fY[u] ? 0.0f : bh->fY[u];

        bh->fX[u] = bh->fX[u] > MAX_FORCE ? MAX_FORCE : bh->fX[u];
        bh->fX[u] = bh->fX[u] < -MAX_FORCE ? -MAX_FORCE : bh->fX[u];

        bh->fY[u] = bh->fY[u] > MAX_FORCE ? MAX_FORCE : bh->fY[u];
        bh->fY[u] = bh->fY[u] < -MAX_FORCE ? -MAX_FORCE : bh->fY[u];

        bh->vX[u] = bh->vX[u] * (1.0f - SOFTEN_EPS) + bh->fX[u] * SOFTEN_EPS;
        bh->vY[u] = bh->vY[u] * (1.0f - SOFTEN_EPS) + bh->fY[u] * SOFTEN_EPS;

        bh->vX[u] *= DECAY;
        bh->vY[u] *= DECAY;

        bh->X[u] += bh->vX[u];
        bh->Y[u] += bh->vY[u];

        bh->X[u] = bh->X[u] >= GRID_WIDTH - 1 ? GRID_WIDTH - 1 : bh->X[u];
        bh->X[u] = bh->X[u] < 0.0f ? 0.0f : bh->X[u];

        bh->Y[u] = bh->Y[u] >= GRID_WIDTH - 1 ? GRID_WIDTH - 1 : bh->Y[u];
        bh->Y[u] = bh->Y[u] < 0.0f ? 0.0f : bh->Y[u];
    }
}