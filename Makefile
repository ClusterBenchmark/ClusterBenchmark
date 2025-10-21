SHELL = /bin/bash

CC = gcc
CFLAGS = -std=gnu17 -O3 -march=native -I include -fopenmp

OBJ = graph.o

OBJ_VIS = $(OBJ) main_vis.o barnes_hut.o screen.o clustering.o local_search.o difference_core.o
OBJ_CONVERT = $(OBJ) main_convert.o
OBJ_EVAL = $(OBJ) main_eval.o
OBJ_CLUSTER = $(OBJ) main_cluster.o clustering.o local_search.o difference_core.o
OBJ_LOUVAIN = $(OBJ) main_louvain.o clustering.o

OBJ_VIS := $(addprefix bin/, $(OBJ_VIS))
OBJ_CONVERT := $(addprefix bin/, $(OBJ_CONVERT))
OBJ_EVAL := $(addprefix bin/, $(OBJ_EVAL))
OBJ_CLUSTER := $(addprefix bin/, $(OBJ_CLUSTER))
OBJ_LOUVAIN := $(addprefix bin/, $(OBJ_LOUVAIN))

DEP = $(OBJ_VIS) $(OBJ_CONVERT) $(OBJ_EVAL) $(OBJ_CLUSTER) $(OBJ_LOUVAIN)
DEP := $(sort $(DEP))

vpath %.c src
vpath %.h include

all : VIS CONVERT EVAL CLUSTER LOUVAIN

-include $(DEP:.o=.d)

VIS : $(OBJ_VIS)
	$(CC) $(CFLAGS) -o $@ $^ `sdl2-config --cflags --libs` -lm

CONVERT : $(OBJ_CONVERT)
	$(CC) $(CFLAGS) -o $@ $^

EVAL : $(OBJ_EVAL)
	$(CC) $(CFLAGS) -o $@ $^ -lm

CLUSTER : $(OBJ_CLUSTER)
	$(CC) $(CFLAGS) -o $@ $^ -lm

LOUVAIN : $(OBJ_LOUVAIN)
	$(CC) $(CFLAGS) -o $@ $^ -lm

bin/%.o : %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@

.PHONY : clean
clean :
	rm -f VIS CONVERT EVAL CLUSTER LOUVAIN $(DEP) $(DEP:.o=.d)