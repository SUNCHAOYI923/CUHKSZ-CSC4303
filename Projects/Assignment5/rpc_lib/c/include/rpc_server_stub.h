#ifndef RPC_SERVER_STUB_H
#define RPC_SERVER_STUB_H

#include "cJSON.h"
#include "rpc_connection.h"
#include <stdbool.h>

#define MAX_REGISTRY_SIZE 256

typedef struct {
    int port;
    int listen_fd; // Listening socket file descriptor
    char *registry_name[MAX_REGISTRY_SIZE];
    cJSON* (*registry_handler[MAX_REGISTRY_SIZE])(cJSON*);
    int registry_size;
    bool running;
} rpc_server_t;

// Create server
rpc_server_t* rpc_server_create(int port);

// Destroy server
void rpc_server_destroy(rpc_server_t *server);

// Register a function handler
bool rpc_server_register_function(rpc_server_t *server, char *name, cJSON* (*handler)(cJSON*));

// Start server (blocking). Returns 0 on success, negative on error
void rpc_server_start(rpc_server_t *server);

#endif // RPC_SERVER_STUB_H