#include "../include/rpc_server_stub.h"
#include "../include/rpc_connection.h"
#include "../include/cJSON.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdint.h>

/**
 * TODO: Implement the process_json_request function
 * This function processes a JSON-encoded RPC request and produces a response.
 * Your implementation should:
 * 1. Parse the incoming JSON string using cJSON
 * 2. Validate the request format has "function" and "args" fields
 * 3. Extract the function name and arguments
 * 4. Look up the function in the registry
 * 5. Execute the function with the provided arguments
 * 6. Build a response JSON with the result
 * 7. Handle errors at each stage and create appropriate error responses
 * 8. Serialize the response JSON and add length prefix
 * 
 * @param server          Pointer to the RPC server instance containing the function registry
 * @param request_json_str Pointer to the raw request bytes (JSON string). It should be a null-terminated string.
 * @return                Pointer to malloc'd buffer containing length-prefixed JSON response, 
 *                        which is a 4 byte length prefix (network byte order) followed by the null-terminated JSON string,
 *                        or NULL on catastrophic failure. Caller must free() the result.
 */
uint8_t *process_json_request(rpc_server_t *server, uint8_t *request_json_str) {
    // Your implementation here
    cJSON *request_json = cJSON_Parse ((char *)request_json_str);
    cJSON *response_json = cJSON_CreateObject ();
    if (response_json == NULL)
    {
        cJSON_AddStringToObject (response_json, "status", "error");
        cJSON_AddStringToObject (response_json, "message", "Invalid request");
    }
    else
    {
        cJSON *func_name_obj = cJSON_GetObjectItemCaseSensitive (request_json, "function");
        cJSON *args_obj = cJSON_GetObjectItemCaseSensitive (request_json, "args");
        if (!cJSON_IsString (func_name_obj) || args_obj == NULL)
        {
            cJSON_AddStringToObject (response_json, "status", "error");
            cJSON_AddStringToObject (response_json, "message", "Missing 'function' or 'args' field");
        } 
        else
        {
            char *func_name = func_name_obj->valuestring;
            cJSON* (*handler)(cJSON*) = NULL;
            for (int i = 0;i < server->registry_size;++i)
            {
                if (strcmp (server->registry_name[i], func_name) == 0)
                {
                    handler = server->registry_handler[i];
                    break;
                }
            }
            if (handler == NULL)
            {
                cJSON_AddStringToObject (response_json, "status", "error");
                cJSON_AddStringToObject (response_json, "message", "Function not found");
            }
            else
            {
                cJSON *result = handler (args_obj);
                if (result == NULL)
                {
                    cJSON_AddStringToObject (response_json, "status", "error");
                    cJSON_AddStringToObject (response_json, "message", "Function execution failed");
                }
                else
                {
                    cJSON_AddStringToObject(response_json, "status", "success");
                    cJSON_AddItemToObject(response_json, "result", result);
                }
            }
        }
    }
    char *json_str = cJSON_PrintUnformatted (response_json);
    uint32_t str_len = strlen (json_str) + 1, net_len = htonl (str_len);
    uint8_t *buffer = malloc (4 + str_len);
    if (buffer)
    {
        memcpy (buffer, &net_len, 4);
        memcpy (buffer + 4, json_str, str_len);
    }
    cJSON_Delete (request_json); cJSON_Delete (response_json); free (json_str);
    return buffer;
}

/**
 * TODO: Implement the handle_client function
 * 
 * This function handles communication with a connected client.
 * Your implementation should:
 * 1. Enter a loop to process client requests while connection is open
 * 2. Read the length prefix and request payload
 * 3. Process the request using process_json_request
 * 4. Send the response back to the client
 * 5. Handle connection errors and processing errors appropriately
 * 6. Send error responses to the client when possible
 * 
 * @param server Pointer to the RPC server instance
 * @param fd     Socket file descriptor for the connected client
 * @return       true if client handled successfully, false if there was a critical error
 */
bool handle_client(rpc_server_t *server, int fd) {
    // Your implementation here
    connection_t *conn = connection_create (fd);
    if (!conn) return false;
    while (conn->open)
    {
        uint32_t *len_ptr = connection_receive_length_prefix (conn);
        if (!len_ptr) break;
        uint32_t payload_len = *len_ptr;
        free (len_ptr);
        uint8_t *request_payload = connection_receive_data (conn, payload_len);
        if (!request_payload) break;
        uint8_t *response = process_json_request (server, request_payload);
        if (response)
        {
            uint32_t net_len;
            memcpy (&net_len, response, 4);
            uint32_t total_len = ntohl (net_len) + 4;
            connection_send_data (conn, response, total_len);
            free (response);
        }
        free (request_payload);
    }
    connection_destroy (conn);
    return true;
}


/**
 * Helper function to set up a listening socket on the specified port.
 * This function creates a socket, binds it to the given port, and starts listening.
 * It returns the file descriptor of the listening socket, or -1 on failure.
 * 
 * @param port Port number to listen on
 * @return     File descriptor of the listening socket, or -1 on failure
 */
