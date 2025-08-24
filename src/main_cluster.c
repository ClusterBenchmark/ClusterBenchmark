#include <graph.h>
#include <local_search.h>

#include <stdlib.h>

int path_name_offset(char *path)
{
    int offset = 0;
    for (int i = 0; path[i] != '\0'; i++)
    {
        if (path[i] == '/')
            offset = i + 1;
    }
    return offset;
}

int main(int argc, char **argv)
{
    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    if (!graph_validate(g))
        printf("Error in graph\n");

    local_search *ls = local_search_init(g, 0);

    printf("%20s,%10d,%10d,%10.6lf\n",
           argv[1] + path_name_offset(argv[1]),
           g->n, g->m,
           local_search_get_modularity_score(ls, g));

    local_search_explore(ls, g, 600.0, 1);

    int *FM = malloc(sizeof(int) * g->n);
    for (int i = 0; i < g->n; i++)
        FM[i] = -1;

    int c = 0;
    for (int u = 0; u < g->n; u++)
    {
        if (FM[ls->Community[u]] < 0)
            FM[ls->Community[u]] = c++;
    }

    f = fopen("clusters.csv", "w");
    fprintf(f, "id,cluster\n");
    for (int u = 0; u < g->n; u++)
    {
        fprintf(f, "%d,%d\n", u, FM[ls->Community[u]]);
    }
    fclose(f);

    free(FM);

    graph_free(g);
    local_search_free(ls);

    return 0;
}