# Makefile for the RPC Server Application (JSON Version)

# Compiler and flags
CC = gcc
# C17 is used
CFLAGS = -std=c17 -Wall -Wextra

# Include directories
INC_DIR = ../rpc_lib/c/include
INCLUDES = -I$(INC_DIR)

# Source directories
APP_SRCDIR = .
LIB_SRCDIR = ../rpc_lib/c/src

# Source files
# Include server app sources and the necessary library sources
APP_SOURCES = $(wildcard $(APP_SRCDIR)/*.c)
LIB_SOURCES = $(wildcard $(LIB_SRCDIR)/rpc_connection.c) $(wildcard $(LIB_SRCDIR)/rpc_server_stub.c) $(wildcard $(LIB_SRCDIR)/cJSON.c)

SOURCES = $(APP_SOURCES) $(LIB_SOURCES)
OBJS = $(SOURCES:.c=.o)

# Library flags
# Link with pthread
LDFLAGS = -lpthread

# Executable name
TARGET = server

# --- Rules ---

all: $(TARGET)

# Link the target executable
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Compile source files into object files
# This rule handles both app sources and library sources
%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)
	# Clean object files possibly generated in lib dir if using alternative rules
	# rm -f $(LIB_SRCDIR)/*.o

.PHONY: all clean
