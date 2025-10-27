#define _GNU_SOURCE

#include "graph.h"
#include "util.h"

#include <assert.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <omp.h>

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
        VW[u] = 0;
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

            VW[u] += EW[ei];
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

int graph_validate(graph *g)
{
    long long *Edge_pos = malloc(sizeof(long long) * g->n);

    long long M = 0;
    for (int u = 0; u < g->n; u++)
    {
        Edge_pos[u] = g->V[u + 1];

        long long d_u = g->V[u + 1] - g->V[u];
        if (d_u < 0)
        {
            fprintf(stderr, "Error in neighborhood list V: Vertex %d starts at position "
                            "%lld and ends at position %lld\n",
                    u + 1, g->V[u], g->V[u + 1]);
            return 0;
        }

        M += d_u;

        int first = 1;
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            if (i < 0 || i >= g->m)
            {
                fprintf(stderr, "Error in neighborhood list V: Vertex %d starts at position "
                                "%lld and ends at position %lld\n",
                        u + 1, g->V[u], g->V[u + 1]);
                return 0;
            }

            int v = g->E[i];
            if (v < 0 || v >= g->n)
            {
                fprintf(stderr, "Edge endpoint out of bounds for {%d,%d}\n", u + 1, v + 1);
                return 0;
            }
            if (v == u)
            {
                fprintf(stderr, "Self edges are not allowd {%d,%d}\n", u + 1, u + 1);
                return 0;
            }
            if (i > g->V[u] && v <= g->E[i - 1])
            {
                fprintf(stderr, "Unsorted neighborhood for vertex %d: {...,%d,%d,...}\n", u + 1, g->E[i - 1] + 1, v + 1);
                return 0;
            }

            if (u > v)
            {
                if (Edge_pos[v] >= g->V[v + 1] || g->E[Edge_pos[v]] != u)
                {
                    if (Edge_pos[v] >= g->V[v + 1] || g->E[Edge_pos[v]] > u)
                        fprintf(stderr, "Undirected edge encountered: Found {%d,%d} but not {%d,%d}\n", u + 1, v + 1, v + 1, u + 1);
                    else
                        fprintf(stderr, "Undirected edge encountered: Found {%d,%d} but not {%d,%d}\n", v + 1, g->E[Edge_pos[v]] + 1, g->E[Edge_pos[v]] + 1, v + 1);
                    return 0;
                }
                Edge_pos[v]++;
            }
            else if (first)
            {
                Edge_pos[u] = i;
                first = 0;
            }
        }
    }

    for (int u = 0; u < g->n; u++)
    {
        if (Edge_pos[u] != g->V[u + 1])
        {
            int v = g->E[Edge_pos[u]];
            fprintf(stderr, "Undirected edge encountered: Found {%d,%d} but not {%d,%d}\n", u + 1, v + 1, v + 1, u + 1);
            return 0;
        }
    }

    if (M != g->V[g->n] || M != g->m)
    {
        fprintf(stderr, "Wrong edge count, found %lld, but file says %lld\n", M / 2, g->m / 2);
        return 0;
    }

    free(Edge_pos);

    return 1;
}

void graph_contract(graph *g, graph *gc, int *A, int *FM)
{
    int *Temp_FM = malloc(sizeof(int) * g->n);

    // Step 1. Label propagation
    for (int u = 0; u < g->n; u++)
        Temp_FM[u] = u;

    int change = 1;
    while (change)
    {
        change = 0;
        for (int u = 0; u < g->n; u++)
        {
            int min = Temp_FM[u];
            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                int v = g->E[i];
                if (A[i] && Temp_FM[v] < min)
                    min = Temp_FM[v];
            }
            if (min != Temp_FM[u])
            {
                Temp_FM[u] = min;
                change = 1;
            }
        }
    }

    // Step 2. Compact labels
    gc->n = 0;
    for (int u = 0; u < g->n; u++)
    {
        if (Temp_FM[u] == u)
            FM[u] = gc->n++;
    }
    for (int u = 0; u < g->n; u++)
    {
        if (Temp_FM[u] != u)
            FM[u] = FM[Temp_FM[u]];
    }

    free(Temp_FM);

    // Step 3. Combine CSR
    long long *D = malloc(sizeof(long long) * gc->n);
    for (int i = 0; i < gc->n; i++)
        D[i] = 0;

    for (int u = 0; u < g->n; u++)
    {
        D[FM[u]] += g->V[u + 1] - g->V[u];
    }

    for (int u = 0; u < gc->n; u++)
    {
        gc->VW[u] = 0;
    }

    long long ps = 0;
    for (int u = 0; u < gc->n; u++)
    {
        gc->V[u] = ps;
        ps += D[u];
        D[u] = 0;
    }
    gc->V[gc->n] = ps;

    for (int u = 0; u < g->n; u++)
    {
        int uc = FM[u];
        gc->VW[uc] += g->VW[u];
        for (long long i = g->V[u]; i < g->V[u + 1]; i++)
        {
            gc->E[gc->V[uc] + D[uc]] = FM[g->E[i]];
            gc->EW[gc->V[uc] + D[uc]] = g->EW[i];
            D[uc]++;
        }
    }

    free(D);

    // Step 4. Contract edges
    long long *Count = malloc(sizeof(long long) * gc->n);
    for (int u = 0; u < gc->n; u++)
    {
        Count[u] = 0;
    }

    gc->m = 0;
    long long s = 0;
    gc->V[0] = 0;
    for (int u = 0; u < gc->n; u++)
    {
        for (long long i = s; i < gc->V[u + 1]; i++)
        {
            Count[gc->E[i]] += gc->EW[i];
        }
        for (long long i = s; i < gc->V[u + 1]; i++)
        {
            if (Count[gc->E[i]] == 0)
                continue;

            gc->E[gc->m] = gc->E[i];
            gc->EW[gc->m] = Count[gc->E[i]];
            gc->m++;

            Count[gc->E[i]] = 0;
        }
        s = gc->V[u + 1];
        gc->V[u + 1] = gc->m;
    }

    free(Count);
}

