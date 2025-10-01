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

int partition(int *E, long long *EW, int left, int right, int bit)
{
    int i = left, j = right;
    while (i <= j)
    {
        while (i <= j && ((E[i] >> bit) & 1) == 0)
            i++;
        while (i <= j && ((E[j] >> bit) & 1) == 1)
            j--;
        if (i < j)
        {
            util_swap(E + i, E + j);
            util_swap_ll(EW + i, EW + j);
            i++;
            j--;
        }
    }
    return i;
}

void radix_sort_msd(int *E, long long *EW, int left, int right, int bit)
{
    if (left >= right || bit < 0)
        return;

    int mid = partition(E, EW, left, right, bit);

    // Recurse on 0-bucket and 1-bucket
    radix_sort_msd(E, EW, left, mid - 1, bit - 1);
    radix_sort_msd(E, EW, mid, right, bit - 1);
}

void graph_sort_edges(graph *g)
{
    g->m = 0;
    long long s = 0;
    for (int u = 0; u < g->n; u++)
    {
        radix_sort_msd(g->E + s, g->EW + s, 0, g->V[u + 1] - s - 1, 31);

        for (long long i = s; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (i == s || v > g->E[g->m - 1])
            {
                g->E[g->m] = g->E[i];
                g->EW[g->m] = g->EW[i];
                g->m++;
            }
            else
            {
                g->EW[g->m - 1] += g->EW[i];
            }
        }
        s = g->V[u + 1];
        g->V[u + 1] = g->m;
    }
}

void graph_contract_new(graph *g, graph *gc, int *A, int *FM)
{
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