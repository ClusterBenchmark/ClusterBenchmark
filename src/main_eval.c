#include "graph.h"
#include "util.h"

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

    util_skip_line(Data, &p);

    long long id, c;
    for (int u = 0; u < n; u++)
    {
        util_parse_id(Data, &p, &id);
        util_parse_id(Data, &p, &c);
        util_skip_line(Data, &p);
        cluster[id] = c;
    }

    munmap(Data, size);

    return cluster;
}

void compute_modularity(graph *g, int *cluster, long long *n, double *q, int *n_clusters)
{
    *n_clusters = 0;
    for (int u = 0; u < g->n; u++)
    {
        if (cluster[u] + 1 > *n_clusters)
            *n_clusters = cluster[u] + 1;
    }

    long long *community_weight = calloc(*n_clusters, sizeof(long long));
    long long *community_edges = calloc(*n_clusters, sizeof(long long));

    for (int u = 0; u < g->n; u++)
    {
        community_weight[cluster[u]] += g->VW[u];

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            if (cluster[u] == cluster[v])
                community_edges[cluster[u]] += g->EW[i];
        }
    }

    long long s = 0, l_sum = 0;

    for (int i = 0; i < *n_clusters; i++)
    {
        s += community_weight[i] * community_weight[i];
        l_sum += community_edges[i];
    }

    *n = 2ll * g->m * l_sum - s;
    *q = (double)*n / (4.0 * g->m * g->m);

    free(community_weight);
    free(community_edges);
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
        fprintf(stderr, "Usage: %s <metis_graph> <clustering_csv> {<ground_truth_csv>}\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (f == NULL)
        printf("Failed to open graph file\n");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);
    graph_default_weights(g);

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
    long long n;
    int n_clusters;
    compute_modularity(g, cluster, &n, &q, &n_clusters);
    printf(",%.8lf,%lld,%d", q, n, n_clusters);

    if (truth != NULL)
    {
        int tp, fp, tn, fn;
        compute_metrics(g, cluster, truth, &tp, &fp, &tn, &fn);

        printf(",%.8lf", (2.0 * (double)tp) / (2.0 * (double)tp + (double)fp + (double)fn));
        printf(",%.8lf", (double)(tp + tn) / (double)g->V[g->n]);
    }

    // printf("\n");

    graph_free(g);
    free(cluster);
    free(truth);

    return 0;
}