#include "graph.h"

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <assert.h>
#include <limits.h>

void z_score_long(long long *In, int n, float *Out)
{
    long long sum = 0;
    for (int i = 0; i < n; i++)
    {
        sum += In[i];
    }

    double avg = (double)sum / (double)n;
    double sum_div = 0;

    for (int i = 0; i < n; i++)
    {
        sum_div += ((double)In[i] - avg) * ((double)In[i] - avg);
    }

    double std_dev = sqrt(sum_div / (double)n);

    for (int i = 0; i < n; i++)
    {
        Out[i] = ((double)In[i] - avg) / std_dev;
    }
}

void z_score_double(double *In, int n, float *Out)
{
    double sum = 0;
    for (int i = 0; i < n; i++)
    {
        sum += In[i];
    }

    double avg = sum / (double)n;
    double sum_div = 0;

    for (int i = 0; i < n; i++)
    {
        sum_div += (In[i] - avg) * (In[i] - avg);
    }

    double std_dev = sqrt(sum_div / (double)n);

    for (int i = 0; i < n; i++)
    {
        Out[i] = (In[i] - avg) / std_dev;
    }
}

void triangle_count(graph *g, long long *T)
{
#pragma omp parallel for schedule(dynamic, 256)
    for (int u = 0; u < g->n; u++)
    {
        T[u] = 0;
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];

            long long i1 = g->V[u], i2 = g->V[v];
            while (i1 < g->V[u + 1] && i2 < g->V[v + 1])
            {
                if (g->E[i1] < g->E[i2])
                {
                    i1++;
                }
                else if (g->E[i1] > g->E[i2])
                {
                    i2++;
                }
                else
                {
                    T[u]++;
                    i1++;
                    i2++;
                }
            }
        }
        assert((T[u] % 2) == 0);
        T[u] /= 2;
    }
}

float *degree_norm(graph *g)
{
    float *res = malloc(sizeof(float) * g->n);
    long long *tmp = malloc(sizeof(long long) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        tmp[u] = g->V[u + 1] - g->V[u];
    }

    z_score_long(tmp, g->n, res);

    free(tmp);

    return res;
}

float *log_degree_norm(graph *g)
{
    float *res = malloc(sizeof(float) * g->n);
    double *tmp = malloc(sizeof(double) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        tmp[u] = log(1 + (g->V[u + 1] - g->V[u]));
    }

    z_score_double(tmp, g->n, res);

    free(tmp);

    return res;
}

float *mean_neighbor_degree(graph *g)
{
    float *res = malloc(sizeof(float) * g->n);
    double *tmp = malloc(sizeof(double) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        tmp[u] = 0.0;
        int degree = g->V[u + 1] - g->V[u];

        if (degree == 0)
            continue;

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            tmp[u] += g->V[v + 1] - g->V[v];
        }

        tmp[u] /= (double)degree;
    }

    z_score_double(tmp, g->n, res);

    free(tmp);

    return res;
}

float *clustering_coefficient(graph *g, long long *T)
{
    float *res = malloc(sizeof(float) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        float degree = g->V[u + 1] - g->V[u];
        if (degree < 2)
            res[u] = 0.0f;
        else
            res[u] = (double)(2 * T[u]) / (double)(degree * (degree - 1));
    }

    return res;
}

// NB! Slow implementation, but should be okay for most instances
float *k_core(graph *g)
{
    int *degree = malloc(sizeof(int) * g->n);
    int *S = malloc(sizeof(int) * g->n);
    int *T = malloc(sizeof(int) * g->n);
    double *C = malloc(sizeof(double) * g->n);
    float *res = malloc(sizeof(float) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        degree[u] = g->V[u + 1] - g->V[u];
        S[u] = u;
    }

    int s = g->n, t = 0, d = 0;
    while (s > 0)
    {
        for (int i = 0; i < s; i++)
        {
            int u = S[i];
            if (degree[u] <= d)
            {
                C[u] = d;
                for (long long j = g->V[u]; j < g->V[u + 1]; j++)
                {
                    int v = g->E[j];
                    degree[v]--;
                }
            }
            else
            {
                T[t++] = u;
            }
        }

        if (t == s)
            d++;

        s = t;
        t = 0;

        int *tmp = S;
        S = T;
        T = tmp;
    }

    z_score_double(C, g->n, res);

    free(degree);
    free(S);
    free(T);
    free(C);

    return res;
}

