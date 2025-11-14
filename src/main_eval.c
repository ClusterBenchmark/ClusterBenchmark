#include "graph.h"
#include "util.h"

#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>

typedef struct
{
    int cluster;
    int truth;
} cluster_pair;

static int cluster_pair_compare(const void *a, const void *b)
{
    const cluster_pair *pa = (const cluster_pair *)a;
    const cluster_pair *pb = (const cluster_pair *)b;
    if (pa->cluster != pb->cluster)
        return pa->cluster - pb->cluster;
    return pa->truth - pb->truth;
}

static inline long double comb2_long_long(long long x)
{
    if (x < 2)
        return 0.0L;
    return ((long double)x * (long double)(x - 1)) / 2.0L;
}

static int *extract_unique_labels(int *labels, int n, int *count)
{
    if (n == 0)
    {
        *count = 0;
        return NULL;
    }

    int *temp = malloc(n * sizeof(int));
    for (int i = 0; i < n; i++)
        temp[i] = labels[i];
    qsort(temp, n, sizeof(int), util_compare);

    int unique = 0;
    for (int i = 0; i < n; i++)
    {
        if (i == 0 || temp[i] != temp[i - 1])
            unique++;
    }

    int *values = malloc(unique * sizeof(int));
    int idx = 0;
    for (int i = 0; i < n; i++)
    {
        if (i == 0 || temp[i] != temp[i - 1])
            values[idx++] = temp[i];
    }

    free(temp);
    *count = unique;
    return values;
}

void compute_supervised_additional_metrics(int *clusters, int *truth, int n,
                                           double *ari, double *nmi,
                                           double *purity, double *inv_purity)
{
    if (n == 0)
    {
        *ari = 0.0;
        *nmi = 0.0;
        *purity = 0.0;
        *inv_purity = 0.0;
        return;
    }

    int n_clusters_pred, n_clusters_truth;
    int *cluster_ids = extract_unique_labels(clusters, n, &n_clusters_pred);
    int *truth_ids = extract_unique_labels(truth, n, &n_clusters_truth);

    long long *cluster_sizes = calloc(n_clusters_pred, sizeof(long long));
    long long *truth_sizes = calloc(n_clusters_truth, sizeof(long long));
    long long *best_cluster_overlap = calloc(n_clusters_pred, sizeof(long long));
    long long *best_truth_overlap = calloc(n_clusters_truth, sizeof(long long));
    cluster_pair *pairs = malloc(n * sizeof(cluster_pair));

    for (int i = 0; i < n; i++)
    {
        int c_idx = lower_bound(cluster_ids, n_clusters_pred, clusters[i]);
        int t_idx = lower_bound(truth_ids, n_clusters_truth, truth[i]);
        cluster_sizes[c_idx]++;
        truth_sizes[t_idx]++;
        pairs[i].cluster = c_idx;
        pairs[i].truth = t_idx;
    }

    qsort(pairs, n, sizeof(cluster_pair), cluster_pair_compare);

    long double pair_sum = 0.0L;
    long double mutual_info = 0.0L;

    int pos = 0;
    while (pos < n)
    {
        int c = pairs[pos].cluster;
        int t = pairs[pos].truth;
        long long overlap = 0;
        while (pos < n && pairs[pos].cluster == c && pairs[pos].truth == t)
        {
            overlap++;
            pos++;
        }

        pair_sum += comb2_long_long(overlap);

        if (overlap > best_cluster_overlap[c])
            best_cluster_overlap[c] = overlap;
        if (overlap > best_truth_overlap[t])
            best_truth_overlap[t] = overlap;

        long double pij = (long double)overlap / (long double)n;
        long double pc = (long double)cluster_sizes[c] / (long double)n;
        long double pt = (long double)truth_sizes[t] / (long double)n;

        if (pij > 0.0L && pc > 0.0L && pt > 0.0L)
            mutual_info += pij * logl(pij / (pc * pt));
    }

    long double cluster_comb = 0.0L;
    for (int i = 0; i < n_clusters_pred; i++)
        cluster_comb += comb2_long_long(cluster_sizes[i]);

    long double truth_comb = 0.0L;
    for (int i = 0; i < n_clusters_truth; i++)
        truth_comb += comb2_long_long(truth_sizes[i]);

    long double total_pairs = comb2_long_long(n);
    long double expected_index = 0.0L;
    if (total_pairs > 0.0L)
        expected_index = (cluster_comb * truth_comb) / total_pairs;

    long double max_index = 0.5L * (cluster_comb + truth_comb);
    long double denominator = max_index - expected_index;
    long double ari_val = 0.0L;

    if (total_pairs > 0.0L && denominator > 0.0L)
        ari_val = (pair_sum - expected_index) / denominator;
    *ari = (double)ari_val;

    long double entropy_clusters = 0.0L;
    for (int i = 0; i < n_clusters_pred; i++)
    {
        if (cluster_sizes[i] == 0)
            continue;
        long double p = (long double)cluster_sizes[i] / (long double)n;
        entropy_clusters -= p * logl(p);
    }

    long double entropy_truth = 0.0L;
    for (int i = 0; i < n_clusters_truth; i++)
    {
        if (truth_sizes[i] == 0)
            continue;
        long double p = (long double)truth_sizes[i] / (long double)n;
        entropy_truth -= p * logl(p);
    }

    long double nmi_val = 0.0L;
    if (entropy_clusters > 0.0L && entropy_truth > 0.0L)
        nmi_val = mutual_info / sqrtl(entropy_clusters * entropy_truth);
    *nmi = (double)nmi_val;

    long double purity_sum = 0.0L;
    for (int i = 0; i < n_clusters_pred; i++)
        purity_sum += (long double)best_cluster_overlap[i];
    *purity = (double)(purity_sum / (long double)n);

    long double inv_purity_sum = 0.0L;
    for (int i = 0; i < n_clusters_truth; i++)
        inv_purity_sum += (long double)best_truth_overlap[i];
    *inv_purity = (double)(inv_purity_sum / (long double)n);

    free(cluster_ids);
    free(truth_ids);
    free(cluster_sizes);
    free(truth_sizes);
    free(best_cluster_overlap);
    free(best_truth_overlap);
    free(pairs);
}

