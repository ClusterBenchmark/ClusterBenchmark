#include <graph.h>
#include <simulated_annealing.h>

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

    simulated_annealing *sa = simulated_annealing_init(g);

    printf("%20s,%10d,%10d,%20lld,%20lld,%20lld,%10.6lf\n", argv[1] + path_name_offset(argv[1]), g->n, g->m, sa->n, sa->l_sum, sa->s, simulated_annealing_get_modularity_score(sa, g));

    simulated_annealing_run(sa, g);

    graph_free(g);
    simulated_annealing_free(sa);

    return 0;
}