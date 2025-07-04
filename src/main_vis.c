#include <GL/glut.h>
#include <stdlib.h>
#include <omp.h>
#include <math.h>

#include "graph.h"

#define STEP_TIME 0.02

unsigned int W, H;
unsigned char *image;

double time_ref;

graph *g;

float *X, *Y;

float center_x, center_y;
float zoom;

void display()
{
    glClearColor(1, 1, 1, 1);
    glClear(GL_COLOR_BUFFER_BIT);

    for (int i = 0; i < W * H * 3; i++)
        image[i] = (unsigned char)255;

    float w = (float)W / zoom, h = (float)H / zoom;
    float win_x = center_x - (w / 2.0f), win_y = center_y - (h / 2.0f);
    for (int u = 0; u < g->n; u++)
    {
        float x = X[u], y = Y[u];

        x = (x - win_x) * zoom;
        y = (y - win_y) * zoom;

        if (x < 0.0f || x >= W || y < 0.0f || y >= H)
            continue;

        image[W * 3 * (int)y + (int)x * 3 + 0] = 0;
        image[W * 3 * (int)y + (int)x * 3 + 1] = 0;
        image[W * 3 * (int)y + (int)x * 3 + 2] = 0;
    }

    glRasterPos2f(-1.0f, -1.0f);
    glDrawPixels(W, H, GL_RGB, GL_UNSIGNED_BYTE, image);

    glutSwapBuffers();
}

void idle()
{
    glutPostRedisplay();
}

int mx, my;

void mouse(int button, int state, int x, int y)
{
    float w = (float)W / zoom, h = (float)H / zoom;
    float win_x = center_x - (w / 2.0f), win_y = center_y - (h / 2.0f);

    if (button == 3)
    {
        zoom *= 1.05;
    }
    else if (button == 4)
    {
        zoom /= 1.05;
    }
    else if (button == 0 && state == 0)
    {
        y = glutGet(GLUT_WINDOW_HEIGHT) - y;

        x = ((float)x / zoom) + win_x;
        y = ((float)y / zoom) + win_y;

        mx = x, my = y;
        // printf("%d %d\n", x, y);
    }
}

void mouse_move(int x, int y)
{
    float w = (float)W / zoom, h = (float)H / zoom;
    float win_x = center_x - (w / 2.0f), win_y = center_y - (h / 2.0f);

    y = glutGet(GLUT_WINDOW_HEIGHT) - y;

    x = ((float)x / zoom) + win_x;
    y = ((float)y / zoom) + win_y;

    center_x += mx - x;
    center_y += my - y;

    // printf("%d %d\n", x, y);
}

int main(int argc, char **argv)
{
    FILE *file = fopen(argv[1], "r");
    g = graph_parse(file);
    fclose(file);

    printf("%d %d\n", g->n, g->V[g->n]);

    H = 1000, W = 1500;
    center_x = W / 2, center_y = H / 2;
    zoom = 1.0;

    X = malloc(sizeof(float) * g->n);
    Y = malloc(sizeof(float) * g->n);

    for (int u = 0; u < g->n; u++)
    {
        X[u] = rand() % W;
        Y[u] = rand() % H;
    }

    image = malloc(sizeof(unsigned char) * H * W * 3);

    time_ref = omp_get_wtime();

    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE);
    glutInitWindowSize(W, H);
    glutCreateWindow("Graph");
    glutDisplayFunc(display);
    glutIdleFunc(idle);
    glutMouseFunc(mouse);
    glutMotionFunc(mouse_move);
    glEnable(GL_BLEND);
    glEnable(GL_LINE_SMOOTH);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    // glutFullScreen();
    glutMainLoop();

    graph_free(g);
    free(image);

    return 0;
}