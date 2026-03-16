COMPILER := gcc

COMPILER_FLAGS := -c -g -std=c17
LINKER_FLAGS := -lpthread -g

EXECUTABLE := p2p_server # Changed output binary name to "p2p_server"
SOURCES := %.c
OBJECTS := main.o server.o utils.o network.o

# Compile and link the binary
$(EXECUTABLE): $(OBJECTS)
	$(COMPILER) $^ -o $@ $(LINKER_FLAGS)


# Compile each source file into object files
%.o: %.c
	$(COMPILER) $< -o $@ $(COMPILER_FLAGS)

clean:
	-rm -rf $(OBJECTS) $(EXECUTABLE)

# Target for cleaning up object files and the binary
# Usage: make clean

