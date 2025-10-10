#pragma once

#include <graph.h>
#include <force_layout.h>
#include <stdint.h>

typedef struct
{
    int height, width;
    uint32_t *Pixels;

    float zoom;
    float root_x, root_y;
} screen;

screen *screen_init(int height, int width);

void screen_free(screen *s);

void screen_draw_line(screen *s, int x0, int y0, int x1, int y1, uint32_t color);

void screen_draw_circle(screen *s, int xm, int ym, int r, uint32_t color);

void screen_draw_circle_filled(screen *s, int xm, int ym, int r, uint32_t draw_color, uint32_t fill_color);

void screen_render_frame(screen *s, graph *g, force_layout *fl, int draw_edges);