float *ego_edge_density(graph *g, long long *T)
{
    double *tmp = malloc(sizeof(double) * g->n);
    float *res = malloc(sizeof(float) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        float degree = g->V[u + 1] - g->V[u];
        if (degree < 2)
            tmp[u] = 0.0f;
        else
            tmp[u] = (double)(3 * T[u]) / (double)degree;
    }

    z_score_double(tmp, g->n, res);

    free(tmp);

    return res;
}

float *pagerank(graph *g)
{
    double *PR = malloc(sizeof(double) * g->n);
    double *PR_next = malloc(sizeof(double) * g->n);
    float *res = malloc(sizeof(float) * g->n);

    for (int i = 0; i < g->n; i++)
    {
        PR[i] = 1.0 / (double)g->n;
    }

    for (int it = 0; it < 100; it++)
    {
        for (int i = 0; i < g->n; i++)
        {
            PR_next[i] = (1.0 - 0.85) / (double)g->n;
        }

        for (int u = 0; u < g->n; u++)
        {
            double degree = g->V[u + 1] - g->V[u];
            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                int v = g->E[i];
                PR_next[v] += 0.85 * PR[u] / degree;
            }
        }

        double *T = PR;
        PR = PR_next;
        PR_next = T;
    }

    z_score_double(PR, g->n, res);

    free(PR);
    free(PR_next);

    return res;
}

float *approx_eccentricity(graph *g)
{
    int n = sqrt(g->n);

    long long *ecc = calloc(g->n, sizeof(long long));
    float *res = malloc(sizeof(float) * g->n);
    int *dist = malloc(sizeof(int) * g->n);

    int *S = malloc(sizeof(int) * g->n);
    int *T = malloc(sizeof(int) * g->n);

    for (int it = 0; it < n; it++)
    {
        for (int i = 0; i < g->n; i++)
            dist[i] = INT_MAX;

        int u = rand() % g->n;

        S[0] = u;
        dist[u] = 0;
        int s = 1, t = 0;

        while (s > 0)
        {
            for (int i = 0; i < s; i++)
            {
                u = S[i];
                for (long long j = g->V[u]; j < g->V[u + 1]; j++)
                {
                    int v = g->E[j];
                    if (dist[v] == INT_MAX)
                    {
                        dist[v] = dist[u] + 1;
                        T[t++] = v;
                        ecc[v] = ecc[v] < dist[v] ? dist[v] : ecc[v];
                    }
                }
            }

            s = t;
            t = 0;

            int *tmp = S;
            S = T;
            T = tmp;
        }
    }

    z_score_long(ecc, g->n, res);

    free(ecc);
    free(dist);
    free(S);
    free(T);

    return res;
}

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);

    printf("%lld %lld\n", g->n, g->m / 2);

    long long *T = calloc(g->n, sizeof(long long));

    triangle_count(g, T);

    float *degree = degree_norm(g);
    float *log_degree = log_degree_norm(g);
    float *mean_n_degree = mean_neighbor_degree(g);
    float *cc = clustering_coefficient(g, T);
    float *core = k_core(g);
    float *eed = ego_edge_density(g, T);
    float *rank = pagerank(g);
    float *ecc = approx_eccentricity(g);

    f = fopen(argv[2], "w");
    fprintf(f, "%lld %d\n", g->n, 8);
    for (int u = 0; u < g->n; u++)
    {
        fprintf(f, "%9.6f %9.6f %9.6f %9.6f %9.6f %9.6f %9.6f %9.6f\n", degree[u], log_degree[u],
                mean_n_degree[u], cc[u], core[u], eed[u], rank[u], ecc[u]);
    }
    fclose(f);

    graph_free(g);
    free(T);
    free(degree);
    free(log_degree);
    free(mean_n_degree);
    free(cc);
    free(core);
    free(eed);
    free(rank);
    free(ecc);

    return 0;
}