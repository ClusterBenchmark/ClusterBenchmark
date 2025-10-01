#pragma once

#include <time.h>
#include <stdlib.h>

static inline int util_compare(const void *a, const void *b)
{
    return *(int *)a - *(int *)b;
}

static inline int util_compare_r(const void *a, const void *b, void *c)
{
    int *ID = (int *)c;
    return ID[*(int *)a] - ID[*(int *)b];
}

static inline void util_swap(int *a, int *b)
{
    int t = *a;
    *a = *b;
    *b = t;
}

static inline void util_swap_ll(long long *a, long long *b)
{
    long long t = *a;
    *a = *b;
    *b = t;
}

static inline void util_swap_p(int **a, int **b)
{
    int *t = *a;
    *a = *b;
    *b = t;
}

static inline double util_get_wtime()
{
    struct timespec tp;
    clock_gettime(CLOCK_REALTIME, &tp);
    return (double)tp.tv_sec + ((double)tp.tv_nsec / 1e9);
}

static inline int util_path_name_offset(char *path)
{
    int offset = 0;
    for (int i = 0; path[i] != '\0'; i++)
    {
        if (path[i] == '/')
            offset = i + 1;
    }
    return offset;
}

static inline void util_shuffle(int *list, int n, unsigned int *seed)
{
    for (int i = 0; i < n - 1; i++)
    {
        int j = i + (rand_r(seed) % (n - i));
        int t = list[j];
        list[j] = list[i];
        list[i] = t;
    }
}

static inline void util_parse_id(char *Data, size_t *p, long long *v)
{
    while ((Data[*p] < '0' || Data[*p] > '9') && Data[*p] != '\n')
        (*p)++;

    *v = 0;
    while (Data[*p] >= '0' && Data[*p] <= '9')
        *v = (*v) * 10 + Data[(*p)++] - '0';
}

static inline void util_skip_line(char *Data, size_t *p)
{
    while (Data[*p] != '\n')
        (*p)++;
    (*p)++;
}

static inline int lower_bound(const int *A, int n, int x)
{
    const int *s = A;
    while (n > 1)
    {
        int h = n / 2;
        s += (s[h - 1] < x) * h;
        n -= h;
    }
    s += (n == 1 && s[0] < x);
    return s - A;
}