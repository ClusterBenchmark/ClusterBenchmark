SHELL = /bin/bash

CC = gcc
CFLAGS = -std=gnu17 -O3 -march=native -g -I include -fopenmp

OBJ = graph.o

OBJ_VIS = $(OBJ) main_vis.o
OBJ_CONVERT = $(OBJ) main_convert.o
OBJ_EVAL = $(OBJ) main_eval.o
OBJ_CLUSTER = $(OBJ) simulated_annealing.o local_search.o main_cluster.o

OBJ_VIS := $(addprefix bin/, $(OBJ_VIS))
OBJ_CONVERT := $(addprefix bin/, $(OBJ_CONVERT))
OBJ_EVAL := $(addprefix bin/, $(OBJ_EVAL))
OBJ_CLUSTER := $(addprefix bin/, $(OBJ_CLUSTER))

DEP = $(OBJ_VIS) $(OBJ_CONVERT) $(OBJ_EVAL) $(OBJ_CLUSTER)
DEP := $(sort $(DEP))

vpath %.c src
vpath %.h include

all : VIS CONVERT EVAL CLUSTER

-include $(DEP:.o=.d)

VIS : $(OBJ_VIS)
	$(CC) $(CFLAGS) -o $@ $^ `sdl2-config --cflags --libs`

CONVERT : $(OBJ_CONVERT)
	$(CC) $(CFLAGS) -o $@ $^

EVAL : $(OBJ_EVAL)
	$(CC) $(CFLAGS) -o $@ $^ -lm

CLUSTER : $(OBJ_CLUSTER)
	$(CC) $(CFLAGS) -o $@ $^ -lm

bin/%.o : %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@

.PHONY : clean
clean :
	rm -f VIS CONVERT EVAL CLUSTER $(DEP) $(DEP:.o=.d)