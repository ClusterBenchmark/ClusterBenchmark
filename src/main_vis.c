#include "graph.h"
// #include "force_layout.h"
#include "barnes_hut.h"
#include "screen.h"
#include "clustering.h"
#include "difference_core.h"

#include <SDL2/SDL.h>
#include <stdint.h>
#include <omp.h>

#define WIDTH 1500
#define HEIGHT 900

int main(int argc, char **argv)
{
    SDL_Init(SDL_INIT_VIDEO);
    SDL_Window *win = SDL_CreateWindow("Graph Vis",
                                       SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, WIDTH, HEIGHT, 0);
    SDL_Renderer *ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture *tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_RGB888,
                                         SDL_TEXTUREACCESS_STREAMING, WIDTH, HEIGHT);

    int running = 1;
    SDL_Event e;

    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);
    for (int u = 0; u < g->n; u++)
        g->VW[u] = 1;

    printf("%lld %lld\n", g->n, g->m);

    // d_core *dc = d_core_init(g, 4, 0);
    // d_core_run(dc, g, 60.0, 1);
    // clustering *c = d_core_get_best_clustering(dc);

    // graph *gc = graph_copy(g);
    // int *A = malloc(sizeof(int) * g->m);
    // for (int u = 0; u < g->n; u++)
    // {
    //     for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    //     {
    //         int v = g->E[i];
    //         A[i] = c->Cluster[u] == c->Cluster[v];
    //     }
    // }

    // int *FM = malloc(sizeof(int) * g->n);
    // graph_contract(g, gc, A, FM);
    // graph_sort_edges(gc);

    // g = gc;
    // for (int u = 0; u < g->n; u++)
    //     g->VW[u] = 1;

    // f = fopen("test.graph", "w");

    // fprintf(f, "%lld %lld 10\n", g->n, (g->m - 1) / 2);

    // for (int u = 0; u < g->n; u++)
    // {
    //     fprintf(f, "%lld ", g->VW[u]);
    //     for (long long i = g->V[u]; i < g->V[u + 1]; i++)
    //     {
    //         int v = g->E[i];
    //         if (v == u)
    //             continue;
    //         fprintf(f, "%d ", v + 1);
    //     }
    //     fprintf(f, "\n");
    // }
    // fclose(f);

    screen *s = screen_init(HEIGHT, WIDTH);
    barnes_hut *bh = barnes_hut_init(g);
    // force_layout *fl = force_layout_init(g);

    int mbd = 0;
    int draw_edges = 0;

    while (running)
    {
        while (SDL_PollEvent(&e))
        {
            if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == 1)
            {
                mbd = 1;
            }
            else if (e.type == SDL_MOUSEBUTTONUP && e.button.button == 1)
            {
                mbd = 0;
            }
            else if (e.type == SDL_MOUSEMOTION && mbd)
            {
                s->root_x += (float)e.motion.xrel / s->zoom;
                s->root_y += (float)e.motion.yrel / s->zoom;
            }
            else if (e.type == SDL_MOUSEWHEEL)
            {
                if (e.wheel.y > 0 && s->zoom < 10.0f)
                    s->zoom *= 1.1;
                else if (e.wheel.y < 0 && s->zoom > 0.01f)
                    s->zoom *= 0.9;
            }
            else if (e.type == SDL_KEYDOWN && e.key.keysym.sym == SDLK_e)
            {
                draw_edges = !draw_edges;
            }
            else if (e.type == SDL_KEYDOWN && e.key.keysym.sym == SDLK_q)
            {
                running = 0;
            }
            else if (e.type == SDL_QUIT)
            {
                running = 0;
            }
        }

        double t0 = omp_get_wtime();
        barnes_hut_step(bh, g);
        // force_layout_step(fl, g);
        double t1 = omp_get_wtime();
        screen_render_frame(s, g, bh->X, bh->Y, draw_edges);
        double t2 = omp_get_wtime();

        // s->Pixels[50 * WIDTH + 50] = 0xff;

        printf("\r%5.3lf %5.3lf", t1 - t0, t2 - t1);
        fflush(stdout);

        SDL_UpdateTexture(tex, NULL, s->Pixels, WIDTH * sizeof(uint32_t));
        SDL_RenderClear(ren);
        SDL_RenderCopy(ren, tex, NULL, NULL);
        SDL_RenderPresent(ren);
    }

    printf("\n");

    graph_free(g);
    barnes_hut_free(bh);
    // force_layout_free(fl);
    screen_free(s);

    SDL_DestroyTexture(tex);
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();
}
