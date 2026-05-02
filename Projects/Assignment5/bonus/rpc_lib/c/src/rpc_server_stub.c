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

struct Person {
    char *name;
    int32_t age;
    bool is_student;
};
extern int32_t add_impl(int32_t a, int32_t b);
extern char* greet_impl(const char *name);
extern bool is_positive_impl(float num);
extern void no_return_impl();
extern int32_t divide_impl(int32_t numerator, int32_t denominator, bool *error);
extern int32_t sum_array_impl(const int32_t *numbers, int size);
extern char* process_person_impl(const struct Person *person_data);
extern char** get_greetings_impl(char** names, int count);

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
static inline uint32_t read_u32(uint8_t **ptr) {
    uint32_t val;
    memcpy (&val, *ptr, 4);
    *ptr += 4;
    return ntohl (val);
}

uint8_t *process_json_request(rpc_server_t *server, uint8_t *request_payload) {
    uint8_t func_id = request_payload[0];
    uint8_t *args_ptr = request_payload + 1;
    // printf("\n[DEBUG] Server received func_id = %d\n", func_id);
    uint8_t status = 0; // 0=success, 1=error, 2=not found, 3=exec fail
    uint8_t *result_data = NULL;
    uint32_t result_len = 0;
    switch (func_id) 
    {
        case 1: // add(int, int) -> int
        {
            int32_t a = (int32_t)read_u32 (&args_ptr);
            int32_t b = (int32_t)read_u32 (&args_ptr);
            int32_t res = add_impl (a, b);
            res = htonl (res);
            result_len = 4;
            result_data = malloc (4);
            memcpy (result_data, &res, 4);
            break;
        }
        case 2:   // greet(str) -> str
        case 9:  // echo(str) -> str
            uint32_t str_len = read_u32 (&args_ptr);
            char *name = malloc (str_len + 1);
            memcpy (name, args_ptr, str_len);
            name[str_len] = '\0';
            args_ptr += str_len;
            char *res_str = NULL;
            if (func_id == 2) res_str = greet_impl(name);
            else
            {
                res_str = malloc (str_len + 1);
                memcpy (res_str, name, str_len + 1); 
            }
            free (name);
            if (!res_str) {status = 3; break;}
            result_len = strlen (res_str);
            result_data = malloc (result_len);
            memcpy (result_data, res_str, result_len);
            free (res_str);
            break;
        case 3: // is_positive(float) -> bool
        {
            union {uint32_t i; float f;} u;
            u.i = read_u32 (&args_ptr);
            bool res = is_positive_impl (u.f);
            result_len = 1;
            result_data = malloc (1);
            result_data[0] = res ? 1 : 0;
            break;
        }
        case 4: // no_return() -> void
        {
            no_return_impl ();
            result_len = 0;
            break;
        }
        case 5: // divide(int, int) -> int
        {
            int32_t num = (int32_t)read_u32 (&args_ptr);
            int32_t den = (int32_t)read_u32 (&args_ptr);
            bool err = false;
            int32_t res = divide_impl (num, den, &err);
            if (err)
            {
                status = 3;
                const char *msg = "Division by zero";
                result_len = strlen (msg);
                result_data = malloc (result_len);
                memcpy (result_data, msg, result_len);
            } 
            else
            {
                res = htonl (res);
                result_len = 4;
                result_data = malloc (4);
                memcpy (result_data, &res, 4);
            }
            break;
        }
        case 6: // sum_array(list[int]) -> int
        {
            uint32_t count = read_u32 (&args_ptr);
            int32_t *arr = malloc (count * sizeof (int32_t));
            for (uint32_t i = 0;i < count;++i) arr[i] = (int32_t)read_u32 (&args_ptr);
            int32_t res = sum_array_impl (arr, count);
            free (arr);
            res = htonl (res);
            result_len = 4;
            result_data = malloc (4);
            memcpy (result_data, &res, 4);
            break;
        }
        case 7: // process_person(dict) -> str
        {
            struct Person p;
            uint32_t name_len = read_u32 (&args_ptr);
            p.name = malloc (name_len + 1);
            memcpy (p.name, args_ptr, name_len);
            p.name[name_len] = '\0';
            args_ptr += name_len;
            p.age = (int32_t)read_u32 (&args_ptr);
            p.is_student = (*args_ptr != 0);
            args_ptr += 1;
            char *res_str = process_person_impl (&p);
            free (p.name);
            if (!res_str) {status = 3; break;}
            result_len = strlen (res_str);
            result_data = malloc (result_len);
            memcpy (result_data, res_str, result_len);
            free (res_str);
            break;
        }
        case 8: // get_greetings(list[str]) -> list[str]
        { 
            uint32_t count = read_u32 (&args_ptr);
            char **names = malloc (count * sizeof (char*));
            for (uint32_t i = 0; i < count; i++)
            {
                uint32_t n_len = read_u32 (&args_ptr);
                names[i] = malloc (n_len + 1);
                memcpy (names[i], args_ptr, n_len);
                names[i][n_len] = '\0';
                args_ptr += n_len;
            }
            char **greetings = get_greetings_impl (names, count);
            result_len = 4;
            for (uint32_t i = 0;i < count;++i) result_len += 4 + strlen (greetings[i]);
            result_data = malloc (result_len);
            uint8_t *out_ptr = result_data;
            uint32_t net_count = htonl (count);
            memcpy (out_ptr, &net_count, 4); out_ptr += 4;
            for (uint32_t i = 0;i < count;++i)
            {
                uint32_t slen = strlen (greetings[i]);
                uint32_t net_slen = htonl (slen);
                memcpy (out_ptr, &net_slen, 4); out_ptr += 4;
                memcpy (out_ptr, greetings[i], slen); out_ptr += slen;
                free (names[i]);
                free (greetings[i]);
            }
            free (names);
            free (greetings);
            break;
        }
        default:
        {
            status = 2;
            const char *msg = "Function not found";
            result_len = strlen (msg);
            result_data = (uint8_t*)strdup (msg);
            break;
        }
    }
    uint32_t total_payload_len = 1 + result_len;
    uint32_t net_len = htonl (total_payload_len);
    uint8_t *buffer = malloc (4 + total_payload_len);
    if (buffer)
    {
        memcpy (buffer, &net_len, 4);
        buffer[4] = status;
        if (result_len > 0 && result_data != NULL) memcpy (buffer + 5, result_data, result_len);
    }
    if (result_data) free (result_data);
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