#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Gather

API contract:
    gather(comm, data, root=0) -> bytes | None
    - comm:  a Comm object (see network/comm.py)
    - data:  bytes on every rank (same length on all ranks)
    - root:  rank that collects the data
    - Returns: on root, concatenated bytes from all ranks (in rank order);
               on non-root ranks, None.
"""


def gather(comm, data, root=0):
    """
    Gather: all ranks send their data to root, which concatenates in rank order.

    Cost model: (N-1) * (alpha + n/N * beta)

    Args:
        comm:  Comm object
        data:  bytes on every rank (same length on all ranks)
        root:  rank that collects the data
    Returns: on root, concatenated bytes from all ranks (in rank order);
             on non-root ranks, None.

    TODO: Implement this function (~8-10 lines).
    Hints:
      - Non-root: send data to root.
      - Root: receive from each rank in order, concatenate.
    """
    rank = comm.rank()
    size = comm.size()
    if rank == root:
        result = b''
        for i in range(size):
            if i != root:
                chunk = comm.recv(i)
                result += chunk
            else:
                result += data
        return result
    else:
        comm.send(root, data)
        return None