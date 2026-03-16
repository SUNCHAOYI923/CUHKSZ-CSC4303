[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/f3fSWE9f)
# CSC4303 Assignment-3: Flooding and Peer-to-peer Search (10 points)

### Deadline: March 13th, 23:59 (UTC+8)

### Name: Chaoyi, Sun

### Student ID: 124090550

This is not a group assignment. **You are not allowed to copy or look at code from other students. You are also not allowed to use generative AI tools to complete your assignment.** However, you are welcome to discuss the assignments with other students without sharing code. 

Let's get started!

## Overview
This assignment outlines the implementation of a basic simulation of a peer-to-peer (P2P) file search protocol using flooding mechanism, akin to the Gnutella protocol. In this flooding-based protocol, when a peer searches for a file, it floods query messages to all its neighbors, who in turn flood to their neighbors, allowing the query to propagate through the P2P network until the file is found or the search expires.

## Basic Requirements
As for the whole project:
- It must be written in C on a Unix-like Operating System (like Linux or macOS).
- You should use `gcc` or `clang` supporting C17 standard as the compiler (you can use features up to C17).
- Make sure GNU Make is installed in your system.
- **If you are using Windows,** you can either use **WSL2**, MSYS2, or Cygwin to compile and run this assignment.
    - See [Microsoft WSL Installation Guide](https://learn.microsoft.com/en-us/windows/wsl/install) for details
    - ⚠️ **Recommended: Use WSL2.** MSYS2 and Cygwin are not tested and use them as your own risk.
- You may also use a virtual machine locally or on AWS EC2 as your development environment
- ⚠️ **Keep an eye on AWS Cost Billing if you choose EC2!**

We provide several helper function files for you: **`utils.c`**, **`utils.h`**, **`network.c`**, and **`network.h`**, with **`network.c`** offering UDP communication APIs. You may choose to use these provided functions. Make sure your implementation follows the command-line call examples (you will see the command-line call examples under **three-party example**).

Your responsibility is to implement the operational procedure in **`main.c`**, **`server.c`**, and **`utils.c`**, ensuring they meet the criteria for command-line call examples. You are required to fill in the TODOs in the three files. For existing functions, you are only allowed to write code in the TODOs and should not modify other parts. However, you can implement your own auxiliary functions outside if needed. Do not include other header files.

For **`main.c`**: **3 TODOs**

- Parse the command-line arguments, record neighbor information, and send CONNECT requests to all neighbors to establish connections.
- Handle server operations (you may consider using a mutex to safely share the neighbor structure between threads).
- Make sure the query ID List and Neighbor List data structures are maintained.

For **`server.c`**: **10 TODOs**

- Init a server that loops and receive packets.
- Read the packet and determine the packet type (there are three types: CONNECT, QUERY, and RESPONSE).
- If the packet is a CONNECT type, establish the connection between the server and the packet sender; add the packet sender as a neighbor.
- If the packet is a QUERY type:
    - Check if the query packet has a duplicated ID based on its ID.
    - Search the target directory for the queried file.
    - If the queried file is found, sends a response back to the server that initialized the query.
    - If file is not found and TTL (Time To Live) is greater than 0, flood the query to all neighbors except the sender.
    - The search fails silently if there are no search results from any reachable server, and the host may receive multiple responses if the query is flooded to multiple server. (you may consider sharing the query ID structure between threads for this purpose).
- If the packet is a RESPONSE type, print out the search response.

For **`utils.c`**: **6 TODOs**

- Implement the functions in **`utils.c`** to support the operations in **`main.c`** and **`server.c`**.


## Objectives

You must achieve three goals to ensure the protocol functions correctly:

1. **Basic Query Flooding**
    
    Confirm that a query packet is distributed to all neighboring servers.
    
    * Procedure:
        1. Launch multiple server instances on different terminals, each with a unique port and directory.
        2. Initiate a query request from one server.
        3. Make sure that all other servers receive the query packet.
    * Expected Outcome: Each server receives the query packet.
2. **Loop Avoidance**
    
    Ensure the system prevents endless looping of query packets in a network with loops.
    
    * Procedure:
        1. Set up a network with at least one loop.
        2. Issue a query request from a server within the loop.
        3. Monitor query packet flow to ensure no server receives the same packet more than once (you may maintain an ID list; each time a query is issued, it is identified as a unique ID).
    * Expected Outcome: Query packets do not loop indefinitely; servers receive the query only once.
3. **TTL Control**
    
    Verify that the Time-to-Live (TTL) mechanism restricts query packet propagation.
    
    * Procedure:
        1. Assign a low TTL value (e.g., 1) to query packets.
        2. Send a query from one server.
        3. Check that the query packet is not forwarded beyond immediate neighbors as the TTL expires.
    * Expected Outcome: Query packets do not extend beyond their TTL scope, preventing excess network traffic and loop risks.

## Testing Environment Setup

The test environment consists of multiple directories, each representing a server with a unique file. Use multiple terminals to run the compiled "p2p_server" binary with necessary arguments to simulate the distributed network.

```
.
├── Makefile
├── dir1
│   ├── file1
│   └── file2
├── dir2
│   └── file3
├── dir3
│   └── file4
├── dir4
│   ├── file5
│   └── file6
├── dir5
│   └── file7
├── main.c
├── network.c
├── network.h
├── server.c
├── server.h
├── utils.c
└── utils.h
```

**Usage**:

```console
$ ./p2p_server [PORT_NUM] [TTL] [DIR] [NEIGHBOR_HOST, ...]  
```

### Three-Party Example
⚠️ The following are examples for three-party communications. You should strictly follow the output format in your implementation. However, the content of the output (for example, filename and directory name) should follow the exact layout. **YOU SHOULD NOT DIRECTLY COPY THE EXAMPLE OUTPUT AND HARD-CODE IT INTO YOUR CODE!**


***Test*: *Flooding query and TTL Control***

(Bob being a neighbor to Alice, Carol being a neighbor to Bob)

```bash
# Initialize Alice as the boostrap server
(terminal Alice) $ ./p2p_server 49151 1 dir1

# Bob being a neighbor connected to Alice
(terminal Bob)   $ ./p2p_server 49152 2 dir2 127.0.0.1 49151 

# Carol being a neighbor connected to Bob
(terminal Carol) $ ./p2p_server 49153 2 dir2 127.0.0.1 49152  
```  

Now Carol searches for ‘file1’ in terminal, then log:

```ini
file1
[CONNECT] Socket created successfully
[CONNECT] Packet sent. size: 140
[FILE] Enter the File Name for Search:
Message received, size: 140
RESPONSE packet

[FILE] File file1 found on 127.0.0.1, with port: 49151

```

Bob would forward packet to Alice since TTL is still alive. Alice log:

```ini
[CONNECT] Packet sent size: 140
[INFO] Received new packet: QUERY packet
[RESPON] File file1 found, responding to query.
```

Now if Alice searches for file3, it logs:

```ini
file3
[CONNECT] Packet sent size: 140

```

Bob would not forward the packet to Carol address due to the initial TTL being 1. As a result, the packet will expire at Bob. This proves the file flooding query and TTL control.  



***Test: Avoid Loops***

(Bob being a neighbor to Alice, Carol being a neighbor to Bob and Carol being a neighbor to Alice.)

Now all three parties are connected with each other as neighbors. 

```bash
# Initialize Alice as the boostrap server
(terminal Alice) $ ./p2p_server 49151 2 dir1

# Bob being a neighbor connected to Alice
(terminal Bob)   $ ./p2p_server 49152 2 dir1 127.0.0.1 49151 

# Carol being a neighbor connected to Bob
(terminal Carol) $ ./p2p_server 49153 2 dir2 127.0.0.1 49152 127.0.0.1 49151
```

If Alice now queries for ‘file3’, the query will be forwarded to both Bob and Carol. For example, Alice searches for 'file3', Bob does not find it, and would again forward to Carol:

```ini
[FILE] Enter the File Name for Search: 
file3
[CONNECT] Packet sent size: 140
[INFO] Received new packet: QUERY packet
[INFO] File Not found, Forward to next neighbor: 49152
```

But Carol already handled this query from Alice, and would not respond to the same query again. Therefore it would simply ignore:

```ini
[INFO] Received new packet: QUERY packet
[CONNECT] Packet sent size: 140
[INFO] File file3 found, responding to query.
Message received, size: 140
[INFO] Received new packet: QUERY packet
[DUPLICATE ID] Duplicate packet with ID 1165118814 detected. Ignoring and discarding.
```

Thus proving the avoid loop functionality.

***Test: TTL Control***

```bash
# Initialize nodes in a chain topology
(terminal Alice) $ ./p2p_server 49151 1 dir1

# Bob connects to Alice
(terminal Bob)   $ ./p2p_server 49152 2 dir2 127.0.0.1 49151

# Carol connects to Bob
(terminal Carol) $ ./p2p_server 49153 2 dir3 127.0.0.1 49152

# David connects to Carol
(terminal David) $ ./p2p_server 49154 2 dir4 127.0.0.1 49153
```

Now when Alice searches for 'file4' (which is in David's directory) with TTL=1:

```ini
[FILE] Enter the File Name for Search:
file4
[CONNECT] Socket created successfully
[CONNECT] Packet sent size: 140
[INFO] Received new packet: QUERY packet
[TTL] Packet TTL expired, stopping forwarding.
```

Bob's log should show:

```ini
[INFO] Received new packet: QUERY packet
[TTL] Packet TTL expired, stopping forwarding.
```

Carol and David should receive nothing since TTL expired at Bob.

Now if Alice increases TTL to 3 and searches again:

```ini
[FILE] Enter the File Name for Search:
file4
[CONNECT] Socket created successfully
[CONNECT] Packet sent size: 140
[INFO] Received new packet: QUERY packet
```

The query should propagate through the chain and Carol should respond:

```ini
[INFO] Received new packet: QUERY packet
[RESPON] File file4 found, responding to query.
```

Alice should then receive:

```ini
[FILE] File file4 found on 127.0.0.1, with port: 49154
```

This demonstrates that the TTL control mechanism works as expected.


## Grading Criteria Parts

(+1): Pass Makefile compiling (you need to write at least some meaningful codes).

(+1): Network is well setup, i.e. server node can be joined to existing node by passing appropriate command line arguments.

(+2): Successful in flooding query.

(+2): Successful in TTL Control.

(+2): Successful in avoiding loops.

(+2): Thread safety is properly implemented with mutexes and supports concurrent operations.

(total: 10 points)

We will test your code with three to five servers with different neighbored topologies on a Unix-like server machine. So your implementation should be robust to handle with multiple servers running in different terminals. 