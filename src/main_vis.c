#include "graph.h"

#include <SDL2/SDL.h>
#include <stdint.h>

#define WIDTH 1920
#define HEIGHT 1080

uint32_t pixels[WIDTH * HEIGHT];

static inline void putpixel(int x, int y, uint32_t color)
{
    if ((unsigned)x < WIDTH && (unsigned)y < HEIGHT)
        pixels[y * WIDTH + x] = color;
}

void draw_line(int x0, int y0, int x1, int y1, uint32_t color)
{
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;
    while (1)
    {
        putpixel(x0, y0, color);
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

    int running = 1;
    SDL_Event e;

    FILE *f = fopen(argv[1], "r");
    graph *g = graph_parse(f);
    fclose(f);

    graph_sort_edges(g);

    int *X = malloc(g->n * sizeof(int)),
        *Y = malloc(g->n * sizeof(int));

    for (int i = 0; i < g->n; i++)
    {
        X[i] = rand() % WIDTH;
        Y[i] = rand() % HEIGHT;
    }

    uint32_t color = 0;
    while (running)
    {
        while (SDL_PollEvent(&e))
        {
            if (e.type == SDL_QUIT)
                running = 0;
        }

        // simulation step (replace with your own logic)
        color = 0;
        for (int i = 0; i < HEIGHT; i++)
        {
            for (int j = 0; j < WIDTH; j++)
            {
                pixels[i * WIDTH + j] = 0xffffff;
            }
        }

        for (int u = 0; u < g->n; u++)
        {
            pixels[Y[u] * WIDTH + X[u]] = 0;
        }

        // for (int i = 0; i < 1000; i++)
        // { // million points
        //   // int x = rand() % WIDTH;
        //   // int y = rand() % HEIGHT;
        //   // putpixel(x, y, color);
        // }

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
