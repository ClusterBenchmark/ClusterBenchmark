#pragma once

#include "graph.h"

typedef struct
{
    int cluster_count;
    long long modularity;
    long long edge_weight_sum;

    int *Cluster;
    long long *Cluster_degree;

    long long *Temp;

    int *Ci, *Cc, *Cs, *Ct;
} clustering;

/*  Initialize the clustering struct for the given graph. */
clustering *clustering_init(graph *g);

/*  Release memory allocated for the clustering struct, including the *c pointer. */
void clustering_free(clustering *c);

/*  Returns the modularity score for the current clustering. */
double clustering_get_modularity(clustering *c);

/*  Move vertex u to the cluster c_new. */
void clustering_move_vertex(clustering *c, graph *g, int u, int c_new);

/*  Move vertex u to the best possible cluster.

    Returns 1 if the vertex moved, otherwise 0.
*/
int clustering_best_move(clustering *c, graph *g, int u);