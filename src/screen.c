#include "screen.h"

#include <stdlib.h>
#include <string.h>

screen *screen_init(int height, int width)
{
    screen *s = malloc(sizeof(screen));

    s->height = height;
    s->width = width;

    s->Pixels = malloc(sizeof(uint32_t) * height * width);

    for (int i = 0; i < height * width; i++)
        s->Pixels[i] = 0;

    s->zoom = 0.5f;
    s->root_x = 0;
    s->root_y = 0;

    return s;
}

void screen_free(screen *s)
{
    free(s->Pixels);

    free(s);
}

void screen_draw_line(screen *s, int x0, int y0, int x1, int y1, uint32_t color)
{
    if (x0 < 0 || x0 >= s->width || y0 < 0 || y0 >= s->height ||
        x1 < 0 || x1 >= s->width || y1 < 0 || y1 >= s->height)
        return;

    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;

    while (1)
    {
        s->Pixels[y0 * s->width + x0] = color;

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

void screen_draw_circle(screen *s, int xm, int ym, int r, uint32_t color)
{
    if (xm - r < 0 || xm + r >= s->width || ym - r < 0 || ym + r >= s->height)
        return;

    int x = -r, y = 0, err = 2 - 2 * r; /* bottom left to top right */
    do
    {
        s->Pixels[(ym + y) * s->width + (xm - x)] = color; /* I. Quadrant +x +y */
        s->Pixels[(ym - x) * s->width + (xm - y)] = color; /* II. Quadrant -x +y */
        s->Pixels[(ym - y) * s->width + (xm + x)] = color; /* III. Quadrant -x -y */
        s->Pixels[(ym + x) * s->width + (xm + y)] = color; /* IV. Quadrant +x -y */

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

void screen_draw_circle_filled(screen *s, int xm, int ym, int r, uint32_t draw_color, uint32_t fill_color)
{
}

void screen_render_frame(screen *s, graph *g, force_layout *fl, int draw_edges)
{
#pragma omp parallel
    {
#pragma omp for
        for (int i = 0; i < s->height * s->width; i++)
        {
            s->Pixels[i] = 0xffffff;
        }

        // for (int i = 0; i < INNER_SIZE; i++)
        // {
        //     int vx = ((float)(i * INNER_WIDTH) + s->root_x) * s->zoom;
        //     screen_draw_line(s, vx, 0, vx, s->height - 1, 0xff0000);
        // }
        // for (int i = 0; i < INNER_SIZE; i++)
        // {
        //     int vy = ((float)(i * INNER_WIDTH) + s->root_y) * s->zoom;
        //     screen_draw_line(s, 0, vy, s->width - 1, vy, 0xff0000);
        // }

        // for (int i = 0; i < OUTER_SIZE; i++)
        // {
        //     int vx = ((float)(i * OUTER_WIDTH) + s->root_x) * s->zoom;
        //     screen_draw_line(s, vx, 0, vx, s->height - 1, 0x00ff00);
        // }
        // for (int i = 0; i < OUTER_SIZE; i++)
        // {
        //     int vy = ((float)(i * OUTER_WIDTH) + s->root_y) * s->zoom;
        //     screen_draw_line(s, 0, vy, s->width - 1, vy, 0x00ff00);
        // }

        // screen_draw_line(s, 100, 0, 100, s->height - 1, 0x00);

        // for (int i = 0; i < OUTER_SIZE; i++)
        // {
        //     draw_line(i * OUTER_WIDTH, 0, i * OUTER_SIZE, HEIGHT, color, pixels);
        // }
        // for (int i = 0; i < INNER_WIDTH; i++)
        // {
        //     draw_line(0, i * CELL_WIDTH, WIDTH, i * CELL_WIDTH, color, pixels);
        // }

#pragma omp for
        for (int u = 0; u < g->n; u++)
        {
            int ux = (fl->X[u] + s->root_x) * s->zoom, uy = (fl->Y[u] + s->root_y) * s->zoom;

            screen_draw_circle(s, ux, uy, s->zoom * 3.0f, 0x00);

            if (!draw_edges)
                continue;

            for (int i = g->V[u]; i < g->V[u + 1]; i++)
            {
                int v = g->E[i];

                int vx = (fl->X[v] + s->root_x) * s->zoom, vy = (fl->Y[v] + s->root_y) * s->zoom;

                if (u < v)
                    screen_draw_line(s, ux, uy, vx, vy, 0x00);
            }
        }
    }
}