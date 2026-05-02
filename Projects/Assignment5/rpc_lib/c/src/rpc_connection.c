#include "../include/rpc_connection.h"
#include <unistd.h> // For close(), read(), write()
#include <sys/socket.h> // For send(), recv()
#include <arpa/inet.h> // For ntohl()

#include <string.h> // For strerror
#include <errno.h>  // For errno
#include <stdio.h> // For error reporting
#include <stdlib.h> // For malloc, free

// Create a new connection object for the given socket file descriptor.
// The connection is considered open if the socket_fd is valid (non-negative).
connection_t *connection_create(int socket_fd) {
    connection_t *connection = malloc(sizeof(connection_t));
    connection->fd = socket_fd;
    connection->open = socket_fd >= 0;
    return connection;
}

// Destroy the connection object, ensuring that any open connection is properly closed first.
void connection_destroy(connection_t *connection) {
    if (connection->open) {
        connection_close(connection);
    }
}

// Close the connection if it is open.
// This will close the underlying socket and mark the connection as closed.
void connection_close(connection_t *connection) {
    if (connection->open) {
        while (close(connection->fd) == -1) {
            if (errno == EINTR) {
                continue; // Retry if interrupted by a signal
            }
            fprintf(stderr, "Error closing socket: %s\n", strerror(errno));
            break;
        }
        connection->fd = -1;
        connection->open = false;
    }
}

// --- Core I/O Operations ---

/**
 * TODO: Implement the connection_receive_data function
 * 
 * This function receives a specific number of bytes from the connection.
 * Key concepts to implement:
 * 1. Check if the connection is open
 * 2. Allocate a buffer of the requested size
 * 3. Receive exactly the requested number of bytes
 * 4. Handle partial receives and retry as needed
 * 5. Handle errors and connection closures
 * 6. Return received data as an array (malloc'd buffer) that the caller is responsible for freeing
 * 
 * @param connection Pointer to the connection object
 * @param num_bytes Number of bytes to receive
 * @return Pointer to a malloc'd buffer containing the received data, or NULL on failure
 */
uint8_t *connection_receive_data(connection_t *connection, size_t num_bytes) {
    // Your implementation here
    if (!connection->open) return NULL;
    uint8_t *buffer = malloc (num_bytes);
    if (buffer == NULL) return NULL;
    size_t tot = 0;
    while (tot < num_bytes)
    {
        ssize_t res = recv (connection->fd, buffer + tot, num_bytes - tot, 0);
        if (res < 0)
        {
            if (errno == EINTR) continue;
            free (buffer);
            connection_close (connection);
            return NULL;
        }
        else if (res == 0)
        {
            free (buffer);
            connection_close (connection);
            return NULL;
        }
        else tot += (size_t) res;
    }
    return buffer;
}


/**
 * TODO: Implement the connection_receive_length_prefix function
 * 
 * This function receives a 4-byte length prefix and converts it from network byte order.
 * Key concepts to implement:
 * 1. Receive exactly 4 bytes using receive_data
 * 2. Convert from network byte order (big-endian) to host byte order using ntohl
 * 3. Handle errors and connection closures
 * 
 * @param connection Pointer to the connection object
 * @return Pointer to a malloc'd uint32_t containing the length (converted from network byte order to host byte order), or NULL on failure
 */
uint32_t *connection_receive_length_prefix(connection_t *connection) {
    // Your implementation here
    uint8_t *raw_len = connection_receive_data (connection, 4);
    if (raw_len == NULL) return NULL;
    uint32_t net_len;
    memcpy (&net_len, raw_len, 4);
    free (raw_len);
    uint32_t *host_len = (uint32_t *)malloc (sizeof (uint32_t));
    if (host_len == NULL) return NULL;
    *host_len = ntohl (net_len);    
    return host_len;
}

/**
 * TODO: Implement the connection_send_data function
 * 
 * This function sends data over the connection.
 * Key concepts to implement:
 * 1. Check if the connection is open
 * 2. Send all bytes in the data array
 * 3. Handle partial sends and retry as needed
 * 4. Handle errors appropriately (including EINTR interruptions)
 * 5. Mark connection as closed and return NULL on failure
 * 
 * @param connection Pointer to the connection object
 * @param data Pointer to the data buffer to send
 * @param num_bytes Number of bytes to send from the data buffer
 * @return true on success, false on failure (e.g., if the connection is not open or if a send error occurs)
 */
bool connection_send_data(connection_t *connection, uint8_t *data, size_t num_bytes) {
    // Your implementation here
    if (!connection->open) return false;
    size_t tot = 0;
    while (tot < num_bytes)
    {
        ssize_t res = send (connection->fd, data + tot, num_bytes - tot, 0);
        if (res < 0)
        {
            if (errno == EINTR) continue;
            connection_close (connection);
            return false;
        }
        else if (res == 0)
        {
            connection_close (connection);
            return false;
        }
        tot += (size_t) res;
    }
    return true;
}