/*  Compute a common new label for all vertices in each component in parallel using label propagation.
    Assums it was called inside a parallel region.
    Shared_tmp needs at least 3 elements. */
void graph_contract_label_propagation(graph *g, int *A, int *FM, int *Shared_tmp)
{
    // Roatate over three shared changed ints.

    int p = 0;
    Shared_tmp[p] = 1;
    Shared_tmp[p + 1] = 0;

    // Reset forward mapping.

#pragma omp for
    for (int u = 0; u < g->n; u++)
    {
        FM[u] = u;
    }

    // While some vertex changed label.

    while (Shared_tmp[p])
    {

        // Rotate to next changed int.

        p = (p + 1) % 3;
#pragma omp single nowait
        {
            // Reset next changed int.

            Shared_tmp[(p + 1) % 3] = 0;
        }

        // Update labels to min in neighborhood.

#pragma omp for schedule(dynamic, 256)
        for (int u = 0; u < g->n; u++)
        {
            int min = FM[u];
            for (long long i = g->V[u]; i < g->V[u + 1]; i++)
            {
                int v = g->E[i];
                if (A[i] && FM[v] < min)
                    min = FM[v];
            }
            if (min != FM[u])
            {
                FM[u] = min;
                Shared_tmp[p] = 1;
            }
        }
    }
}

/*  Computes compact labels from 0 to n - 1 given the old forward mapping in parallel.
    Assums it was called inside a parallel region.
    Returns the number of labels. */
int graph_contract_compact_labels(graph *g, int *FM_old, int *FM_new, int *Shared_nt)
{
    int tid = omp_get_thread_num();
    int nt = omp_get_num_threads();

    // Count number of new labels in local area.

    int n = 0;
#pragma omp for nowait
    for (int u = 0; u < g->n; u++)
    {
        n += (FM_old[u] == u);
    }
    Shared_nt[tid] = n;

#pragma omp barrier

    // Compute offset for this thread.

    int ps = 0;
    for (int i = 0; i < tid; i++)
        ps += Shared_nt[i];

    n = 0;

    // Assign final label for the representative in each label group.

#pragma omp for
    for (int u = 0; u < g->n; u++)
    {
        if (FM_old[u] == u)
            FM_new[u] = ps + n++;
    }

    // Assign final label to all vertices.

#pragma omp for nowait
    for (int u = 0; u < g->n; u++)
    {
        FM_new[u] = FM_new[FM_old[u]];
    }

    // Compute return value.

    n = 0;
    for (int i = 0; i < nt; i++)
        n += Shared_nt[i];

#pragma omp barrier

    return n;
}

/*  Computes a graph structure for the new supernodes in standard CSR format.
    The neighborhood of each supernode is the set of old vertices that make up this supernode.
    Assums it was called inside a parallel region.
    Dt must be nt x n. */
void graph_contract_group_supernodes(graph *g, int n, int *FM, int *V, int *E, long long **Dt, int *Shared_nt)
{
    int tid = omp_get_thread_num();
    int nt = omp_get_num_threads();

    long long *D = Dt[tid];

    // Reset local counters.

    for (int u = 0; u < n; u++)
    {
        D[u] = 0;
    }

    // Count vertices in each supernode.

#pragma omp for
    for (int u = 0; u < g->n; u++)
    {
        D[FM[u]]++;
    }

    // Combine counts from each thread.

    int sum = 0;

#pragma omp for nowait
    for (int u = 0; u < n; u++)
    {
        for (int t = 0; t < nt; t++)
        {
            sum += Dt[t][u];
        }
    }

    // Communicate sums.

    Shared_nt[tid] = sum;

#pragma omp barrier

    // Prefix sum.

    int offset = 0;
    for (int i = 0; i < tid; i++)
        offset += Shared_nt[i];

    // Compute final edgelist offsets.

    V[0] = 0;

#pragma omp for
    for (int u = 0; u < n; u++)
    {
        for (int t = 0; t < nt; t++)
        {
            offset += Dt[t][u];
            Dt[t][u] = offset - Dt[t][u];
        }
        V[u + 1] = offset;
    }

    // Populate edgelist.

#pragma omp for
    for (int u = 0; u < g->n; u++)
    {
        E[D[FM[u]]++] = u;
    }
}

