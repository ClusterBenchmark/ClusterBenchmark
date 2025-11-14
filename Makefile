SHELL = /bin/bash

CC = gcc
CFLAGS = -std=gnu17 -O3 -march=native -I include -fopenmp

OBJ = graph.o

OBJ_VIS = $(OBJ) main_vis.o barnes_hut.o screen.o clustering.o
OBJ_EVAL = $(OBJ) main_eval.o
OBJ_CLUSTER = $(OBJ) main_cluster.o clustering.o simulated_annealing.o
OBJ_FEATURE = $(OBJ) main_feature.o

OBJ_VIS := $(addprefix bin/, $(OBJ_VIS))
OBJ_EVAL := $(addprefix bin/, $(OBJ_EVAL))
OBJ_CLUSTER := $(addprefix bin/, $(OBJ_CLUSTER))
OBJ_FEATURE := $(addprefix bin/, $(OBJ_FEATURE))

DEP = $(OBJ_VIS) $(OBJ_EVAL) $(OBJ_CLUSTER) $(OBJ_FEATURE)
DEP := $(sort $(DEP))

vpath %.c src
vpath %.h include

all : CLUSTER VIS FEATURE EVAL

-include $(DEP:.o=.d)

VIS : $(OBJ_VIS)
	$(CC) $(CFLAGS) -o $@ $^ `sdl2-config --cflags --libs` -lm

EVAL : $(OBJ_EVAL)
	$(CC) $(CFLAGS) -o $@ $^ -lm

CLUSTER : $(OBJ_CLUSTER)
	$(CC) $(CFLAGS) -o $@ $^ -lm

FEATURE : $(OBJ_FEATURE)
	$(CC) $(CFLAGS) -o $@ $^ -lm

test : EVAL
	./tests/run_eval_tests.sh

bin/%.o : %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@

.PHONY : clean
clean :
	rm -f VIS CONVERT EVAL CLUSTER LOUVAIN $(DEP) $(DEP:.o=.d)
