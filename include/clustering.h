#pragma once

#include "graph.h"

typedef struct
{
    int cluster_count;
    long long modularity;
    long long edge_weight_sum;

    int *Cluster;
    long long *Cluster_degree;

    int *Temp;
} clustering;

/*  Initialize the clustering struct for the given graph. */
clustering *clustering_init(graph *g);

/*  Release memory allocated for the clustering struct, including the *c pointer. */
void clustering_free(clustering *c);

/*  Reset clustering for the given graph. */
void clustering_reset(clustering *c, graph *g);

/*  Returns the modularity score for the current clustering. */
double clustering_get_modularity(clustering *c);

/*  Move vertex u to the cluster c_new. */
void clustering_move_vertex(clustering *c, graph *g, int u, int c_new);

/*  Move vertex u to the best possible cluster.

    Returns 1 if the vertex moved, otherwise 0.
*/
int clustering_best_move(clustering *c, graph *g, int u);

/*  Clustering CSR graph structure.

    The neighborhood of each vertex is the clusters it sees, including a count for each.

    Should only be used when the number of clusters each vertex sees is small compared to
    its degree.
*/
typedef struct
{
    long long *V_end;
    int *E_cluster, *E_count;
} clustering_graph;

/*  Initialize the clustering graph struct for the given clustering and graph. */
clustering_graph *clustering_graph_init(clustering *c, graph *g);

/*  Release memory allocated for the clustering graph struct, including the *cg pointer. */
void clustering_graph_free(clustering_graph *cg);

/*  Populate the clustering graph for the given graph and clustering */
void clustering_graph_populate(clustering_graph *cg, clustering *c, graph *g);

/*  Move vertex u to the cluster c_new. */
void clustering_graph_move_vertex(clustering_graph *cg, clustering *c, graph *g, int u, int c_new);

/*  Move vertex u to the best possible cluster.

    Returns 1 if the vertex moved, otherwise 0.
*/
int clustering_graph_best_move(clustering_graph *cg, clustering *c, graph *g, int u);