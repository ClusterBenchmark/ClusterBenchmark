#include "graph.h"

#include <stdlib.h>
#include <sys/mman.h>

static inline void parse_id(char *Data, size_t *p, long long *v)
{
    while ((Data[*p] < '0' || Data[*p] > '9') && Data[*p] != '\n')
        (*p)++;

    *v = 0;
    while (Data[*p] >= '0' && Data[*p] <= '9')
        *v = (*v) * 10 + Data[(*p)++] - '0';
}

static inline void skip_line(char *Data, size_t *p)
{
    while (Data[*p] != '\n')
        (*p)++;
    (*p)++;
}

static inline int compare(const void *a, const void *b)
{
    return (*(int *)a - *(int *)b);
}

graph *graph_parse(FILE *f)
{
    fseek(f, 0, SEEK_END);
    size_t size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *Data = mmap(0, size, PROT_READ, MAP_PRIVATE, fileno_unlocked(f), 0);
    size_t p = 0;

    while (Data[p] == '%')
        skip_line(Data, &p);

    long long n, m, t;
    parse_id(Data, &p, &n);
    parse_id(Data, &p, &m);
    parse_id(Data, &p, &t);

    skip_line(Data, &p);

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
            skip_line(Data, &p);

        if (VW != NULL)
            parse_id(Data, &p, VW + u);

        V[u] = ei;
        while (ei < m * 2)
        {
            while (Data[p] == ' ')
                p++;
            if (Data[p] == '\n')
                break;

            long long e;
            parse_id(Data, &p, &e);
            E[ei] = e - 1;

            if (EW != NULL)
                parse_id(Data, &p, EW + ei);

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