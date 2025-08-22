#pragma once

#include <time.h>

static inline int compare(const void *a, const void *b)
{
    return (*(int *)a - *(int *)b);
}

static inline double get_wtime()
{
    struct timespec tp;
    clock_gettime(CLOCK_REALTIME, &tp);
    return (double)tp.tv_sec + ((double)tp.tv_nsec / 1e9);
}