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

     - **Header**

        ```
        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |          Source Port          |       Destination Port        | ← Identifies sockets
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                        Sequence Number (32)                   | ← Byte-based sequencing
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Acknowledgment Number (32)                 | ← Next expected byte
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  Data Offset  |  0  |  Flags  |       Window Size (16)        | ← Control & flow control
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |     Checksum (16)             |       Urgent Pointer (16)     | ← Integrity & urgent data
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                         Options (variable)                    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                           Data                                |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        ```

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
                
    - **Flow Control**

        - **Automatic Repeat Query**
            
            ARQ with one message at a time is **Stop-and-Wait**. It allows only a single message to be outstanding from sender.

        - **Sliding Window**

           It allows $W$ outstanding packets, enabling pipelining to send multiple packets per RTT for improved performance.

           Sender buffers up to $W$ segments until they are acknowledged. The last frame sent minus last ack rec'd should no more than $W$.

           <img src="pic/5.png" width="60%" height="60%">

            - **Go-Back-N**

                Only buffers next expected packet (LAS). Accepts only sequential packets, discards others, sends **cumulative** ACK.

            - **Selective Repeat**

                Buffers entire window. Stores out-of-order packets, sends individual ACKs, retransmits only lost packets.
            
            - **Sequence Number**

                $n$ bit counter wraps around at $2^n - 1$. Let $\text{LAR}$ be Last Acknowledgement Received, $\text{LAS}$ be Last Acknowledgement Sent.
                |Method|Sender's Range|Receiver's Range|Min Number Needed to Avoid Overlap|
                |:--:|:--:|:--:|:--:|
                |Go-Back-N|$[\text{LAR} + 1,\text{LAR} + W]$|$\text{LAS} + 1$|$W + 1$|
                |Selective Repeat|$[\text{LAR} + 1,\text{LAR} + W]$|$[\text{LAS} + 1,\text{LAS} + W]$|$2W$|
        
        - **Pacing**

            - **ACK Clocking** (sender)

                ACK clocking is a feedback mechanism where the network itself determines the sending pace, preventing queue buildup and ensuring efficient, low-latency data flow.

            - **Flow Control** (Receiver)

                Flow control uses the `WIN` field, calculated as `WIN = ReceiveBuffer - (LastByteRcvd - LastByteRead)`, to dynamically limit the sender's window, preventing receiver buffer overflow.

            $\text{SEQ} + \text{length} < \text{ACK} + \text{WIN}$

            - **Adaptive Timeout**

                |Name|Formula|
                |:--:|:--:|
                |$\text{SRTT}$ (average round‑trip time)|$\text{SRTT}_{n + 1} = (1 - \alpha)\cdot \text{SRTT}_n + \alpha \cdot \text{RTT}_{n + 1}$ |
                |$\text{Svar}$ (variability of RTT)|$\text{Svar}_{n + 1} = (1-\beta)\cdot \text{Svar}_n + \beta \cdot \mid \text{RTT}_{n + 1} - \text{SRTT}_{n + 1} \mid$|
                |$\text{Timeout}$|$\text{Timeout}_n = \text{SRTT}_n + 4 \cdot \text{Svar}_n$|
        
    - **Congestion Control**
        TCP congestion control uses a sliding window (cwnd), interprets packet loss as a congestion signal, and adjusts the window via AIMD to achieve an efficient and roughly fair bandwidth allocation.

        - **Max-Min fairness**

            Increse the rate of one flow will decrease the rate of a smaller flow.

            > Step 1 Initialize all flows at zero  
            Step 2 Increase all flows equally  
            Step 3 Freeze bottlenecked flows  
            Step 4 Repeat for remaining flows

        - **Bandwidth allocation**

            Network layer provides direct feedback & Transport layer reduces load [Network is distributed, no single party has an overall picture of its state.]

            - **Models**
                - Open loop [reserve] & Closed loop [use feedback to adjust rates]

                - Host support & Network support

                - Window based & Rate based

                **TCP is a closed loop,host-driven, and window-based**

            - **AIMD(Additive Increase Multiplicative Decrease)** 

                - Hosts additively increase rate while network not congested

                - Hosts multiplicatively decrease rate when congested

        - **TCP Tahoe**

            - **Slow Start**
                
               For each ACK received: $\text{cwnd} = \text{cwnd} + 1$, $\text{cwnd}$ doubles every RTT.
            
            - **Later Additive Increase (AI)**

                For each ACK received: $\text{cwnd} \leftarrow \text{cwnd} + \frac{1}{\text{cwnd}}$, roughly adds 1 packet per RTT.

            - **Switching Threshold (Initially Infinity)**

                Switch to AI when When $\text{cwnd} > \text{ssthresh}$, and $\text{ssthresh} = \frac{\text{cwnd}}{2}$ after loss. **Begin with slow start after timeout ($\text{cwnd} = 1$).**
            
            - **Fast Retransmit**

                TCP's cumulative ACKs allow duplicate ACKs to signal lost packets for fast retransmission.(Treat three duplicate ACKs as a loss.)
            
            - **Fast Recovery (TCP Reno)**

                Fast recovery keeps data flowing during retransmission by maintaining the ACK clock. It avoids resetting to Slow Start after packet loss. Set $\text{ssthresh} = \frac{\text{cwnd}}{2}$ and then continue AI directly.
        