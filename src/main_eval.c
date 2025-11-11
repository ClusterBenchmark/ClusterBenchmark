#include "graph.h"
#include "util.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>

int *clustering_parse(FILE *f, long long n)
{
    int *cluster = malloc(n * sizeof(int));

    fseek(f, 0, SEEK_END);
    size_t size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *Data = mmap(0, size, PROT_READ, MAP_PRIVATE, fileno_unlocked(f), 0);
    size_t p = 0;

    long long c;
    for (int u = 0; u < n; u++)
    {
        util_parse_id(Data, &p, &c);
        util_skip_line(Data, &p);
        cluster[u] = c;
    }

    munmap(Data, size);

    return cluster;
}

void compute_modularity(graph *g, int *cluster, __int128_t *n, double *q, int *n_clusters)
{
    long long edge_weight_sum = 0;
    *n_clusters = 0;

    for (int u = 0; u < g->n; u++)
    {
        if (cluster[u] + 1 > *n_clusters)
            *n_clusters = cluster[u] + 1;

        if (g->EW == NULL)
        {
            edge_weight_sum += g->V[u + 1] - g->V[u];
        }
        else
        {
            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                edge_weight_sum += g->EW[i];
            }
        }
    }

    long long *community_weight = calloc(*n_clusters, sizeof(long long));
    long long l_sum = 0;

    for (int u = 0; u < g->n; u++)
    {
        if (g->EW == NULL)
        {
            community_weight[cluster[u]] += g->V[u + 1] - g->V[u];
            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                if (cluster[u] == cluster[g->E[i]])
                    l_sum++;
            }
        }
        else
        {
            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                community_weight[cluster[u]] += g->EW[i];
                if (cluster[u] == cluster[g->E[i]])
                    l_sum += g->EW[i];
            }
        }
    }

    *n = 0;

    int count = 0;

    for (int i = 0; i < *n_clusters; i++)
    {
        *n -= community_weight[i] * community_weight[i];

        if (community_weight[i] > 0)
            count++;
    }

    *n_clusters = count;

    *n += (__int128_t)edge_weight_sum * (__int128_t)l_sum;

    // Computing modularity score with 9 decimal precision
    __int128_t den = (__int128_t)edge_weight_sum * (__int128_t)edge_weight_sum;
    __int128_t num = (__int128_t)1000000000 * *n;
    *q = (double)(num / den) / 1000000000.0;

    free(community_weight);
}

void compute_metrics(graph *g, int *clusters, int *labels,
                     int *tp, int *fp, int *tn, int *fn)
{
    *tp = 0;
    *fp = 0;
    *tn = 0;
    *fn = 0;

    for (int u = 0; u < g->n; u++)
    {
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (clusters[u] == clusters[v])
            {
                if (labels[u] == labels[v])
                    (*tp)++;
                else
                    (*fp)++;
            }
            else
            {
                if (labels[u] == labels[v])
                    (*fn)++;
                else
                    (*tn)++;
            }
        }
    }
}

int main(int argc, char **argv)
{
    if (argc != 3 && argc != 4)
    {
        fprintf(stderr, "Usage: %s <metis_graph> <clustering> {<ground_truth_csv>}\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (f == NULL)
        printf("Failed to open graph file\n");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);

    if (!graph_validate(g))
    {
        printf("Error in graph\n");
        graph_free(g);
        return 1;
    }

    f = fopen(argv[2], "r");
    if (f == NULL)
        printf("Failed to open clustering file\n");
    int *cluster = clustering_parse(f, g->n);
    fclose(f);

    int *truth = NULL;
    if (argc == 4)
    {
        f = fopen(argv[3], "r");
        if (f == NULL)
            printf("Failed to open ground truth clustering file\n");
        truth = clustering_parse(f, g->n);
        fclose(f);
    }

    int offset = util_path_name_offset(argv[1]);

    printf("%s,%lld,%lld", argv[1] + offset, g->n, g->m);

    double q;
    __int128_t n;
    int n_clusters;
    compute_modularity(g, cluster, &n, &q, &n_clusters);

    printf(",%.9lf", q);
    if (n > LLONG_MAX)
    {
        long long base = 1000000000000000000LL; // 1e18
        long long hi = n / (__int128_t)base;
        long long lo = n % (__int128_t)base;
        printf(",%lld%018lld", hi, lo);
    }
    else
    {
        printf(",%lld", (long long)n);
    }
    printf(",%d", n_clusters);

    if (truth != NULL)
    {
        int tp, fp, tn, fn;
        compute_metrics(g, cluster, truth, &tp, &fp, &tn, &fn);

        printf(",%.8lf", (2.0 * (double)tp) / (2.0 * (double)tp + (double)fp + (double)fn));
        printf(",%.8lf", (double)(tp + tn) / (double)g->V[g->n]);
        printf(",%d,%d,%d,%d", tp, fp, tn, fn);
    }

    printf("\n");

    graph_free(g);
    free(cluster);
    free(truth);

    return 0;
}