#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Allreduce Algorithms

Implement three allreduce algorithms using the provided Comm layer.

API contract:
    allreduce(comm, arr) -> numpy.ndarray
    - comm:  a Comm object (see network/comm.py)
    - arr:   1-D numpy float64 array, same length on all ranks,
             length must be divisible by comm.size()
    - Returns: numpy array with the element-wise SUM across all ranks

Serialization helpers (use these for sending/receiving numpy arrays):
    send:  comm.send(dest, arr.tobytes())
    recv:  np.frombuffer(comm.recv(source), dtype=np.float64)
"""
import numpy as np


def tree_allreduce(comm, arr):
    """
    Tree allreduce = tree_reduce (leaves → root) + tree_broadcast (root → all).

    Cost model: 2*ceil(log2(N))*alpha + 2*ceil(log2(N))*n*beta + ceil(log2(N))*n*gamma
    (gamma << beta in practice, so computation cost is negligible)

    Phase 1 — Tree reduce (mirror of tree_broadcast, bottom-up):
      At each level L (from 1 up to the largest power-of-2 < size):
        - Ranks whose relative index r satisfies r % (2*L) == L: SEND their
          buffer to rank (r - L), i.e., upward in the tree.
        - Ranks whose relative index r satisfies r % (2*L) == 0 AND
          (r + L) < size: RECEIVE from rank (r + L) and ADD to their buffer.
      After this phase, root holds the element-wise sum.

    Phase 2 — Tree broadcast (top-down, same as tree_broadcast in broadcast.py):
      Broadcast the reduced result from root to all ranks.

    TODO: Implement this function (~25-30 lines).
    Hints:
      - Use rel = (rank - root) % size for relative indexing (root = 0).
      - For reduce: levels go 1, 2, 4, ... (bottom-up).
      - For broadcast: levels go ..., 4, 2, 1 (top-down).
      - Serialize with arr.tobytes(), deserialize with np.frombuffer(..., dtype=np.float64).
    """
    rank = comm.rank()
    size = comm.size()
    root = 0
    rel = (rank - root) % size
    buf = arr.copy()

    if size == 1:
        return buf
    level = 1
    while level < size:
        if rel % (2 * level) == level:
            parent_abs = (rel - level + root) % size
            comm.send(parent_abs, buf.tobytes())
        elif rel % (2 * level) == 0 and rel + level < size:
            child_abs = (rel + level + root) % size
            child_data = np.frombuffer(comm.recv(child_abs), dtype = np.float64)
            buf += child_data
        level <<= 1
    level = 1
    while level * 2 < size:
        level *= 2
    while level:
        if rel % (2 * level) == 0 and rel + level < size:
              target_abs = (rel + level + root) % size
              comm.send(target_abs, buf.tobytes())
        elif rel % (2 * level) == level:
            source_abs = (rel - level + root) % size
            buf = np.frombuffer(comm.recv(source_abs), dtype = np.float64)
        level >>= 1
    return buf

def ring_allreduce(comm, arr):
    """
    Ring allreduce = reduce-scatter + allgather over a logical ring.

    Cost model: 2*(N-1)*alpha + 2*(N-1)/N*n*beta + (N-1)/N*n*gamma
    (gamma << beta in practice, so computation cost is negligible)

    The array is split into N equal chunks (one per rank).

    Phase 1 — Reduce-scatter (N-1 steps):
      Each step, every rank sends one chunk to its right neighbor and
      receives one chunk from its left neighbor. The received chunk is
      ADDED to the local buffer. After N-1 steps, each rank holds the
      fully reduced version of exactly one chunk.

      Step indexing:
        send_idx = (rank - step) % N
        recv_idx = (rank - step - 1) % N

    Phase 2 — Allgather (N-1 steps):
      Each step, every rank sends its completed chunk to the right and
      receives a completed chunk from the left. The received chunk
      REPLACES (not adds to) the local buffer. After N-1 steps, every
      rank has the complete reduced array.

      Initial send_idx = (rank + 1) % N, then each step:
        recv_idx = (send_idx - 1) % N
        (after send/recv, send_idx = recv_idx for next step)

    TODO: Implement this function (~30-50 lines).
    Hints:
      - Use comm.sendrecv(dest, send_data, source) for deadlock-free
        simultaneous send-right / recv-left.
      - left = (rank - 1) % N, right = (rank + 1) % N
      - Chunk i spans buf[i*chunk : (i+1)*chunk] where chunk = len(arr) // N
      - Phase 1: received data is ADDED (+=)
      - Phase 2: received data REPLACES (=)
    """
    rank = comm.rank()
    size = comm.size()
    buf = arr.copy()
    if size == 1:
        return buf
    chunk_size = len(buf) // size
    for step in range(size - 1):
        send_idx = (rank - step) % size
        recv_idx = (rank - step - 1) % size
        send_data = buf[send_idx * chunk_size : (send_idx + 1) * chunk_size].tobytes()
        recv_data_bytes = comm.sendrecv((rank + 1) % size, send_data, (rank - 1) % size)
        recv_data = np.frombuffer(recv_data_bytes, dtype=np.float64)
        buf[recv_idx * chunk_size : (recv_idx + 1) * chunk_size] += recv_data
    send_idx = (rank + 1) % size
    for step in range(size - 1):
        recv_idx = (send_idx - 1) % size
        send_data = buf[send_idx * chunk_size : (send_idx + 1) * chunk_size].tobytes()
        recv_data_bytes = comm.sendrecv((rank + 1) % size, send_data, (rank - 1) % size)
        recv_data = np.frombuffer(recv_data_bytes, dtype=np.float64)
        buf[recv_idx * chunk_size : (recv_idx + 1) * chunk_size] = recv_data
        send_idx = recv_idx
    return buf

def naive_allreduce(comm, arr):
    """
    Naive allreduce: every rank sends its data to every other rank.

    Cost model: (N-1) * (alpha + n*beta + n*gamma)
    Total messages: N * (N-1)

    This is provided as a reference implementation. Study it to understand
    how numpy arrays are serialized before implementing tree/ring allreduce.
    """
    rank = comm.rank()
    size = comm.size()
    my_data = arr.copy()
    buf = arr.copy()

    for i in range(size):
        if i == rank:
            for j in range(size):
                if j != rank:
                    comm.send(j, my_data.tobytes())
        else:
            inc = np.frombuffer(comm.recv(i), dtype=np.float64)
            buf += inc

    return buf
