#include "graph.h"

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    printf("%lld %lld\n", g->n, g->m);

    if (!graph_validate(g))
        printf("Error in graph\n");

    graph_free(g);

    return 0;
}