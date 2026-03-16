
#include <sys/types.h>
#include <dirent.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>
#include "network.h"
#include "utils.h"
#include "pthread.h"

extern int global_ttl;

int generateIdentifier(){
  srand(time(NULL));
  return rand();
}


int generatePacket(packet_t *dataPacket, char *filename, int type, int TTL){
  /* 
   * TODO: Generate a data packet corresponding to the input parameters
   * Use generateIdentifier function to generate a random ID
   */

  // Your code starts here
  dataPacket -> descriptor = type;
  dataPacket -> TTL = TTL;
  dataPacket -> ID = generateIdentifier ();
  if (filename != NULL) strncpy (dataPacket -> message, filename, sizeof (dataPacket -> message) - 1);
  // Your code ends here

  return dataPacket->ID;
}

int initializeList(IDlist_t *dataList){
  dataList->num = 0;
  return 0;
}

int addToDataList(IDlist_t *dataList, int identifier){
  /* 
   * TODO: check if the ID is already in the list; if not, add it to the list
   * Hint: you can use mutex to ensure thread safety
   */

  // Your code starts here
  if (!findInList (dataList, identifier)) dataList -> IDs[dataList -> num++] = identifier;
  // Your code ends here

  return dataList->num;
}

int findInList(IDlist_t *dataList, int identifier){
  /*
   * TODO: check if the ID is already in the list; if not, return 0
   */

  // Your code starts here
  for (int i = 0; i < dataList -> num; ++i)
    if (dataList -> IDs[i] == identifier) return 1;
  // Your code ends here

  return 0;
}

void printList(IDlist_t *idList) {
  printf("[DEBUG] Current ID list: [");
  for (int i = 0; i < idList->num; ++i) {
      printf("%d", idList->IDs[i]);
        if (i != idList->num - 1) {
          printf(", ");
      }
  }
  printf("]\n");
}

int initializeNeighbors(neighbors_t *neighborData){
  neighborData->num_neighbors = 0;
  memset(neighborData->neighbor_list, 0, sizeof(neighborData->neighbor_list));
  return 0;
}

int addNeighbor(neighbors_t *neighborData, unsigned long hostIPAddress, int port){
  int index = neighborData->num_neighbors;
  neighbor_t *newNeighbor = &(neighborData->neighbor_list[index]);

  if (neighborData->num_neighbors >= MAX_NEIGHBOR){
    ERROR("ERROR: Exceeds maximum neighbor number\n");
    return -1;
  }
  // TODO: Assign the IP Address and Port to the new neighbor
  newNeighbor -> inaddr = hostIPAddress; newNeighbor -> port = port;
  // TODO: update the number of neighbors
  ++neighborData -> num_neighbors;
  return index;
}

void printNeighborData(neighbors_t *neighborData) {
    printf("[NEIGHBOR] Current neighbors\n");
    printf("[NEIGHBOR] Number of neighbors: %d\n", neighborData->num_neighbors);
    printf("[NEIGHBOR] Neighbor list:\n");
    for (int i = 0; i < neighborData->num_neighbors; ++i) {
        printf("[NEIGHBOR] Neighbor %d: IP %s, Port %d\n", i + 1, 
               getHostIp(neighborData->neighbor_list[i].inaddr),
               neighborData->neighbor_list[i].port);
    }
}

int findInDirectory(char *directory, char *file){
  DIR *dp;
  struct dirent *directoryStruct;
  if ( (dp = opendir(directory)) == NULL ){
    return -1;
  }
  // loop through directory, search for the file
  while ( (directoryStruct = readdir(dp)) != NULL ){
    if ( strcmp(file, directoryStruct->d_name) == 0 ){
      closedir(dp);
      return 1;
    }
  }
  closedir(dp);
  return 0;
}

int floodRequest(neighbors_t *neighbors, int portno, packet_t *packet, int size){
  int num_neighbors = neighbors->num_neighbors;
    
  for (int i = 0; i < num_neighbors; ++i){
    // TODO: send packet to the neighbor
    // Hint: functions in network.c may be helpful
    if (neighbors -> neighbor_list[i].port == portno) continue;
    sendToSocket (neighbors -> neighbor_list[i].inaddr, neighbors -> neighbor_list[i].port, packet, size);
  }
  return 0;
}
