#pragma once

#include <stdio.h>

/*  Binary CSR container. Layout, all little-endian:

        char      magic[8]      "CBCSRv1", zero padded
        long long n             number of vertices
        long long m             number of directed edges, equal to V[n]
        int       flags         bit 0: edge weights, bit 1: vertex weights
        int       reserved
        long long V[n + 1]      neighborhood offsets
        int       E[m]          edge list
        long long EW[m]         edge weights, only if flag bit 0
        long long VW[n]         vertex weights, only if flag bit 1

    The 32 byte header keeps the following long long array 8 byte aligned so
    the payload can be mapped directly without copying.  */
#define GRAPH_CSR_MAGIC "CBCSRv1"
#define GRAPH_CSR_MAGIC_LEN 8
#define GRAPH_CSR_HEADER_LEN 32
#define GRAPH_CSR_FLAG_EDGE_WEIGHTS 1
#define GRAPH_CSR_FLAG_VERTEX_WEIGHTS 2

typedef struct
{
    long long n, m;     // Number of vertices and edges
    long long *V;       // Neighborhood offsets
    int *E;             // Edge list
    long long *VW, *EW; // Weights for vertices and edges
} graph;

graph *graph_parse(FILE *f);

graph *graph_parse_csr(FILE *f);

/*  Loads either a METIS or a binary CSR file, detected by magic. METIS input
    is sorted and deduplicated on load, CSR input is already canonical. */
graph *graph_load(const char *path);

graph *graph_copy(graph *g);

void graph_free(graph *g);

void graph_sort_edges(graph *g);

int graph_validate(graph *g);

graph *graph_contract_clusters(graph *g, int nc, int *C);

// void graph_contract(graph *g, graph *gc, int *A, int *FM);

// void graph_contract_par(graph *g, graph *gc, int *A, int *FM);

// /*  V, E, and S must be at least n long.
//     C must be at least nt long.
//     Dt must be nt x n.
//     T must hold at least 3 elements. */
// void graph_contract_par_internal(graph *g, graph *gc, int *A, int *FM,
//                                  int *V, int *E, long long *S, long long **Dt, int *C, int *T);