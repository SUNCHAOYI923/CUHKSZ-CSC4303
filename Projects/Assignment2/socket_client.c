// socket_client.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    struct sockaddr_in serv_addr;
    int sock = 0;
    char *hello = "Hello from client";
    char buffer[BUFFER_SIZE] = {0};

    /* TODO: socket()
    * Create a socket using socket(AF_INET, SOCK_STREAM, 0)
    * Store the result in 'sock' variable
    * Print an error message and exit if it fails
    */
    sock = socket (AF_INET, SOCK_STREAM, 0);
    if (sock < 0)
    {
        perror ("Socket failed!");
        exit (EXIT_FAILURE);
    }
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    /* TODO: inet_pton()
    * Convert the IP address "127.0.0.1" from text to binary form
    * Use inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr)
    * Print an error message and exit if conversion fails (returns <= 0)
    */
    if (inet_pton (AF_INET, "127.0.0.1", &serv_addr.sin_addr) <= 0)
    {
        perror ("The address is invalid!");
        exit (EXIT_FAILURE);
    }

    /* TODO: connect()
    * Connect to the server.
    */
    if (connect (sock, (struct sockaddr *) &serv_addr, sizeof (serv_addr)) < 0)
    {
        perror ("Connect failed!");
        exit (EXIT_FAILURE);
    }

    // Send data to the server
    send(sock, hello, strlen(hello), 0);
    printf("Hello message sent\n");


    /* TODO: read()
    * Read data from the server into buffer with size BUFFER_SIZE.
    */
    ssize_t bytes_read = read (sock, buffer, BUFFER_SIZE);
    printf("Message from server: %s\n", buffer);

    // Introduce a delay to keep the connection open
    sleep(2); // Waits for 2 seconds. You can adjust this value as needed.

    /* TODO: close()
    * Close the socket.
    */
    close (sock);

    return 0;
}