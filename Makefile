SHELL = /bin/bash

CC = gcc
CFLAGS = -std=gnu17 -O3 -march=native -I include

OBJ = graph.o

OBJ_EVAL = $(OBJ) main_eval.o
OBJ_EVAL := $(addprefix bin/, $(OBJ_EVAL))

DEP = $(OBJ_EVAL) $(OBJ_CONVERT)
DEP := $(sort $(DEP))

vpath %.c src
vpath %.h include

all : EVAL

-include $(DEP:.o=.d)

EVAL : $(OBJ_EVAL)
	$(CC) $(CFLAGS) -o $@ $^ -lm

bin/%.o : %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@

.PHONY : clean
clean :
	rm -f EVAL $(DEP) $(DEP:.o=.d)
