#pragma once

#include "graph.h"

typedef struct
{
    int cluster_count;         // Number of clusters
    long long modularity;      // Modularity * 4m^2
    long long edge_weight_sum; // Total sum of edge weights (counted once)
    int *Cluster;              // Cluster assignment
    long long *Cluster_degree; // Sum of degrees in each cluster

    long long *V_end;   // End pointer for each neighborhood in clustering graph
    int *E_cluster;     // Cluster id for clustering graph
    long long *E_count; // Cluster count for clustering graph
    int *Valid;         // Valid flag for clustering graph structure

    long long *Temp_counter; // Temporary counter for best move computation
} clustering;

/*  Initialize the clustering struct for the given graph. */
clustering *clustering_init(graph *g);

/*  Release memory allocated for the clustering struct, including the *c pointer. */
void clustering_free(clustering *c);

/*  Reset clustering for the given graph. */
void clustering_reset(clustering *c, graph *g);

/*  Update clusterig after d-core. */
void clustering_update(clustering *c, graph *g, clustering *cd, int *FM);

/*  Returns the modularity score for the current clustering. */
double clustering_get_modularity(clustering *c);

/*  Move vertex u to the cluster c_new. */
void clustering_move_vertex(clustering *c, graph *g, int u, int c_new);

/*  Move vertex u to the best possible cluster.

    Returns 1 if the vertex moved, otherwise 0.
*/
int clustering_best_move(clustering *c, graph *g, int u);