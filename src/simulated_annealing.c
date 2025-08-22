#include "simulated_annealing.h"

#include <stdlib.h>

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

    return sa;
}

void simulated_annealing_free(simulated_annealing *sa)
{
    free(sa->L);
    free(sa->K);
    free(sa->Community);

    free(sa);
}

double simulated_annealing_get_modularity_score(simulated_annealing *sa, graph *g)
{
    return (double)sa->n / (16.0 * g->m * g->m);
}

static inline void simulated_annealing_move_vertex(simulated_annealing *sa, graph *g, int u, int c)
{
    int old_c = sa->Community[u];
    int degree = g->V[u + 1] - g->V[u];
    sa->K[old_c] -= degree;
    sa->K[c] += degree;

    int old_internal = 0, new_internal = 0;
    for (int i = g->V[u]; i < g->V[u + 1]; i++)
    {
        int v = g->E[i];
        if (sa->Community[v] == old_c)
            old_internal++;
        else if (sa->Community[v] == c)
            new_internal++;
    }

    sa->L[old_c] -= old_internal;
    sa->L[c] += new_internal;

    sa->l_sum -= old_internal;
    sa->l_sum += new_internal;

    sa->s += 2 * degree * degree + 2 * degree * (sa->K[c] - sa->K[old_c]);
    sa->n = 4 * g->m * sa->l_sum - sa->s;
}

void simulated_annealing_run(simulated_annealing *sa, graph *g)
{
    
}