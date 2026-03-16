#include <pthread.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include "network.h"
#include "utils.h"
#include "server.h"
#include <stdio.h>
#include <dirent.h>

void *server(void *arg) {
  serverArg_t *_arg = (serverArg_t *)arg;
  IDlist_t *idList = _arg->idList;
  int portNum = _arg->port;
  char *directory = _arg->directory;
  neighbors_t *neighbors = _arg->neighbors;
  pthread_mutex_t *mutex = _arg->lock;

  int socketfd = createNewSock();
  packet_t packet;
  unsigned long clientIpAddress;

  if (bindSocket(socketfd, portNum) == -1){
    ERROR("Error: wrong port binding. \n");
  }
  printf("[CONNECT] Successfully bind with the port: %d\n", portNum);

  while (1) {
    // TODO: receive packet
    clientIpAddress = recvFromSocket (socketfd, &packet, sizeof (packet_t));
    unsigned char type = packet.descriptor;   

    char *packetType;
    switch(type) {
      case 0: packetType = "CONNECT"; break;
      case 1: packetType = "QUERY"; break;
      case 2: packetType = "RESPONSE"; break;
    }
    printf("[SERVER INFO] Received new packet: %s packet\n", packetType);

    if (type == CONNECT){
      // TODO: handle server connect
      serverHandleConnect (neighbors, &packet, mutex);
    }
    else if (type == QUERY){
      // TODO: handle server query
      serverQuery (_arg, &packet);
    }
    else if (type == RESPONSE){
      // TODO: handle server response
      serverHandleResponse (&packet);
    }
  }
}

int serverHandleConnect(neighbors_t *neighbors, packet_t *packet, pthread_mutex_t *mutex) {
  unsigned long hostIpAddress;
  int portNum;
  /*
   * TODO: update neighbor list
   * Hint: functions in utils.c and network.c may be helpful
   * Hint: use mutex to ensure thread safety
   */

  // Your code starts here
  hostIpAddress = getHostAddr (packet -> hostname);
  portNum = packet -> port;
  pthread_mutex_lock (mutex);
  addNeighbor (neighbors, hostIpAddress, portNum);
  pthread_mutex_unlock (mutex);
  printf("[NEIGHBOR] New neighbor connecting request. From address: %s:%d\n", 
    getHostIp(hostIpAddress), portNum);
  // Your code ends here

  printf("[NEIGHBOR] New neighbor connected!\n");
  return 0;
}

int serverQuery(serverArg_t *args, packet_t *packet) {
  /*
   * TODO: handle server query
   * Hint: always remember thread safety
   */

  
  // TODO: if found in ID list
  pthread_mutex_lock (args -> lock);
  if (findInList (args -> idList, packet -> ID))
  {
    pthread_mutex_unlock (args -> lock);
    printf("[DUPLICATE ID] Duplicate packet with ID %d detected. Ignoring and discarding.\n", packet->ID);
    return 0;
  }
  addToDataList (args -> idList, packet -> ID);
  pthread_mutex_unlock (args -> lock);

  // TODO: if file found in directory, return the msg back to query host
  if (findInDirectory (args -> directory, packet -> message) == 1)
  {
    printf("[RESPON] File %s found, responding to query.\n", packet->message);
    packet_t res;
    memset (&res, 0, sizeof (packet_t));
    res.descriptor = RESPONSE; res.port = args -> port;
    strcpy (res.message, packet -> message); strcpy (res.hostname, "127.0.0.1");
    sendToSocket (getHostAddr (packet -> hostname), packet -> port, &res, sizeof (packet_t));
    return 0;
  }
  
  // TODO: TTL check
  --packet -> TTL;
  if (packet -> TTL <= 0) 
  {
    printf("[TTL] Packet TTL expired, stopping forwarding.\n");
    return 0;
  }
  
  // TODO: else not found, flood to neighbors
  pthread_mutex_lock (args -> lock);
  for(int i = 0; i < args -> neighbors -> num_neighbors; ++i)
  {
    int nxt_port = args -> neighbors -> neighbor_list[i].port;
    if (nxt_port != packet -> port) printf("[INFO] File Not found, Forward to next neighbor: %d\n", nxt_port);
  }

  printf("[TTL] Forwarding packet with TTL=%d\n", packet->TTL);
  floodRequest (args -> neighbors, packet -> port, packet, sizeof (packet_t));
  pthread_mutex_unlock (args -> lock);
  return 0;
}

int serverHandleResponse(packet_t *packet) {
    printf("\n[FILE] File %s found on address %s, with port %d\n\n",
         packet->message, packet->hostname,
         packet->port);
  return 0;
}
