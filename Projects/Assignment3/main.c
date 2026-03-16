#include <pthread.h>
#include "utils.h"
#include "server.h"
#include "network.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>


int main(int argc, char **argv) {
    // Read in port number, TTL, directory, and neighbors from arguments
    int portNumber, neighborPortNumber; // host port number
    int ttl; // host ttl
    char directory[128]; // host directory

    neighbors_t neighbors;
    pthread_mutex_t lock;

    if (argc < 4) {
        ERROR("ERROR: Insufficient arguments provided. Usage: ./p2p_server [PORT_NUM] [TTL] [DIR] [NEIGHBOR_HOST, ...]\n");
    }

    if (argc >= 4) {
        // Parse arguments
        portNumber = atoi(argv[1]);
        ttl = atoi(argv[2]);
        strcpy(directory, argv[3]);

        // Initialize neighbors
        initializeNeighbors(&neighbors);
        int i;
        for (i = 4; i < argc - 1; i += 2) {  // Increment by 2 to process both IP and port at the same time
            unsigned long hostIpAddress = getHostAddr(argv[i]);
            printf("[NEIGHBOR] HostIPaddr: %lu\n", hostIpAddress);
            neighborPortNumber = atoi(argv[i+1]);
            if (hostIpAddress < 0) {
                ERROR("ERROR: Could not find host\n");
            }
            // TODO: Save to neighbor data structure
            addNeighbor (&neighbors, hostIpAddress, neighborPortNumber);
            // print neighbor information
            printNeighborData(&neighbors);
            printf("[NEIGHBOR] Sent connection request to neighbor with address %s:%d \n", argv[i], portNumber);
        }
    }

    IDlist_t idList;
    serverArg_t serverArg;

    // Initialize ID list
    initializeList(&idList);

    /*
     * TODO: Send CONNECT packet to all neighbors
     */

    // Your code starts here
    packet_t pac;
    memset (&pac, 0, sizeof (packet_t));
    pac.descriptor = CONNECT; pac.port = portNumber; strcpy (pac.hostname, "127.0.0.1");
    for (int i = 0; i < neighbors.num_neighbors; ++i) sendToSocket (neighbors.neighbor_list[i].inaddr, neighbors.neighbor_list[i].port, &pac, sizeof (packet_t));
    // Your code ends here

    // Add values to server arguments
    serverArg.idList = &idList;
    serverArg.port = portNumber;
    serverArg.directory = directory;
    serverArg.lock = &lock;
    serverArg.neighbors = &neighbors;

    // TODO: create a thread to handle server operations
    pthread_mutex_init (&lock, NULL);
    pthread_t tid;
    pthread_create (&tid, NULL, server, (void *)&serverArg);
    pthread_detach (tid);
    // Main thread while loop: host sender
    while (1) {
        // Read input from user
        char input[MAX_STRLEN];

        // Input filename for search
        printf("[FILE] Enter the File Name for Search: \n");
        fgets(input, MAX_STRLEN, stdin);
        int len = strlen(input);
        if (input[0] != '\0' && input[len - 1] == '\n') {
            input[len - 1] = '\0';
        }
      
        // First search local server directory
        if (findInDirectory(directory, input) == 1) {
            printf("[FILE] Found file '%s' in local directory \n", input);
            continue;
        }
        
        /*
         * TODO: flooding
         * Hint: Ensure thread safety by using a mutex
         */
        
        // Your code starts here
        packet_t query;
        memset (&query, 0, sizeof (packet_t));
        int qid = generatePacket (&query, input, QUERY, ttl);
        query.port = portNumber; strcpy (query.hostname, "127.0.0.1");  
        pthread_mutex_lock (&lock);
        addToDataList (&idList, qid);
        pthread_mutex_unlock (&lock);

        pthread_mutex_lock (&lock);
        floodRequest (&neighbors, portNumber, &query, sizeof (packet_t));
        pthread_mutex_unlock (&lock);
        // Your code ends here
    }

    return 0;
}
