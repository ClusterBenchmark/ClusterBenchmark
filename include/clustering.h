#pragma once

#include "graph.h"

typedef struct
{
    int cluster_count;         // Number of clusters
    long long modularity;      // Modularity * 4m^2
    long long edge_weight_sum; // Total sum of edge weights (counted once)
    int *Cluster;              // Cluster assignment
    long long *Cluster_degree; // Sum of degrees in each cluster

    long long *V_end;     // End pointer for each neighborhood in clustering graph
    int *E_cluster;       // Cluster id for clustering graph
    long long *E_count;   // Cluster count for clustering graph
    int *Valid;           // Valid flag for clustering graph structure
    int update_threshold; // Ratio between clusters and neighbors
    int update_max;       // Max number of clusters to update

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

typedef struct
{
    int cluster_count;         // Number of clusters
    __int128_t modularity;     // Modularity * 4m^2
    long long edge_weight_sum; // Total sum of edge weights (counted once)
    int *Cluster;              // Cluster assignment
    long long *Cluster_degree; // Sum of degrees in each cluster
    long long *Temp_counter;   // Temporary counter for best move computation
} clustering_sparse;

/*  Initialize the clustering struct for the given graph. */
clustering_sparse *clustering_sparse_init(graph *g);

/*  Release memory allocated for the clustering struct, including the *c pointer. */
void clustering_sparse_free(clustering_sparse *c);

/*  Reset clustering for the given graph. */
void clustering_sparse_reset(clustering_sparse *c, graph *g);

/*  Update the clusterig given another clustering. */
void clustering_sparse_set_clustering(clustering_sparse *c, graph *g, int *C);

/*  Update the clusterig given another clustering. */
void clustering_sparse_update(clustering_sparse *c, graph *g, clustering_sparse *cd, int *FM);

/*  Returns the modularity score for the current clustering. */
double clustering_sparse_get_modularity(clustering_sparse *c);

/*  Move vertex u to the cluster c_new. */
void clustering_sparse_move_vertex(clustering_sparse *c, graph *g, int u, int c_new);

/*  Get the modularity delta by moving vertex u to the cluster c_new. */
long long clustering_sparse_compute_move_delta(clustering_sparse *c, graph *g, int u, int c_new);

/*  Move vertex u to the cluster c_new reusing computed delta. */
void clustering_sparse_move_vertex_delta(clustering_sparse *c, graph *g, int u, int c_new, long long delta);

/*  Move vertex u to the best possible cluster.

    Returns 1 if the vertex moved, otherwise 0.
*/
int clustering_sparse_best_move(clustering_sparse *c, graph *g, int u);
