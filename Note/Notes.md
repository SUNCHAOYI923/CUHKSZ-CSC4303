# CSC4303 Network Programming

## Reference

- https://book.systemsapproach.org/foundation.html

## Transport Layer

### Network Model

|Layer|Description|Example|
|:--:|:--:|:--:|
|Application|Programs that use network service|HTTP, DNS, CDNs|
|Transport|Provides end-to-end data delivery|TCP, UDP|
|Network|Send packets over multiple networks|IP, NAT, BGP|
|Link|Send frames over one or more links|Ethernet, 802.11|
|Physical|Send bits using signals|wires, fiber, wireless|

#### Transport Layer

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

- **UDP**

    - **Connectionless** 
        
        Each packet is independent.

        ```
        Sender    Time       Receiver
          |                     |
          |----- Packet1 -----> |
          |                     |
          |----- Packet2 -----> |
          |                     |
        ```

    - **Buffering**

        UDP buffering is a "temporary storage area" maintained by the operating system for each UDP port, where arriving packets queue up when applications can't process them immediately.

        ```
        Application A  Application B   Application C
            ↓               ↓               ↓
        [Port X]        [Port Y]        [Port Z]      ← Port mapping
            ↓               ↓               ↓
        [Queue 1]       [Queue 2]       [Queue 3]     ← Independent UDP message queues
            │               │               │
            └───────┬───────┴───────┬───────┘
                    ↓               ↓
            [Port Multiplexer/Demultiplexer]          ← Routes by port number
                    ↓
            [Incoming UDP packets]
        ```

    - **Header**

        Note that the Datagram length up to 64K.
        ```
             32-bit width (4 bytes per row)
        0                  16                31
        ┌──────────────────┬──────────────────┐
        │ Source Port      │ Destination Port │ ← Port addressing
        │   (16 bits)      │   (16 bits)      │
        ├──────────────────┴──────────────────┤
        │    Length        │    Checksum      │ ← Size & integrity
        │    (16 bits)     │    (16 bits)     │
        ├─────────────────────────────────────┤
        │                                     │
        │           Application Data          │
        │                                     │
        └─────────────────────────────────────┘
        ```
    
- **TCP**

    - **Connection Establishment (Setup)**

        - **Three-Way Handshake**

            Both parties send Initial Sequence Numbers (ISNs) via SYNchronize segments. Each party acknowledges the other's sequence number using ACKnowledge segments.

            <img src="pic/1.png" width="40%" height="40%">

            |Step|Initiator (Client)| Receiver (Server)|Description|
            |:--:|:--:|:--:|:--:|
            |First Handshake | Sends $\texttt{SYN}=1, \texttt{seq}=x$ | Waits for connection request | Client requests to establish a connection and sends its ISN $x$.|
            |Second Handshake | Waits for acknowledgment | Sends $\texttt{SYN}=1, \texttt{ACK}=1, \texttt{seq}=y, \texttt{ack}=x+1$ <br> It acknowledges receipt through sequence number $x$. | Server agrees to connect, sends its own ISN $y$, and acknowledges the receipt of $x$.|
            |Third Handshake | Sends $\texttt{ACK}=1, \texttt{seq}=x+1, \texttt{ack}=y+1$ | Connection established| Client acknowledges the receipt of $y$, and the connection is formally established.|

            Three-way handshake prevents a server from wasting resources on stale or duplicate connection requests by requiring the client's final acknowledgment.

        - **State Machine**

            <img src="pic/2.png" width="70%" height="70%">

            - Client Path `CLOSED → connect() → SYN_SENT → Receive SYN+ACK → ESTABLISHED`

            - Server Path `CLOSED → listen() → LISTEN → Receive SYN → SYN_RCVD → Receive ACK → ESTABLISHED`

            - Both parties run instances of this state machine, and TCP allows for simultaneous open.

    - **Sliding Windows/Flow Control**

    - **Connection Release (Teardown)**

        - **Four-Way Handshake (symmetric)**

            <img src="pic/3.png" width="40%" height="40%">

            | Step | Initiator (Active Closer) | Receiver (Passive Closer) | Description |
            |:---:|:---:|:---:|:---:|
            | First Wave | Sends $\texttt{FIN}=1, \texttt{seq}=u$ | Waits for close request | Initiator has finished sending data and requests to close its sending channel. |
            | Second Wave | Waits for remaining data | Sends $\texttt{ACK}=1, \texttt{ack}=u+1$ | Receiver acknowledges the close request **but may still have data to send**. |
            | Third Wave | Waits for confirmation | Sends $\texttt{FIN}=1, \texttt{seq}=v$ | Receiver has finished sending data and requests to close its sending channel. |
            | Fourth Wave | Sends $\texttt{ACK}=1, \texttt{ack}=v+1$ | Connection closed | Initiator acknowledges the close request. |
        
        - **State Machine**

            <img src="pic/4.png" width="70%" height="70%">

            - **Active Closer Path** `ESTABLISHED → close() → FIN_WAIT_1 → Receive ACK → FIN_WAIT_2 → Receive FIN → TIME_WAIT → Timeout → CLOSED`

            - **Passive Closer Path** `ESTABLISHED → Receive FIN → CLOSE_WAIT → close() → LAST_ACK → Receive ACK → CLOSED`

            - **TIME_WAIT State**

                - $2 \times \texttt{MSL}$ (Maximum Segment Lifetime).

                - Lost ACKs can be recovered.

                - Old segments won't confuse new connections.