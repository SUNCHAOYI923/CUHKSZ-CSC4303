#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Correctness Autograder

Tests broadcast and allreduce implementations using multi-process
simulation on a single machine (no EC2 needed).

Usage:
    python3 -m pytest tests/test_correctness.py -v

Scoring (5 points total):
    - tree_broadcast:   1.0 pt
    - scatter:          0.5 pt
    - gather:           0.5 pt
    - tree_reduce:      0.5 pt
    - tree_allreduce:   1.0 pt
    - ring_allreduce:   1.5 pt

Note: naive_broadcast and naive_allreduce are provided as reference
implementations and are tested but not scored.
"""
import multiprocessing as mp
import socket
import struct
import time
import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from network.comm import Comm
from collective.broadcast import naive_broadcast, tree_broadcast
from collective.scatter import scatter
from collective.gather import gather
from collective.reduce import tree_reduce
from collective.allreduce import tree_allreduce, ring_allreduce, naive_allreduce


# ── helpers ──────────────────────────────────────────────────────────

def _find_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _run_worker(fn, rank, size, base_port, args_dict, result_dict, error_dict):
    """Worker process: create Comm, call fn, store result."""
    try:
        hosts = ["127.0.0.1"] * size
        comm = Comm(rank, size, hosts, base_port)
        result = fn(comm, rank, size, **args_dict)
        result_dict[rank] = result
        comm.close()
    except Exception as e:
        import traceback
        error_dict[rank] = traceback.format_exc()


def run_collective(fn, size, args_dict=None, timeout=30):
    """Run fn on `size` local processes, return {rank: result}."""
    if args_dict is None:
        args_dict = {}

    base_port = _find_free_port()

    manager = mp.Manager()
    result_dict = manager.dict()
    error_dict = manager.dict()

    procs = []
    for rank in range(size):
        p = mp.Process(
            target=_run_worker,
            args=(fn, rank, size, base_port, args_dict, result_dict, error_dict),
        )
        p.start()
        procs.append(p)

    for p in procs:
        p.join(timeout=timeout)
        if p.is_alive():
            p.terminate()
            p.join(timeout=5)
    if error_dict:
        for rank, tb in error_dict.items():
            print(f"\n--- Rank {rank} error ---\n{tb}", file=sys.stderr)
        pytest.fail(f"Errors in ranks: {list(error_dict.keys())}")

    return dict(result_dict)


# ── broadcast test functions ─────────────────────────────────────────

def _bcast_worker(comm, rank, size, bcast_fn, msg_size, root):
    if rank == root:
        data = bytes(range(256)) * (msg_size // 256 + 1)
        data = data[:msg_size]
    else:
        data = None
    result = bcast_fn(comm, data, root=root)
    return result


# ── scatter/gather test functions ────────────────────────────────────

def _scatter_worker(comm, rank, size, msg_size, root):
    if rank == root:
        data = bytes(range(256)) * (msg_size // 256 + 1)
        data = data[:msg_size]
    else:
        data = None
    return scatter(comm, data, root=root)


def _gather_worker(comm, rank, size, chunk_size, root):
    chunk = bytes([(rank * 7 + i) % 256 for i in range(chunk_size)])
    return gather(comm, chunk, root=root)


# ── reduce test functions ───────────────────────────────────────────

def _reduce_worker(comm, rank, size, n, root):
    data = np.arange(rank * n, (rank + 1) * n, dtype=np.float64)
    result = tree_reduce(comm, data, root=root)
    if result is not None:
        return result.tobytes()
    return None


# ── allreduce test functions ─────────────────────────────────────────

def _allreduce_worker(comm, rank, size, allreduce_fn, n):
    data = np.arange(rank * n, (rank + 1) * n, dtype=np.float64)
    result = allreduce_fn(comm, data)
    return result.tobytes()


# ── broadcast tests ──────────────────────────────────────────────────

class TestNaiveBroadcast:
    @pytest.mark.parametrize("size", [2, 4])
    @pytest.mark.parametrize("msg_size", [0, 1, 1024, 65536])
    @pytest.mark.parametrize("root", [0])
    def test_basic(self, size, msg_size, root):
        results = run_collective(
            _bcast_worker, size,
            {"bcast_fn": naive_broadcast, "msg_size": msg_size, "root": root},
        )
        expected = bytes(range(256)) * (msg_size // 256 + 1)
        expected = expected[:msg_size]
        for rank, data in results.items():
            assert data == expected, f"Rank {rank}: wrong data"

    @pytest.mark.parametrize("size", [2, 4])
    def test_nonzero_root(self, size):
        root = size - 1
        results = run_collective(
            _bcast_worker, size,
            {"bcast_fn": naive_broadcast, "msg_size": 1024, "root": root},
        )
        expected = bytes(range(256)) * 4
        expected = expected[:1024]
        for rank, data in results.items():
            assert data == expected


class TestTreeBroadcast:
    @pytest.mark.parametrize("size", [2, 4, 8])
    @pytest.mark.parametrize("msg_size", [0, 1, 1024, 65536])
    @pytest.mark.parametrize("root", [0])
    def test_basic(self, size, msg_size, root):
        results = run_collective(
            _bcast_worker, size,
            {"bcast_fn": tree_broadcast, "msg_size": msg_size, "root": root},
        )
        expected = bytes(range(256)) * (msg_size // 256 + 1)
        expected = expected[:msg_size]
        for rank, data in results.items():
            assert data == expected, f"Rank {rank}: wrong data"

    @pytest.mark.parametrize("size", [2, 4, 8])
    def test_nonzero_root(self, size):
        root = size - 1
        results = run_collective(
            _bcast_worker, size,
            {"bcast_fn": tree_broadcast, "msg_size": 1024, "root": root},
        )
        expected = bytes(range(256)) * 4
        expected = expected[:1024]
        for rank, data in results.items():
            assert data == expected


# ── allreduce tests ──────────────────────────────────────────────────

class TestTreeAllreduce:
    @pytest.mark.parametrize("size", [2, 4])
    @pytest.mark.parametrize("n_multiplier", [1, 4, 100])
    def test_correctness(self, size, n_multiplier):
        n = size * n_multiplier
        results = run_collective(
            _allreduce_worker, size,
            {"allreduce_fn": tree_allreduce, "n": n},
        )
        expected = np.zeros(n, dtype=np.float64)
        for r in range(size):
            expected += np.arange(r * n, (r + 1) * n, dtype=np.float64)

        for rank, data_bytes in results.items():
            result = np.frombuffer(data_bytes, dtype=np.float64)
            assert np.allclose(result, expected), f"Rank {rank}: wrong result"

    @pytest.mark.parametrize("size", [8])
    def test_n8(self, size):
        n = size * 100
        results = run_collective(
            _allreduce_worker, size,
            {"allreduce_fn": tree_allreduce, "n": n},
            timeout=60,
        )
        expected = np.zeros(n, dtype=np.float64)
        for r in range(size):
            expected += np.arange(r * n, (r + 1) * n, dtype=np.float64)
        for rank, data_bytes in results.items():
            result = np.frombuffer(data_bytes, dtype=np.float64)
            assert np.allclose(result, expected)


class TestRingAllreduce:
    @pytest.mark.parametrize("size", [2, 4])
    @pytest.mark.parametrize("n_multiplier", [1, 4, 100, 10000])
    def test_correctness(self, size, n_multiplier):
        n = size * n_multiplier
        results = run_collective(
            _allreduce_worker, size,
            {"allreduce_fn": ring_allreduce, "n": n},
        )
        expected = np.zeros(n, dtype=np.float64)
        for r in range(size):
            expected += np.arange(r * n, (r + 1) * n, dtype=np.float64)

        for rank, data_bytes in results.items():
            result = np.frombuffer(data_bytes, dtype=np.float64)
            assert np.allclose(result, expected), f"Rank {rank}: wrong result"

    @pytest.mark.parametrize("size", [8])
    def test_n8(self, size):
        n = size * 100
        results = run_collective(
            _allreduce_worker, size,
            {"allreduce_fn": ring_allreduce, "n": n},
            timeout=60,
        )
        expected = np.zeros(n, dtype=np.float64)
        for r in range(size):
            expected += np.arange(r * n, (r + 1) * n, dtype=np.float64)
        for rank, data_bytes in results.items():
            result = np.frombuffer(data_bytes, dtype=np.float64)
            assert np.allclose(result, expected)


# ── scatter tests ───────────────────────────────────────────────────

class TestScatter:
    @pytest.mark.parametrize("size", [2, 4])
    @pytest.mark.parametrize("msg_size", [0, 128, 1024])
    def test_basic(self, size, msg_size):
        total_size = msg_size * size
        results = run_collective(
            _scatter_worker, size,
            {"msg_size": total_size, "root": 0},
        )
        full_data = bytes(range(256)) * (total_size // 256 + 1)
        full_data = full_data[:total_size]
        for rank, chunk in results.items():
            expected = full_data[rank * msg_size : (rank + 1) * msg_size]
            assert chunk == expected, f"Rank {rank}: wrong chunk"

    @pytest.mark.parametrize("size", [2, 4])
    def test_nonzero_root(self, size):
        root = size - 1
        msg_size = 256 * size
        results = run_collective(
            _scatter_worker, size,
            {"msg_size": msg_size, "root": root},
        )
        full_data = bytes(range(256)) * (msg_size // 256 + 1)
        full_data = full_data[:msg_size]
        chunk_size = msg_size // size
        for rank, chunk in results.items():
            expected = full_data[rank * chunk_size : (rank + 1) * chunk_size]
            assert chunk == expected


# ── gather tests ────────────────────────────────────────────────────

class TestGather:
    @pytest.mark.parametrize("size", [2, 4])
    @pytest.mark.parametrize("chunk_size", [0, 64, 512])
    def test_basic(self, size, chunk_size):
        results = run_collective(
            _gather_worker, size,
            {"chunk_size": chunk_size, "root": 0},
        )
        for rank, data in results.items():
            if rank == 0:
                expected = b""
                for r in range(size):
                    expected += bytes([(r * 7 + i) % 256 for i in range(chunk_size)])
                assert data == expected, "Root: wrong gathered data"
            else:
                assert data is None, f"Rank {rank}: non-root should return None"

    @pytest.mark.parametrize("size", [2, 4])
    def test_nonzero_root(self, size):
        root = size - 1
        chunk_size = 128
        results = run_collective(
            _gather_worker, size,
            {"chunk_size": chunk_size, "root": root},
        )
        for rank, data in results.items():
            if rank == root:
                expected = b""
                for r in range(size):
                    expected += bytes([(r * 7 + i) % 256 for i in range(chunk_size)])
                assert data == expected
            else:
                assert data is None


# ── tree_reduce tests ───────────────────────────────────────────────

class TestTreeReduce:
    @pytest.mark.parametrize("size", [2, 4])
    @pytest.mark.parametrize("n_multiplier", [1, 4, 100])
    def test_correctness(self, size, n_multiplier):
        n = size * n_multiplier
        results = run_collective(
            _reduce_worker, size,
            {"n": n, "root": 0},
        )
        expected = np.zeros(n, dtype=np.float64)
        for r in range(size):
            expected += np.arange(r * n, (r + 1) * n, dtype=np.float64)

        root_data = results[0]
        assert root_data is not None, "Root should have result"
        result = np.frombuffer(root_data, dtype=np.float64)
        assert np.allclose(result, expected), "Root: wrong reduced result"
        for rank in range(1, size):
            assert results[rank] is None, f"Rank {rank}: non-root should return None"

    @pytest.mark.parametrize("size", [2, 4])
    def test_nonzero_root(self, size):
        root = size - 1
        n = size * 10
        results = run_collective(
            _reduce_worker, size,
            {"n": n, "root": root},
        )
        expected = np.zeros(n, dtype=np.float64)
        for r in range(size):
            expected += np.arange(r * n, (r + 1) * n, dtype=np.float64)

        root_data = results[root]
        assert root_data is not None
        result = np.frombuffer(root_data, dtype=np.float64)
        assert np.allclose(result, expected)


# ── naive_allreduce tests ───────────────────────────────────────────

class TestNaiveAllreduce:
    @pytest.mark.parametrize("size", [2, 4])
    @pytest.mark.parametrize("n_multiplier", [1, 4, 100])
    def test_correctness(self, size, n_multiplier):
        n = size * n_multiplier
        results = run_collective(
            _allreduce_worker, size,
            {"allreduce_fn": naive_allreduce, "n": n},
        )
        expected = np.zeros(n, dtype=np.float64)
        for r in range(size):
            expected += np.arange(r * n, (r + 1) * n, dtype=np.float64)

        for rank, data_bytes in results.items():
            result = np.frombuffer(data_bytes, dtype=np.float64)
            assert np.allclose(result, expected), f"Rank {rank}: wrong result"
