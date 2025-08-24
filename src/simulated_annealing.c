#include "simulated_annealing.h"

#include "util.h"

#include <stdlib.h>
#include <math.h>

void simulated_annealing_reset(simulated_annealing *sa, graph *g)
{
    sa->l_sum = 0;
    sa->s = 0;
    for (int u = 0; u < g->n; u++)
    {
        sa->L[u] = 0;
        sa->K[u] = g->V[u + 1] - g->V[u];
        sa->s += sa->K[u] * sa->K[u];
        sa->Community[u] = u;
    }
    sa->n = 4 * g->m * sa->l_sum - sa->s;
}

simulated_annealing *simulated_annealing_init(graph *g)
{
    simulated_annealing *sa = malloc(sizeof(simulated_annealing));

    sa->l_sum = 0;
    sa->s = 0;
    sa->n = 0;

    sa->L = malloc(sizeof(long long) * g->n);
    sa->K = malloc(sizeof(long long) * g->n);
    sa->Community = malloc(sizeof(int) * g->n);

    simulated_annealing_reset(sa, g);

    sa->best_c = malloc(sizeof(int) * g->n);
    for (int i = 0; i < g->n; i++)
        sa->best_c[i] = sa->Community[i];
    sa->best_n = sa->n;

    return sa;
}

void simulated_annealing_free(simulated_annealing *sa)
{
    free(sa->L);
    free(sa->K);
    free(sa->Community);

    free(sa->best_c);

    free(sa);
}

double simulated_annealing_get_modularity_score(simulated_annealing *sa, graph *g)
{
    return (double)sa->n / (4.0 * g->m * g->m);
}

static inline void simulated_annealing_move_vertex(simulated_annealing *sa, graph *g, int u, int c)
{
    int old_c = sa->Community[u];
    if (old_c == c)
        return;

    int degree = g->V[u + 1] - g->V[u];
    long long Ko1 = sa->K[old_c] * sa->K[old_c],
              Kn1 = sa->K[c] * sa->K[c];

    sa->K[old_c] -= degree;
    sa->K[c] += degree;

    long long Ko2 = sa->K[old_c] * sa->K[old_c],
              Kn2 = sa->K[c] * sa->K[c];

    int old_internal = 0, new_internal = 0;
    for (int i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        if (sa->Community[v] == old_c)
            old_internal++;
        if (sa->Community[v] == c)
            new_internal++;
    }

    sa->L[old_c] -= old_internal;
    sa->L[c] += new_internal;

    sa->l_sum -= old_internal;
    sa->l_sum += new_internal;

    sa->s += Ko2 + Kn2 - (Ko1 + Kn1);
    sa->n = 4ll * g->m * sa->l_sum - sa->s;

    sa->Community[u] = c;
}

long long count_internal_edges(simulated_annealing *sa, graph *g)
{
    long long l_sum = 0;

    for (int u = 0; u < g->n; u++)
    {
        for (int i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];

            if (sa->Community[u] == sa->Community[v])
                l_sum++;
        }
    }

    return l_sum / 2;
}

void simulated_annealing_run(simulated_annealing *sa, graph *g)
{
    simulated_annealing_reset(sa, g);

    for (int k = 0; k < (1 << 25); k++)
    {
        double t = 1.0 - ((double)(k + 1) / (double)(1 << 25));
        t /= 8.0;

        int u = rand() % g->n;
        int d = g->V[u + 1] - g->V[u];
        if (d == 0)
            continue;

        int v = g->E[g->V[u] + (rand() % d)];
        int old_c = sa->Community[u];
        int c = sa->Community[v];

        if (old_c == c)
            c = rand() % g->n;

        long long old_n = sa->n;

        simulated_annealing_move_vertex(sa, g, u, c);

        double score = (double)(sa->n - old_n) / 100000.0;
        if (sa->n < old_n && rand() > exp(score / t) * (double)RAND_MAX)
        {
            simulated_annealing_move_vertex(sa, g, u, old_c);
        }

        if (sa->n > sa->best_n)
        {
            sa->best_n = sa->n;
            // for (int u = 0; u < g->n; u++)
            //     sa->best_c[u] = sa->Community[u];
        }

        if ((k % 1028) == 0)
        {
            printf("\r%15d,%12.8lf,%12.8lf,%12.8lf", k, t, simulated_annealing_get_modularity_score(sa, g), (double)sa->best_n / (4.0 * g->m * g->m));
            fflush(stdout);
        }
    }
    printf("\n");
}