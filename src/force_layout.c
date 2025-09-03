#include "force_layout.h"
#include "util.h"

#include <stdlib.h>
#include <math.h>

// --- Parameters (tune) ---
const float REST_L = 200.0f;   // L
const float K_SPRING = 0.15f;  // k_s
const float K_REPEL = 50.0f;   // k_r
const float SOFTEN_EPS = 0.5f; // ε

force_layout *force_layout_init(graph *g, int h, int w)
{
    force_layout *fl = malloc(sizeof(force_layout));

    *fl = (force_layout){.h = h, .w = w, .n = g->n};

    fl->Grid = calloc(h * w, sizeof(int));
    fl->X = calloc(g->n, sizeof(float));
    fl->Y = calloc(g->n, sizeof(float));

    for (int i = 0; i < g->n; i++)
    {
        fl->X[i] = rand() % w;
        fl->Y[i] = rand() % h;

        fl->Grid[(int)(fl->Y[i]) * fl->w + (int)(fl->X[i])]++;
    }

    return fl;
}

void force_layout_free(force_layout *fl)
{
    free(fl->Grid);
    free(fl->X);
    free(fl->Y);

    free(fl);
}

void force_layout_forces_fruchterman_reingold(force_layout *fl, graph *g, int u, float *fx, float *fy)
{
    float ux = fl->X[u], uy = fl->Y[u];

    // Gravity

    float cx = fl->w / 2;
    float cy = fl->h / 2;

    float cd = sqrtf(cx * cx + cy * cy);

    *fx = (cx - ux), *fy = (cy - uy);

    // Springs between neighbors

    for (int i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];

        float dx = fl->X[v] - fl->X[u];
        float dy = fl->Y[v] - fl->Y[u];

        float d = sqrtf(dx * dx + dy * dy + SOFTEN_EPS * SOFTEN_EPS);
        float s = K_SPRING * (d - REST_L);

        *fx += s * (dx / d);
        *fy += s * (dy / d);
    }

    for (int _dy = -250; _dy <= 250; _dy++)
    {
        int _y = uy + _dy;
        if (_y < 0 || _y >= fl->h)
            continue;
        for (int _dx = -250; _dx <= 250; _dx++)
        {
            int _x = ux + _dx;
            if (_x < 0 || _x >= fl->w || fl->Grid[_y * fl->w + _x] == 0)
                continue;

            float dx = _dx, dy = _dy;
            float d2 = dx * dx + dy * dy;

            float inv_d = 1.0 / sqrt(d2 + 0.0001);
            float inv_d2 = 1.0 / (d2 + 0.0001);

            float s = K_REPEL * inv_d2;
            float ux = dx * inv_d;
            float uy = dy * inv_d;

            *fx += s * ux * fl->Grid[_y * fl->w + _x];
            *fy += s * uy * fl->Grid[_y * fl->w + _x];
        }
    }
}

void force_layout_step(force_layout *fl, graph *g, double tl, long long il)
{
    double t0 = util_get_wtime();
    for (long long i = 0; i < il; i++)
    {
        if (util_get_wtime() - t0 > tl)
            break;

        int u = rand() % g->n;

        float fx, fy;
        force_layout_forces_fruchterman_reingold(fl, g, u, &fx, &fy);

        fl->Grid[(int)(fl->Y[u]) * fl->w + (int)(fl->X[u])]--;

        fl->X[u] += fx * 0.01;
        fl->Y[u] += fy * 0.01;

        // printf("%f %f\n", fx, fy);

        if (fl->X[u] < 0.0f)
            fl->X[u] = 0.0f;
        if (fl->X[u] > fl->w - 1)
            fl->X[u] = fl->w - 1;

        if (fl->Y[u] < 0.0f)
            fl->Y[u] = 0.0f;
        if (fl->Y[u] > fl->h - 1)
            fl->Y[u] = fl->h - 1;

        fl->Grid[(int)(fl->Y[u]) * fl->w + (int)(fl->X[u])]++;
    }
}