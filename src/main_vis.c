#include "graph.h"
#include "force_layout.h"

#include <SDL2/SDL.h>
#include <stdint.h>

#define WIDTH 1920
#define HEIGHT 1080

void draw_line(int x0, int y0, int x1, int y1, uint32_t color, uint32_t *pixels)
{
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;
    while (1)
    {
        // if (pixels[y0 * WIDTH + x0] == color)
        //     break;

        pixels[y0 * WIDTH + x0] = color;
        if (x0 == x1 && y0 == y1)
            break;
        e2 = 2 * err;
        if (e2 >= dy)
        {
            err += dy;
            x0 += sx;
        }
        if (e2 <= dx)
        {
            err += dx;
            y0 += sy;
        }
    }
}

int main(int argc, char **argv)
{
    SDL_Init(SDL_INIT_VIDEO);
    SDL_Window *win = SDL_CreateWindow("Graph Vis",
                                       SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, WIDTH, HEIGHT, 0);
    SDL_Renderer *ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture *tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_RGB888,
                                         SDL_TEXTUREACCESS_STREAMING, WIDTH, HEIGHT);

    uint32_t *pixels = malloc(sizeof(uint32_t) * WIDTH * HEIGHT);

    int running = 1;
    SDL_Event e;

    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);

    force_layout *fl = force_layout_init(g, HEIGHT, WIDTH);

    // force_layout_step(fl, g, 10.0, 1000000000);

    uint32_t color = 0;
    while (running)
    {
        while (SDL_PollEvent(&e))
        {
            if (e.type == SDL_QUIT)
                running = 0;
        }

        force_layout_step(fl, g, 0.01, 10000000);

        memset(pixels, 0xff, sizeof(uint32_t) * WIDTH * HEIGHT);

        for (int u = 0; u < g->n; u++)
        {
            for (int i = g->V[u]; i < g->V[u + 1]; i++)
            {
                int v = g->E[i];

                if (u > v)
                    draw_line(fl->X[u], fl->Y[u], fl->X[v], fl->Y[v], 0x000000, pixels);
            }
        }

        for (int u = 0; u < g->n; u++)
        {
            pixels[(int)(fl->Y[u]) * WIDTH + (int)(fl->X[u])] = 0x0000ff;
        }

        SDL_UpdateTexture(tex, NULL, pixels, WIDTH * sizeof(uint32_t));
        SDL_RenderClear(ren);
        SDL_RenderCopy(ren, tex, NULL, NULL);
        SDL_RenderPresent(ren);
    }

    SDL_DestroyTexture(tex);
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();
}