/*  Computes the contracted graph structure in CSR format.
    Assums it was called inside a parallel region.
    V and E must hold the list of vertices in each supernode.
    Dt must be nt x n_c. */
void graph_contract_construct_contracted(graph *g, graph *gc, int *FM, int *V, int *E, long long *S, long long **Dt, int *Shared_nt)
{
    int tid = omp_get_thread_num();
    int nt = omp_get_num_threads();

    long long *D = Dt[tid];

    // Reset local counters

    for (int u = 0; u < gc->n; u++)
    {
        D[u] = 0;
    }

    // Compute the degree for each supernode

#pragma omp for schedule(dynamic, 4)
    for (int u = 0; u < gc->n; u++)
    {
        int count = 0;
        gc->VW[u] = 0;
        for (int i = V[u]; i < V[u + 1]; i++)
        {
            int v = E[i];
            gc->VW[u] += g->VW[v];
            for (long long j = g->V[v]; j < g->V[v + 1]; j++)
            {
                int w = FM[g->E[j]];
                if (D[w] == 0)
                    count++;
                D[w] = 1;
            }
        }
        S[u] = count;
        for (int i = V[u]; i < V[u + 1]; i++)
        {
            int v = E[i];
            for (long long j = g->V[v]; j < g->V[v + 1]; j++)
            {
                int w = FM[g->E[j]];
                D[w] = 0;
            }
        }
    }

    gc->V[0] = 0;

    // Sync up and count

#pragma omp barrier

    int m = 0;

#pragma omp for
    for (int u = 0; u < gc->n; u++)
    {
        m += S[u];
    }

    Shared_nt[tid] = m;

    // Prefix sum

#pragma omp barrier

    int ps = 0;

    for (int i = 0; i < tid; i++)
        ps += Shared_nt[i];

#pragma omp for
    for (int u = 0; u < gc->n; u++)
    {
        ps += S[u];
        S[u] = ps - S[u];
    }

    // Populate the contracted graph

#pragma omp for schedule(dynamic, 4)
    for (int u = 0; u < gc->n; u++)
    {
        for (int i = V[u]; i < V[u + 1]; i++)
        {
            int v = E[i];
            for (long long j = g->V[v]; j < g->V[v + 1]; j++)
            {
                int w = FM[g->E[j]];
                D[w] += g->EW[j];
            }
        }
        for (int i = V[u]; i < V[u + 1]; i++)
        {
            int v = E[i];
            for (long long j = g->V[v]; j < g->V[v + 1]; j++)
            {
                int w = FM[g->E[j]];
                if (D[w] == 0)
                    continue;

                gc->E[S[u]] = w;
                gc->EW[S[u]] = D[w];
                S[u]++;
                D[w] = 0;
            }
        }
        gc->V[u + 1] = S[u];
    }

    gc->m = S[gc->n - 1];
}

void graph_contract_par(graph *g, graph *gc, int *A, int *FM)
{
    int T[3] = {0, 0, 0};
    int *C = NULL;
    long long **Dt = NULL;
    int *V = malloc(sizeof(int) * (g->n + 1));
    int *E = malloc(sizeof(int) * g->n);
    long long *S = malloc(sizeof(long long) * g->n);

#pragma omp parallel
    {
        int nt = omp_get_num_threads();
        int tid = omp_get_thread_num();

#pragma omp single
        {
            C = malloc(sizeof(int) * nt);
            Dt = malloc(sizeof(long long *) * nt);
        }

        Dt[tid] = malloc(sizeof(long long) * g->n);

        graph_contract_par_internal(g, gc, A, FM, V, E, S, Dt, C, T);

        free(Dt[tid]);

#pragma omp barrier

#pragma omp single
        {
            free(C);
            free(Dt);
        }
    }

    free(V);
    free(E);
    free(S);
}

void graph_contract_par_internal(graph *g, graph *gc, int *A, int *FM,
                                 int *V, int *E, long long *S, long long **Dt, int *C, int *T)
{
    graph_contract_label_propagation(g, A, V, T);
    int n = graph_contract_compact_labels(g, V, FM, C);
    gc->n = n;
    graph_contract_group_supernodes(g, n, FM, V, E, Dt, C);
    graph_contract_construct_contracted(g, gc, FM, V, E, S, Dt, C);
}
