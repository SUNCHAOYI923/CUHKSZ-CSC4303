# CSC4303 Network Programming

## Reference

- https://book.systemsapproach.org/foundation.html

## Transport Layer

### Network Model

|Layer|Description|Example
|:--:|:--:|:--:|
|Application|Programs that use network service|HTTP, DNS, CDNs|
|Transport|Provides end-to-end data delivery|TCP, UDP|
|Network|Send packets over multiple networks|IP, NAT, BGP|
|Link|Send frames over one or more links|Ethernet, 802.11|
|Physical|Send bits using signals|wires, fiber, wireless|

#### Transport Layer

Key Concepts:

- **Socket** 
    
    An endpoint for network communication that allows an application to attach to a specific port on the local network interface, enabling data exchange with other applications across the network.

- **Port**

    A port is a 16-bit number appended to an IP address that identifies a specific application or service on a single computer.
    
|Feature|TCP|UDP|
|:--:|:--:|:--:|
|Mode|Connections|Datagrams|
|Reliability|No loss, no duplicates, in-order delivery|May lose, reorder, or duplicate packets|
|Data Size|Unlimited|Limited|
|Flow Control|Flow control matches sender to receiver|Send regardless of receiver state|
|Congestion Control|Congestion control matches sender to network|Send regardless of network state|
|Format|

