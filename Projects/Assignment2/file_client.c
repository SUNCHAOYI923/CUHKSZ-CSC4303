// file_client.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return 1;
    }

    struct sockaddr_in serv_addr;
    int sock = 0;
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

    /* IMPLEMENTING SIMPLE FILE TRANSFER */

    // Variables you may need to declare:
    FILE *file;
    char *base_filename;

    /* TODO: Open file for reading in binary mode
    * Use fopen() with "rb" mode
    */
    file = fopen (argv[1], "rb");
    if (!file)
    {
        perror ("Error opening file");
        exit(EXIT_FAILURE);
    }

    /* TODO: Extract filename from path (argv[1])
    * Use strrchr() to find the last '/' in the path
    * Example: "../file1.zip" -> "file1.zip"
    * If no '/' found, use the entire path as filename
    * Store result in base_filename
    */
    base_filename = strrchr (argv[1], '/');
    if (base_filename == NULL) base_filename = argv[1];
    else ++base_filename;
    /* TODO: Send filename to server
    * Send the filename (padded to BUFFER_SIZE) so server knows what to name the file
    */
    strncpy (buffer, base_filename, BUFFER_SIZE);
    send (sock, buffer, BUFFER_SIZE, 0);
    // sleep (10);
    // You can add a small delay to avoid data mix-up

    /* TODO: Send file content
    * Read file in chunks of BUFFER_SIZE and send each chunk
    */
    size_t sz = 0;
    while ((sz = fread (buffer, 1, BUFFER_SIZE, file)) > 0) send (sock, buffer, sz, 0);

    printf("File '%s' uploaded successfully.\n", base_filename);
    shutdown (sock, SHUT_WR);
    /* TODO: Close file and socket */
    fclose (file);
    
    close (sock);
    return 0;
}