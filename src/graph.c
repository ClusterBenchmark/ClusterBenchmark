#include "graph.h"

#include <stdlib.h>
#include <sys/mman.h>

static inline void parse_id(char *Data, size_t *p, long long *v)
{
    while (Data[*p] < '0' || Data[*p] > '9')
        (*p)++;

    *v = 0;
    while (Data[*p] >= '0' && Data[*p] <= '9')
        *v = (*v) * 10 + Data[(*p)++] - '0';
}

graph *graph_parse(FILE *f)
{
    fseek(f, 0, SEEK_END);
    size_t size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *Data = mmap(0, size, PROT_READ, MAP_PRIVATE, fileno_unlocked(f), 0);
    size_t p = 0;

    long long n, m, t;
    parse_id(Data, &p, &n);
    parse_id(Data, &p, &m);
    parse_id(Data, &p, &t);

    int *V = malloc(sizeof(int) * (n + 1));
    int *E = malloc(sizeof(int) * (m * 2));

    long long *W = malloc(sizeof(long long) * n);

    int ei = 0;
    for (int u = 0; u < n; u++)
    {
        parse_id(Data, &p, W + u);
        V[u] = ei;
        while (ei < m * 2)
        {
            while (Data[p] == ' ')
                p++;
            if (Data[p] == '\n')
                break;

            long long e;
            parse_id(Data, &p, &e);
            E[ei++] = e - 1;
            ;
        }
        p++;
    }
    V[n] = ei;

    munmap(Data, size);

    graph *g = malloc(sizeof(graph));
    *g = (graph){.n = n, .V = V, .E = E, .W = W};

    return g;
}

void graph_free(graph *g)
{
    if (g == NULL)
        return;

    free(g->V);
    free(g->E);
    free(g->W);

    free(g);
}

static inline int compare(const void *a, const void *b)
{
    return (*(int *)a - *(int *)b);
}

int graph_validate(graph *g)
{
    int M = 0;
    for (int u = 0; u < g->n; u++)
    {
        if (g->V[u + 1] - g->V[u] < 0)
            return 0;

        M += g->V[u + 1] - g->V[u];

        for (int i = g->V[u]; i < g->V[u + 1]; i++)
        {
            if (i < 0 || i >= g->V[g->n])
                return 0;

            int v = g->E[i];
            if (v < 0 || v >= g->n || v == u || (i > g->V[u] && v <= g->E[i - 1]))
                return 0;
        }
    }

    if (M != g->V[g->n])
        return 0;

    return 1;
}