void compute_structure_metrics(graph *g, int *clusters,
                               double *avg_conductance, double *avg_cut_ratio)
{
    if (g->n == 0)
    {
        *avg_conductance = 0.0;
        *avg_cut_ratio = 0.0;
        return;
    }

    int n_clusters = 0;
    int *cluster_ids = extract_unique_labels(clusters, g->n, &n_clusters);

    long long *node_counts = calloc(n_clusters, sizeof(long long));
    long long *volumes = calloc(n_clusters, sizeof(long long));
    long long *cut_weights = calloc(n_clusters, sizeof(long long));

    for (int u = 0; u < g->n; u++)
    {
        int idx = lower_bound(cluster_ids, n_clusters, clusters[u]);
        node_counts[idx]++;

        long long degree = 0;
        if (g->EW == NULL)
        {
            degree = g->V[u + 1] - g->V[u];
        }
        else
        {
            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
                degree += g->EW[i];
        }
        volumes[idx] += degree;

        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            int v = g->E[i];
            long long weight = (g->EW == NULL) ? 1 : g->EW[i];
            if (clusters[u] != clusters[v])
                cut_weights[idx] += weight;
        }
    }

    long long total_volume = 0;
    for (int i = 0; i < n_clusters; i++)
        total_volume += volumes[i];

    long double conductance_sum = 0.0L;
    long double cut_ratio_sum = 0.0L;

    for (int i = 0; i < n_clusters; i++)
    {
        long double cut = (long double)cut_weights[i] / 2.0L;
        long double vol = (long double)volumes[i];
        long double complement_vol = (long double)total_volume - vol;
        long double denom = vol < complement_vol ? vol : complement_vol;

        long double cond = 0.0L;
        if (denom > 0.0L)
            cond = cut / denom;
        conductance_sum += cond;

        long long nodes = node_counts[i];
        long long other_nodes = g->n - nodes;
        long double cut_ratio = 0.0L;
        long double node_denom = (long double)nodes * (long double)other_nodes;
        if (node_denom > 0.0L)
            cut_ratio = cut / node_denom;
        cut_ratio_sum += cut_ratio;
    }

    *avg_conductance = (double)(conductance_sum / (long double)n_clusters);
    *avg_cut_ratio = (double)(cut_ratio_sum / (long double)n_clusters);

    free(cluster_ids);
    free(node_counts);
    free(volumes);
    free(cut_weights);
}

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
        fprintf(stderr, "Usage: %s <metis_graph> <clustering> {<ground_truth_labels>}\n", argv[0]);
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

    double avg_conductance = 0.0;
    double avg_cut_ratio = 0.0;
    compute_structure_metrics(g, cluster, &avg_conductance, &avg_cut_ratio);
    printf(",%.8lf,%.8lf", avg_conductance, avg_cut_ratio);

    if (truth != NULL)
    {
        int tp, fp, tn, fn;
        compute_metrics(g, cluster, truth, &tp, &fp, &tn, &fn);

        printf(",%.8lf", (2.0 * (double)tp) / (2.0 * (double)tp + (double)fp + (double)fn));
        printf(",%.8lf", (double)(tp + tn) / (double)g->V[g->n]);
        printf(",%d,%d,%d,%d", tp, fp, tn, fn);

        double ari, nmi, purity, inv_purity;
        compute_supervised_additional_metrics(cluster, truth, g->n,
                                              &ari, &nmi, &purity, &inv_purity);
        printf(",%.8lf,%.8lf,%.8lf,%.8lf", ari, nmi, purity, inv_purity);
    }

    printf("\n");

    graph_free(g);
    free(cluster);
    free(truth);

    return 0;
}
