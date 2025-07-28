SHELL = /bin/bash

CC = gcc
CFLAGS = -std=gnu17 -O3 -g -march=native -I include -fopenmp

OBJ = graph.o

OBJ_VIS = $(OBJ) main_vis.o
OBJ_CONVERT = $(OBJ) main_convert.o
OBJ_EVAL = $(OBJ) main_eval.o

OBJ_VIS := $(addprefix bin/, $(OBJ_VIS))
OBJ_CONVERT := $(addprefix bin/, $(OBJ_CONVERT))
OBJ_EVAL := $(addprefix bin/, $(OBJ_EVAL))

DEP = $(OBJ_VIS) $(OBJ_CONVERT) $(OBJ_EVAL)
DEP := $(sort $(DEP))

vpath %.c src
vpath %.h include

all : VIS CONVERT EVAL

-include $(DEP:.o=.d)

VIS : $(OBJ_VIS)
	$(CC) $(CFLAGS) -o $@ $^ -lm -lGL -lglut -lGLU

CONVERT : $(OBJ_CONVERT)
	$(CC) $(CFLAGS) -o $@ $^

EVAL : $(OBJ_EVAL)
	$(CC) $(CFLAGS) -o $@ $^ -lm

bin/%.o : %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@

.PHONY : clean
clean :
	rm -f VIS CONVERT EVAL $(DEP) $(DEP:.o=.d)