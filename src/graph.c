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

    m *= 2;

    util_skip_line(Data, &p);

    long long *V = malloc(sizeof(long long) * (n + 1));
    int *E = malloc(sizeof(int) * m);

    long long *VW = malloc(sizeof(long long) * n);
    long long *EW = malloc(sizeof(long long) * m);

    int vertex_weights = (t == 10 || t == 11);
    int edge_weights = (t == 1 || t == 11);

    long long ei = 0;
    for (int u = 0; u < n; u++)
    {
        while (Data[p] == '%')
            util_skip_line(Data, &p);

        if (vertex_weights)
            util_parse_id(Data, &p, VW + u);

        V[u] = ei;
        while (ei < m)
        {
            while (Data[p] == ' ')
                p++;
            if (Data[p] == '\n')
                break;

            long long e;
            util_parse_id(Data, &p, &e);
            E[ei] = e - 1;

            EW[ei] = 1;
            if (edge_weights)
                util_parse_id(Data, &p, EW + ei);

            ei++;
        }
        p++;
        VW[u] = ei - V[u];
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
    gc->E = malloc(sizeof(int) * g->m);

    gc->VW = malloc(sizeof(long long) * g->n);
    gc->EW = malloc(sizeof(long long) * g->m);

    for (int i = 0; i <= g->n; i++)
        gc->V[i] = g->V[i];

    for (long long i = 0; i < g->m; i++)
        gc->E[i] = g->E[i];

    for (int i = 0; i < g->n; i++)
        gc->VW[i] = g->VW[i];

    for (long long i = 0; i < g->m; i++)
        gc->EW[i] = g->EW[i];

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
    int *order = malloc(sizeof(int) * g->m);
    int *buff1 = malloc(sizeof(int) * g->m);
    long long *buff2 = malloc(sizeof(long long) * g->m);

    g->m = 0;

    long long s = 0, t = 0;
    for (int u = 0; u < g->n; u++)
    {
        t = g->V[u + 1];
        int d = t - s;
        for (int i = 0; i < d; i++)
            order[i] = i;

        for (int i = 0; i < d; i++)
            buff1[i] = g->E[s + i];

        qsort_r(order, d, sizeof(int), util_compare_r, g->E + s);

        for (int i = 0; i < d; i++)
            g->E[s + i] = buff1[order[i]];

        for (int i = 0; i < d; i++)
            buff2[i] = g->EW[s + i];

        for (int i = 0; i < d; i++)
            g->EW[s + i] = buff2[order[i]];

        for (int i = 0; i < d; i++)
        {
            if (i == 0 || g->E[s + i] != g->E[g->m - 1])
            {
                g->E[g->m] = g->E[s + i];
                g->EW[g->m] = g->EW[s + i];
                g->m++;
            }
            else
            {
                g->EW[g->m - 1] += g->EW[s + i];
            }
        }
        s = g->V[u + 1];
        g->V[u + 1] = g->m;
    }

    free(order);
    free(buff1);
    free(buff2);
}

int graph_contract_find(int *P, int x)
{
    int root = x;
    while (P[root] != root)
        root = P[root];

    while (P[x] != root)
    {
        int next = P[x];
        P[x] = root;
        x = next;
    }
    return root;
}

void graph_contract_union(int *P, int *S, int x, int y)
{
    x = graph_contract_find(P, x);
    y = graph_contract_find(P, y);

    if (x == y)
        return;

    if (S[x] < S[y])
    {
        int t = x;
        x = y;
        y = t;
    }

    P[y] = x;
    S[x] += S[y];
}

void graph_contract(graph *g, graph *gc, int *A, int *FM)
{
    int *P = malloc(sizeof(int) * g->n);
    int *S = malloc(sizeof(int) * g->n);
    long long *D = malloc(sizeof(long long) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        P[u] = u;
        S[u] = 1;
        D[u] = 0;
    }

    gc->n = 0;
    gc->m = g->m;

    // Discover the new vertices
    for (int u = 0; u < g->n; u++)
    {
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            if (A[i])
                graph_contract_union(P, S, u, g->E[i]);
        }
    }

    // Create new labels
    for (int u = 0; u < g->n; u++)
    {
        int root = graph_contract_find(P, u);
        if (u == root)
        {
            gc->VW[gc->n] = 0;
            FM[u] = gc->n;
            gc->n++;
        }
    }

    // Count degrees
    for (int u = 0; u < g->n; u++)
    {
        int root = graph_contract_find(P, u);
        FM[u] = FM[root];
        gc->VW[FM[root]] += g->VW[u];

        D[FM[root]] += g->V[u + 1] - g->V[u];
    }

    // Prefix sum
    long long ps = 0;
    gc->V[0] = 0;
    for (int u = 0; u < gc->n; u++)
    {
        ps += D[u];
        gc->V[u + 1] = ps;
        D[u] = 0;
    }

    // Move edges
    for (int u = 0; u < g->n; u++)
    {
        int v = FM[u];
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            gc->E[gc->V[v] + D[v]] = FM[g->E[i]];
            gc->EW[gc->V[v] + D[v]] = g->EW[i];
            D[v]++;
        }
    }

    // Sort neigborhoods
    graph_sort_edges(gc);

    free(P);
    free(S);
    free(D);
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

    if (m != g->V[g->n] || m != g->m)
        return 0;

    return 1;
}