#ifndef __UTILS_H__
#define __UTILS_H__
#include <stdio.h>


// #include "config.h"


/*
 * ERROR Macro:
 * 
 * This macro is used for printing error messages to the standard error stream (stderr) 
 * and exiting the program with an exit status of 1. It accepts a variable number of arguments, 
 * similar to the printf function, allowing for formatted error messages. The macro is defined 
 * using the do-while(0) construct to ensure proper behavior when used in conditional statements.
 * 
 * Example usage:
 * ERROR("Failed to open file: %s\n", filename);
 * 
 * This will print an error message to stderr indicating the failure to open a file, with the 
 * filename included in the message, and terminate the program with an exit status of 1.
 */
#define ERROR(...) do { fprintf(stderr, __VA_ARGS__); exit(1); } while (0)

#define MAX_IDSIZE 128
#define MAX_NEIGHBOR 16
#define MAX_STRLEN 64

// define packet type
#define CONNECT 0
#define QUERY 1
#define RESPONSE 2

/* Sender Packet */
typedef struct packet {
  // Unique ID
  int ID; 
  
  // Descriptor: describes the type of socket
  unsigned char descriptor;

  // searching message string 
  char message[MAX_STRLEN];
  
  // hos ip (query or respond)
  char hostname[MAX_STRLEN];

  // Time To Live 
  unsigned char TTL;
  
  // port number
  int port;

} packet_t;


/* An ID data structure for querying ID history */
typedef struct IDlist {
  // an array for all IDs 
  int IDs[MAX_IDSIZE];

  // num of all IDs 
  int num;
} IDlist_t;


/* Neighbor data structure */
// neighbor structure
typedef struct neighbor {
  // neighbors hostname 
  char hostname[MAX_STRLEN];

  // the binary addr, load with inet_ntop
  unsigned long inaddr;
  
  // port number
  int port;
  // socket file
  int sockfd;

} neighbor_t;


/* Neighbors data structure */
typedef struct neighbors {
  // the num of neighbors
  int num_neighbors;
  // the array of neighbors
  neighbor_t neighbor_list[MAX_NEIGHBOR];

} neighbors_t;


/*
 * Query related functions
 */
// generate a random ID for each payload 
int generateIdentifier();

// generate sending packet according to params; returns ID
int generatePacket(packet_t *packet, char *filename, int type, int TTL);


// init IDlist
int initializeList(IDlist_t *IDlist);

// add to ID list
int addToDataList(IDlist_t *IDlist, int ID); 

// find in ID list
int findInList(IDlist_t *IDlist, int ID);

// print the list for debug purposes
void printList(IDlist_t *idList);


/*
 * Neighbor related functions
 */
// init neighbors
int initializeNeighbors(neighbors_t *neighbors);

// push in a new neighbor
int addNeighbor(neighbors_t *neighbors, unsigned long host_in_addr, int port);

// print neighbor information
void printNeighborData(neighbors_t *neighbors);

int findInDirectory(char *Dir, char *filename);

// flood message data to neighbors
int floodRequest(neighbors_t *neighbors, int portno, packet_t *packet, int size);

#endif
