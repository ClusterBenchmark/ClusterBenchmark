#define _GNU_SOURCE

#include "graph.h"
#include "util.h"

#include <assert.h>
#include <stdlib.h>
#include <sys/mman.h>

graph *graph_parse(FILE *f)
{
    fseek(f, 0, SEEK_END);
    size_t size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *Data = mmap(0, size, PROT_READ, MAP_PRIVATE, fileno_unlocked(f), 0);
    size_t p = 0;

    while (Data[p] == '%')
        util_skip_line(Data, &p);

    long long n, m, t;
    util_parse_id(Data, &p, &n);
    util_parse_id(Data, &p, &m);
    util_parse_id(Data, &p, &t);

    util_skip_line(Data, &p);

    long long *V = malloc(sizeof(long long) * (n + 1));
    int *E = malloc(sizeof(int) * (m * 2));

    long long *EW = NULL, *VW = NULL;

    if (t == 10 || t == 11)
        VW = malloc(sizeof(long long) * n);
    if (t == 1 || t == 11)
        EW = malloc(sizeof(long long) * (m * 2));

    int ei = 0;
    for (int u = 0; u < n; u++)
    {
        while (Data[p] == '%')
            util_skip_line(Data, &p);

        if (VW != NULL)
            util_parse_id(Data, &p, VW + u);

        V[u] = ei;
        while (ei < m * 2)
        {
            while (Data[p] == ' ')
                p++;
            if (Data[p] == '\n')
                break;

            long long e;
            util_parse_id(Data, &p, &e);
            E[ei] = e - 1;

            if (EW != NULL)
                util_parse_id(Data, &p, EW + ei);

            ei++;
        }
        p++;
    }
    V[n] = ei;

    munmap(Data, size);

    graph *g = malloc(sizeof(graph));
    *g = (graph){.n = n, .m = m, .V = V, .E = E, .VW = VW, .EW = EW};

    return g;
}

graph *graph_copy(graph *g)
{
    graph *gc = malloc(sizeof(graph));

    gc->n = g->n;
    gc->m = g->m;

    gc->V = malloc(sizeof(long long) * (g->n + 1));
    gc->E = malloc(sizeof(int) * g->m * 2);

    for (int i = 0; i <= g->n; i++)
        gc->V[i] = g->V[i];

    for (int i = 0; i < g->m * 2; i++)
        gc->E[i] = g->E[i];

    gc->VW = NULL;
    gc->EW = NULL;

    if (g->VW != NULL)
    {
        gc->VW = malloc(sizeof(long long) * g->n);
        for (int i = 0; i < g->n; i++)
            gc->VW[i] = g->VW[i];
    }

    if (g->EW != NULL)
    {
        gc->EW = malloc(sizeof(long long) * g->m * 2);
        for (int i = 0; i < g->m * 2; i++)
            gc->EW[i] = g->EW[i];
    }

    return gc;
}

void graph_free(graph *g)
{
    if (g == NULL)
        return;

    free(g->V);
    free(g->E);
    free(g->VW);
    free(g->EW);

    free(g);
}

void graph_sort_edges(graph *g)
{
    int *order = malloc(sizeof(int) * g->m * 2);
    int *buff1 = malloc(sizeof(int) * g->m * 2);
    long long *buff2 = malloc(sizeof(long long) * g->m * 2);

    for (int u = 0; u < g->n; u++)
    {
        int d = g->V[u + 1] - g->V[u];
        for (int i = 0; i < d; i++)
            order[i] = i;

        for (int i = 0; i < d; i++)
            buff1[i] = g->E[g->V[u] + i];

        qsort_r(order, d, sizeof(int), util_compare_r, g->E + g->V[u]);

        for (int i = 0; i < d; i++)
            g->E[g->V[u] + i] = buff1[order[i]];

        if (g->EW == NULL)
            continue;

        for (int i = 0; i < d; i++)
            buff2[i] = g->EW[g->V[u] + i];

        for (int i = 0; i < d; i++)
            g->EW[g->V[u] + i] = buff2[order[i]];
    }

    free(order);
    free(buff1);
    free(buff2);
}

void graph_contract_bfs(graph *g, graph *gc, int *A, int *FM, int s, int *R, int *W)
{
    int r = 1, w = 0;
    R[0] = s;

    FM[s] = gc->n;
    gc->VW[gc->n] = g->VW[s];
    gc->V[gc->n] = gc->m;

    while (r > 0)
    {
        for (int i = 0; i < r; i++)
        {
            int u = R[i];
            for (int j = g->V[u]; j < g->V[u + 1]; j++)
            {
                int v = g->E[j];
                gc->E[gc->m] = v;
                gc->EW[gc->m] = g->EW[j];
                gc->m++;

                if (FM[v] != gc->n && A[j])
                {
                    assert(FM[v] < 0);

                    FM[v] = gc->n;
                    gc->VW[gc->n] += g->VW[v];

                    W[w++] = v;
                }
            }
        }

        r = w;
        w = 0;

        util_swap_int(&R, &W);
    }

    gc->n++;
    gc->V[gc->n] = gc->m;
}

void graph_contract(graph *g, graph *gc, int *A, int *FM)
{
    int *R = malloc(sizeof(int) * g->n);
    int *W = malloc(sizeof(int) * g->n);

    gc->n = 0;
    gc->m = 0;

    for (int i = 0; i < g->n; i++)
        FM[i] = -1;

    for (int u = 0; u < g->n; u++)
    {
        if (FM[u] >= 0)
            continue;

        graph_contract_bfs(g, gc, A, FM, u, R, W);
    }

    for (long long i = 0; i < gc->m; i++)
    {
        gc->E[i] = FM[gc->E[i]];
    }

    gc->m /= 2;

    graph_sort_edges(gc);

    gc->m = 0;
    for (int u = 0; u < gc->n; u++)
    {
        long long s = gc->V[u];
        gc->V[u] = gc->m;
        for (long long i = s; i < gc->V[u + 1]; i++)
        {
            if (i == s || gc->E[i] > gc->E[gc->m - 1])
            {
                gc->E[gc->m] = gc->E[i];
                gc->EW[gc->m] = gc->EW[i];
                gc->m++;
            }
            else
            {
                gc->EW[gc->m - 1] += gc->EW[i];
            }
        }
        for (long long i = gc->V[u]; i < gc->m; i++)
        {
            if (gc->E[i] == u)
                gc->EW[i] /= 2;
        }
    }
    gc->V[gc->n] = gc->m;
    gc->m = g->m; // Should probably not be like this!!

    free(R);
    free(W);
}

void graph_default_weights(graph *g)
{
    if (g->EW == NULL)
    {
        g->EW = malloc(sizeof(long long) * g->m * 2);
        for (int i = 0; i < g->m * 2; i++)
            g->EW[i] = 1;
    }
    if (g->VW == NULL)
    {
        g->VW = malloc(sizeof(long long) * g->n);
        for (int u = 0; u < g->n; u++)
            g->VW[u] = g->V[u + 1] - g->V[u];
    }
}

int graph_validate(graph *g)
{
    int m = 0;
    for (int u = 0; u < g->n; u++)
    {
        if (g->V[u + 1] - g->V[u] < 0)
            return 0;

        m += g->V[u + 1] - g->V[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            if (i < 0 || i >= g->V[g->n])
                return 0;

            int v = g->E[i];
            if (v < 0 || v >= g->n || v == u || (i > g->V[u] && v <= g->E[i - 1]))
                return 0;
        }
    }

    if (m != g->V[g->n] || m / 2 != g->m)
        return 0;

    return 1;
}