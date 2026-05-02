#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Broadcast Algorithms

Implement two broadcast algorithms using the provided Comm layer.

API contract:
    broadcast(comm, data, root=0) -> bytes
    - comm:  a Comm object (see network/comm.py)
    - data:  bytes on the root rank, None on all other ranks
    - root:  rank of the broadcasting process (default 0)
    - Returns: the broadcast data (bytes) on ALL ranks
"""


def naive_broadcast(comm, data, root=0):
    """
    Naive broadcast: root sends data to every other rank sequentially.

    Cost model: (N-1) * (alpha + n * beta)

    This is provided as a reference implementation. Study it to understand
    the Comm API before implementing tree_broadcast.
    """
    rank = comm.rank()
    size = comm.size()
    if rank == root:
        for i in range(size):
            if i != root:
                comm.send(i, data)
        return data
    else:
        return comm.recv(root)


def tree_broadcast(comm, data, root=0):
    """
    Binary-tree broadcast: root sends data down a binary tree.

    Cost model: ceil(log2(N)) * (alpha + n * beta)

    At each level L (from largest power-of-2 down to 1):
      - Ranks that already have data and whose relative index r satisfies
        r % (2*L) == 0: send to rank (r + L) if it exists.
      - Ranks whose relative index r satisfies r % (2*L) == L: receive
        from rank (r - L).

    TODO: Implement this function (~15-20 lines).
    Hints:
      - Use relative indexing: rel = (rank - root) % size
      - Convert back: abs_rank = (rel + root) % size
      - Start with level = largest power of 2 < size, then halve each step.
      - Only ranks that already have the data should send.
    """
    rank = comm.rank()
    size = comm.size()
    if size == 1: 
        return data
    rel = (rank - root) % size
    L = 1
    while L * 2 < size: 
        L <<= 1
    while L:
        if rel % (2 * L) == 0 and rel + L < size:
            abs_rank = (rel + L + root) % size
            comm.send(abs_rank, data)
        if rel % (2 * L) == L:
            abs_rank = (rel - L + root) % size
            data = comm.recv(abs_rank)
        L >>= 1
    return data
