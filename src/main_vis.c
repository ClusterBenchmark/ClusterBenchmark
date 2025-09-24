#include "graph.h"
#include "force_layout.h"

#include <SDL2/SDL.h>
#include <stdint.h>

#define WIDTH 1920
#define HEIGHT 900

void draw_line(int x0, int y0, int x1, int y1, uint32_t color, uint32_t *pixels)
{
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;

    while (1)
    {
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

void draw_circle(int xm, int ym, int r, uint32_t color, uint32_t *pixels)
{
    int x = -r, y = 0, err = 2 - 2 * r; /* bottom left to top right */
    do
    {
        pixels[(ym + y) * WIDTH + (xm - x)] = color; /* I. Quadrant +x +y */
        pixels[(ym - x) * WIDTH + (xm - y)] = color; /* II. Quadrant -x +y */
        pixels[(ym - y) * WIDTH + (xm + x)] = color; /* III. Quadrant -x -y */
        pixels[(ym + x) * WIDTH + (xm + y)] = color; /* IV. Quadrant +x -y */

        r = err;
        if (r <= y) /* e_xy+e_y < 0 */
        {
            err += ++y * 2 + 1;
        }

        if (r > x || err > y) /* e_xy+e_x > 0 or no 2nd y-step */
        {
            err += ++x * 2 + 1; /* -> x-step now */
        }

    } while (x < 0);
}

int main(int argc, char **argv)
{
    SDL_Init(SDL_INIT_VIDEO);
    SDL_Window *win = SDL_CreateWindow("Graph Vis",
                                       SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, WIDTH, HEIGHT, 0);
    SDL_Renderer *ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture *tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_RGB888,
                                         SDL_TEXTUREACCESS_STREAMING, WIDTH, HEIGHT);

    uint32_t *pixels = malloc(sizeof(uint32_t) * WIDTH * HEIGHT * 4);

    int running = 1;
    SDL_Event e;

    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);
    graph_default_weights(g);
    for (int u = 0; u < g->n; u++)
        g->VW[u] = 1;

    printf("%lld %lld\n", g->n, g->m);

    force_layout *fl = force_layout_init(g);

    uint32_t color = 0;

    while (running)
    {
        while (SDL_PollEvent(&e))
        {
            if (e.type == SDL_QUIT)
                running = 0;
        }

        force_layout_step(fl, g);

        memset(pixels, 0xff, sizeof(uint32_t) * WIDTH * HEIGHT);

        for (int i = 0; i < INNER_WIDTH; i++)
        {
            draw_line(i * CELL_WIDTH, 0, i * CELL_WIDTH, HEIGHT, color, pixels);
        }
        for (int i = 0; i < INNER_WIDTH; i++)
        {
            draw_line(0, i * CELL_WIDTH, WIDTH, i * CELL_WIDTH, color, pixels);
        }

#pragma omp parallel for
        for (int u = 0; u < g->n; u++)
        {
            int x = fl->X[u], y = fl->Y[u];

            if (x - 3 < 0 || x + 3 >= WIDTH || y - 3 < 0 || y + 3 >= HEIGHT)
                continue;

            draw_circle(x, y, 3, 0, pixels);

            for (int i = g->V[u]; i < g->V[u + 1]; i++)
            {
                int v = g->E[i];

                int x_v = fl->X[v], y_v = fl->Y[v];

                if (x_v < 0 || x_v >= WIDTH || y_v < 0 || y_v >= HEIGHT)
                    continue;

                if (u < v)
                    draw_line(x, y, x_v, y_v, 0, pixels);
            }
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