int setup_listening_socket(int port) {
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        fprintf(stderr, "socket() failed: %s\n", strerror(errno));
        return -1;
    }

    // Allow reusing the address (helpful for quick restarts)
    int optval = 1;
    if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval)) < 0) {
        close(sockfd);
        fprintf(stderr, "setsockopt(SO_REUSEADDR) failed: %s\n", strerror(errno));
        return -1;
    }

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY); // Listen on all interfaces
    server_addr.sin_port = htons(port);

    if (bind(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        close(sockfd);
        fprintf(stderr, "bind() failed: %s\n", strerror(errno));
        return -1;
    }

    // Start listening, allow a backlog of connections (e.g., 10)
    if (listen(sockfd, 10) < 0) {
        close(sockfd);
        fprintf(stderr, "listen() failed: %s\n", strerror(errno));
        return -1;
    }

    return sockfd;
}


/**
 * Helper function to create a new RPC server instance.
 * This function allocates and initializes a new rpc_server_t structure.
 * The server is initialized with the specified port and default values for other fields.
 * 
 * @param port Port number for the server to listen on
 * @return     Pointer to the newly created rpc_server_t instance, or NULL on failure
 */
rpc_server_t* rpc_server_create(int port) {
    rpc_server_t *server = malloc(sizeof(rpc_server_t));
    server->listen_fd = -1;
    server->port = port;
    server->running = false;
    server->registry_size = 0;
    return server;
}

/**
 * Helper function to destroy an RPC server instance.
 * This function ensures that the server is stopped and any open sockets are closed before freeing the server structure.
 * 
 * @param server Pointer to the rpc_server_t instance to destroy
 */
void rpc_server_destroy(rpc_server_t *server) {
    // Ensure the server is stopped and socket is closed before destroying
    if (server->running) {
        shutdown(server->listen_fd, SHUT_RDWR);
        close(server->listen_fd);
        server->running = false;
    }
}

/**
 * TODO: Implement the rpc_server_start function
 * 
 * This function starts the RPC server and listens for incoming connections.
 * Your implementation should:
 * 1. Check if server is already running
 * 2. Set up a listening socket using setup_listening_socket()
 * 3. Enter an accept loop to handle client connections
 * 4. For each connection, create a connection_t object and handle client requests
 * 5. Handle errors and allow for graceful shutdown (e.g., on SIGINT)
 * 6. Clean up resources when server is stopped
 * 
 * @param server Pointer to the RPC server instance
 */
void rpc_server_start(rpc_server_t *server) {
    // Your implementation here
    if (server->running) return;
    server->listen_fd = setup_listening_socket (server->port);
    if (server->listen_fd < 0) return;
    server->running = true;
    while (server->running)
    {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof (client_addr);
        int client_fd = accept (server->listen_fd, (struct sockaddr *)&client_addr, &client_len);
        if (client_fd < 0)
        {
            if (errno == EINTR) continue;
            break;
        }
        handle_client (server, client_fd);
    }
    close (server->listen_fd);
    server->running = false; server->listen_fd = -1;
}


/**
 * TODO: Implement the rpc_server_register_function function
 * 
 * This function allows clients to register functions that can be called remotely.
 * Your implementation should:
 * 1. Check if server is already running (should not register while running)
 * 2. Check if function with the same name already exists (print warning)
 * 3. Store the function name and handler in the server's registry
 * 4. Print confirmation message
 * 
 * @param server  Pointer to the RPC server instance
 * @param name    Name of the function to register (string)
 * @param handler Function pointer to the handler that takes a cJSON* argument and returns a
 *              cJSON* response. 
 * @return        true if registration is successful, false if server is running or registry is full
 */
bool rpc_server_register_function(rpc_server_t *server, char *name, cJSON* (*handler)(cJSON*)) {
    // Your implementation here
    if (server->running) return false;
    for (int i = 0;i < server->registry_size;++i)
    {
        if (strcmp (server->registry_name[i], name) == 0)
        {
            printf("Warning: Function %s already registered.\n", name);
            return false;
        }
    }
    if (server->registry_size >= MAX_REGISTRY_SIZE)
    {
        printf ("Registry full, cannot register function '%s'\n", name);
        return false;
    }
    size_t len = strlen (name) + 1;
    server->registry_name[server->registry_size] = malloc (len);
    memcpy(server->registry_name[server->registry_size], name, len);
    server->registry_handler[server->registry_size] = handler;
    // printf("[DEBUG-REG] Index: %d, Name: '%s', NamePtr: %p, ArrayBase: %p\n",
    //        server->registry_size, 
    //        server->registry_name[server->registry_size],
    //        (void*)server->registry_name[server->registry_size],
    //        (void*)server->registry_name);
    ++server->registry_size;
    printf("Registered function: %s\n", name);
    return true;
}