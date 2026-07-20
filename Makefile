SHELL = /bin/bash

CC = gcc
CFLAGS = -std=gnu17 -O3 -march=native -I include

OBJ = graph.o

OBJ_EVAL = $(OBJ) main_eval.o
OBJ_EVAL := $(addprefix bin/, $(OBJ_EVAL))

OBJ_CONVERT = $(OBJ) main_convert.o
OBJ_CONVERT := $(addprefix bin/, $(OBJ_CONVERT))

DEP = $(OBJ_EVAL) $(OBJ_CONVERT)
DEP := $(sort $(DEP))

vpath %.c src
vpath %.h include

all : EVAL CONVERT

-include $(DEP:.o=.d)

EVAL : $(OBJ_EVAL)
	$(CC) $(CFLAGS) -o $@ $^ -lm

CONVERT : $(OBJ_CONVERT)
	$(CC) $(CFLAGS) -o $@ $^ -lm

bin/%.o : %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@

.PHONY : clean
clean :
	rm -f EVAL CONVERT $(DEP) $(DEP:.o=.d)
