SHELL = /bin/bash

CC = gcc
CFLAGS = -std=gnu17 -O3 -g -march=native -I include -fopenmp

OBJ = graph.o

OBJ_VIS = $(OBJ) main_vis.o

OBJ_VIS := $(addprefix bin/, $(OBJ_VIS))

DEP = $(OBJ_VIS)
DEP := $(sort $(DEP))

vpath %.c src
vpath %.h include

all : VIS

-include $(DEP:.o=.d)

VIS : $(OBJ_VIS)
	$(CC) $(CFLAGS) -o $@ $^ -lm -lGL -lglut -lGLU

bin/%.o : %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@

.PHONY : clean
clean :
	rm -f VIS $(DEP) $(DEP:.o=.d)