#ifndef __NETWORK_H__
#define __NETWORK_H__

#include <netdb.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>


// find hostname binary ip form from hostname
unsigned long getHostAddr(char *hostname);

// find hostname char readable form
char *getHostIp(unsigned long host_in_addr);

// create new udp socket
int createNewSock();

// bind server to portno
int bindSocket(int sockfd, int portno);

// recv from a socket, return bin ip addr
unsigned long recvFromSocket(int sockfd, void *buffer, int size);

// send to a socket
int sendToSocket(unsigned long host_inaddr, int portno, void *buffer, int size);


#endif
