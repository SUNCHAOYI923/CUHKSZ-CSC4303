#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Scatter

API contract:
    scatter(comm, data, root=0) -> bytes
    - comm:  a Comm object (see network/comm.py)
    - data:  bytes on root (length must be divisible by N), None on others
    - root:  rank that holds the data
    - Returns: bytes — this rank's chunk (length = len(data) / N)
"""


def scatter(comm, data, root=0):
    """
    Scatter: root splits data into N equal chunks and sends chunk i to rank i.

    Cost model: (N-1) * (alpha + n/N * beta)

    Args:
        comm:  Comm object
        data:  bytes on root (length must be divisible by N), None on others
        root:  rank that holds the data
    Returns: bytes — this rank's chunk (length = len(data) / N)

    TODO: Implement this function (~8-10 lines).
    Hints:
      - Root: split data into N chunks, send chunk i to rank i, keep own chunk.
      - Non-root: receive from root.
    """
    rank = comm.rank()
    size = comm.size()
    if rank == root:
        chunk_size = len(data) // size
        tmp = []
        for i in range(size):
            chunk = data[i * chunk_size : (i + 1) * chunk_size]
            if i != root:
                comm.send(i, chunk)
            else:
                tmp = chunk
        return tmp
    else:
        return comm.recv(root)