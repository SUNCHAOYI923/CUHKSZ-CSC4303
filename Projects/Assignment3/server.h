#ifndef __SERVER_H__
#define __SERVER_H__

#include <sys/types.h>
#include "utils.h"
#include <unistd.h>


typedef struct serverArg {

  IDlist_t *idList;

  int port;

  char *directory;

  neighbors_t *neighbors;

  pthread_mutex_t *lock;

} serverArg_t;


// server thread function
void *server(void *arg);


// server handles CONNECT packet
int serverHandleConnect(neighbors_t *neighbors,
                          packet_t *packet,
                          pthread_mutex_t *lock);

// server handles Query packet
int serverQuery(serverArg_t *args, packet_t *packet);

// server handles RESPONSE packet
int serverHandleResponse(packet_t *packet);


#endif
