# Makefile for temperature reader
CC=gcc
CFLAGS=-Wall

all: ac-ctrl ac-learn

ac-ctrl: main.c
	$(CC) $(CFLAGS) main.c -o $@

ac-learn: main.c
	$(CC) $(CFLAGS) main.c -o $@

clean:
	rm ac-ctrl
	rm ac-learn
