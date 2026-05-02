#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Tree Reduce

API contract:
    tree_reduce(comm, arr, root=0) -> numpy.ndarray | None
    - comm:  a Comm object (see network/comm.py)
    - arr:   1-D numpy float64 array (same length on all ranks)
    - root:  rank that receives the final sum
    - Returns: numpy array with element-wise sum on root; None on other ranks.

Serialization helpers (use these for sending/receiving numpy arrays):
    send:  comm.send(dest, arr.tobytes())
    recv:  np.frombuffer(comm.recv(source), dtype=np.float64)
"""
import numpy as np


def tree_reduce(comm, arr, root=0):
    """
    Tree reduce: leaves send up to root, which holds the element-wise sum.

    Cost model: ceil(log2(N))*alpha + ceil(log2(N))*n*beta + ceil(log2(N))*n*gamma

    This is the bottom-up phase only (no broadcast back). After this call,
    only root has the correct result; other ranks' buffers are undefined.

    Args:
        comm:  Comm object
        arr:   1-D numpy float64 array (same length on all ranks)
        root:  rank that receives the final sum
    Returns: numpy array with element-wise sum on root; None on other ranks.

    TODO: Implement this function (~15 lines).
    Hints:
      - Same tree structure as tree_broadcast, but bottom-up (levels 1, 2, 4, ...).
      - Ranks with rel % (2*L) == L: send buffer to parent (rel - L).
      - Ranks with rel % (2*L) == 0 and child exists: recv and add (+=).
    """
    rank = comm.rank()
    size = comm.size()
    rel = (rank - root) % size
    level = 1
    while level < size:
        if rel % (2 * level) == level:
            rel_abs = (rel - level + root) % size
            comm.send(rel_abs, arr.tobytes())
        elif rel % (2 * level) == 0 and rel + level < size:
            child_abs = (rel + level + root) % size
            child_data = comm.recv(child_abs)
            child_arr = np.frombuffer(child_data, dtype=np.float64)
            arr += child_arr
        level <<= 1

    if rank == root:
        return arr
    else:
        return None