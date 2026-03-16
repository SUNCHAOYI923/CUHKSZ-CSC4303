#include <stdio.h>
#include <stdio.h>
#include <string.h>
#include <string.h>
#include <sys/types.h>
#include "network.h"
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include "pthread.h"


unsigned long getHostAddr(char *hostname){
  struct hostent *host_entry;
  struct in_addr **addr_list;
  unsigned long ip_inaddr;

  if ((host_entry = gethostbyname(hostname)) == NULL){
    return 0;
  }
  addr_list = (struct in_addr**)host_entry->h_addr_list;
  ip_inaddr = (*addr_list[0]).s_addr;

  return ip_inaddr;
}


char *getHostIp(unsigned long host_in_addr){
  struct in_addr in_addr;
  in_addr.s_addr = host_in_addr;

  return inet_ntoa(in_addr);
}


int createNewSock(){
  int sockfd = socket(AF_INET, SOCK_DGRAM, 0);

  return sockfd;
}


int bindSocket(int sockfd, int portno){

  struct sockaddr_in server_address;
  bzero((char *) &server_address, sizeof (server_address));
  server_address.sin_family = AF_INET;
  server_address.sin_addr.s_addr = htonl(INADDR_ANY);
  server_address.sin_port = htons(portno);

  if (bind(sockfd, (struct sockaddr *)&server_address, sizeof (server_address)) < 0){
    return -1;
  }
  return 0;
}


unsigned long recvFromSocket(int sockfd, void *buffer, int totalsize){
  int recved;
  int allrecved = 0;

  struct sockaddr_in remoteaddr;
  socklen_t addrlen = sizeof(remoteaddr);

  while (allrecved < totalsize){
    recved = recvfrom(sockfd, buffer + allrecved, totalsize - allrecved, 0, (struct sockaddr *)&remoteaddr, &addrlen);
    allrecved += recved;

    printf("Message received, size: %d\n", allrecved);
  }

  unsigned long bin_ip = remoteaddr.sin_addr.s_addr;

  return bin_ip;
}

// store the packet into the buffer and send it to the target address
int sendToSocket(unsigned long host_inaddr, int portno, void *buffer, int size){
  int sockfd;
  struct in_addr in_addr;
  struct hostent *host_entry;
  struct sockaddr_in servaddr;
  char *ip;

  in_addr.s_addr = host_inaddr;
  ip = inet_ntoa(in_addr);

  printf("[CONNECT] Destination IP: %s, Port: %d\n", ip, portno);

  if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0){
    return -1;
  }
  printf("[CONNECT] Socket created successfully\n");

  memset((char *)&servaddr, 0, sizeof(struct sockaddr_in));
  servaddr.sin_family = AF_INET;
  servaddr.sin_port = htons(portno);
  if ((host_entry = gethostbyname(ip)) == NULL){
    return -1;
  }
  memcpy((void *)&servaddr.sin_addr, host_entry->h_addr_list[0], host_entry->h_length);

  int totalsent = 0;
  while (totalsent < size){
    int sent = sendto(sockfd, (char *)buffer + totalsent, size - totalsent, 0, (struct sockaddr *)&servaddr, sizeof(servaddr));
    totalsent += sent;
  }

  close(sockfd);

  printf("[CONNECT] Packet sent size: %d\n", totalsent);

  return 0;
}
