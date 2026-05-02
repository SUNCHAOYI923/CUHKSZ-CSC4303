#ifndef RPC_CONNECTION_H
#define RPC_CONNECTION_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

typedef struct {
    int fd; // Socket file descriptor
    bool open;
} connection_t;

// Create a new connection object for the given socket file descriptor. 
// The connection is considered open if the socket_fd is valid (non-negative).
connection_t *connection_create(int socket_fd);

// Close the connection if it is open. 
// This will close the underlying socket and mark the connection as closed.
void connection_close(connection_t *connection);

// Destroy the connection object, ensuring that any open connection is properly closed first.
void connection_destroy(connection_t *connection);

// Receive a specified number of bytes from the connection.
// Returns a pointer to a malloc'd buffer containing the received data, or NULL on failure.
uint8_t *connection_receive_data(connection_t *connection, size_t num_bytes);

// Send a specified number of bytes over the connection.
// Returns true on success, or false on failure (e.g., if the connection is not open or if a send error occurs).
bool connection_send_data(connection_t *connection, uint8_t *data, size_t num_bytes);

// Receive a 4-byte length prefix from the connection, which indicates the length of the subsequent data.
// Returns a pointer to a malloc'd uint32_t containing the length (converted from network byte order to host byte order), or NULL on failure.
uint32_t *connection_receive_length_prefix(connection_t *connection);

#endif