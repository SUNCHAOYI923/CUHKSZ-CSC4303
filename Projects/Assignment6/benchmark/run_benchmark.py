#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Benchmark Driver

Runs broadcast and allreduce benchmarks on EC2 and writes CSV with
forensic metadata. Rank 0 collects and writes all results.

Usage (via launcher):
    python3 network/launcher.py --script benchmark/run_benchmark.py

Or manually on each node:
    python3 benchmark/run_benchmark.py --rank 0 --size 4 --hosts <ips> [--base-port 20000]
"""
import argparse
import csv
import os
import sys
import time
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from network.comm import Comm
from collective.broadcast import naive_broadcast, tree_broadcast
from collective.allreduce import tree_allreduce, ring_allreduce


# ── forensic metadata ───────────────────────────────────────────────

def _get_ec2_metadata(path, timeout=2):
    import urllib.request
    try:
        token_req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        token = urllib.request.urlopen(token_req, timeout=timeout).read().decode()
        req = urllib.request.Request(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token},
        )
        return urllib.request.urlopen(req, timeout=timeout).read().decode()
    except Exception:
        return "N/A"


def get_forensic_metadata():
    return {
        "instance_id": _get_ec2_metadata("instance-id"),
        "instance_type": _get_ec2_metadata("instance-type"),
        "az": _get_ec2_metadata("placement/availability-zone"),
        "hostname": _get_ec2_metadata("hostname"),
    }


# ── benchmark functions ─────────────────────────────────────────────

MSG_SIZES = [64, 256, 1024, 4096, 16384, 65536, 262144, 1048576,
             4194304, 16777216, 67108864]

WARMUP_ROUNDS = 3
BENCH_ROUNDS_SMALL = 20
BENCH_ROUNDS_LARGE = 5
LARGE_THRESHOLD = 262144


def bench_broadcast(comm, bcast_fn, label):
    rank = comm.rank()
    results = []

    for sz in MSG_SIZES:
        data_root = b"\x42" * sz if rank == 0 else None
        rounds = BENCH_ROUNDS_SMALL if sz <= LARGE_THRESHOLD else BENCH_ROUNDS_LARGE

        for _ in range(WARMUP_ROUNDS):
            bcast_fn(comm, data_root if rank == 0 else None, root=0)
            comm.barrier()

        times = []
        for _ in range(rounds):
            comm.barrier()
            t0 = time.perf_counter()
            bcast_fn(comm, data_root if rank == 0 else None, root=0)
            t1 = time.perf_counter()
            times.append(t1 - t0)

        comm.barrier()
        if rank == 0:
            results.append({
                "algorithm": label,
                "operation": "broadcast",
                "size_bytes": sz,
                "rounds": rounds,
                "min_s": min(times),
                "median_s": sorted(times)[len(times) // 2],
                "mean_s": sum(times) / len(times),
            })

    return results


def bench_allreduce(comm, allreduce_fn, label):
    rank = comm.rank()
    results = []

    for sz in MSG_SIZES:
        n_floats = (sz // 8 // comm.size()) * comm.size()
        if n_floats < comm.size():
            n_floats = comm.size()
        data = np.ones(n_floats, dtype=np.float64)
        actual_bytes = n_floats * 8

        rounds = BENCH_ROUNDS_SMALL if sz <= LARGE_THRESHOLD else BENCH_ROUNDS_LARGE

        for _ in range(WARMUP_ROUNDS):
            allreduce_fn(comm, data)
            comm.barrier()

        times = []
        for _ in range(rounds):
            comm.barrier()
            t0 = time.perf_counter()
            allreduce_fn(comm, data)
            t1 = time.perf_counter()
            times.append(t1 - t0)

        comm.barrier()
        if rank == 0:
            results.append({
                "algorithm": label,
                "operation": "allreduce",
                "size_bytes": actual_bytes,
                "rounds": rounds,
                "min_s": min(times),
                "median_s": sorted(times)[len(times) // 2],
                "mean_s": sum(times) / len(times),
            })

    return results


# ── main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank", type=int, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--hosts", required=True)
    parser.add_argument("--base-port", type=int, default=20000)
    parser.add_argument("--output-dir", default="raw_data")
    args = parser.parse_args()

    hosts = args.hosts.split(",")
    comm = Comm(args.rank, args.size, hosts, args.base_port)

    run_uuid = str(uuid.uuid4())
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta = get_forensic_metadata() if args.rank == 0 else {}

    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config.my_config import STUDENT_ID, STUDENT_NAME
    except ImportError:
        STUDENT_ID = "UNKNOWN"
        STUDENT_NAME = "UNKNOWN"

    if not STUDENT_ID or STUDENT_ID == "UNKNOWN":
        print("ERROR: STUDENT_ID is empty. Fill in config/my_config.py first.", file=sys.stderr)
        sys.exit(1)

    if args.rank == 0:
        print(f"Benchmark: size={args.size}, run_uuid={run_uuid}", flush=True)

    all_results = []

    if args.rank == 0:
        print("\n--- Broadcast benchmarks ---", flush=True)
    all_results.extend(bench_broadcast(comm, naive_broadcast, "naive_broadcast"))
    all_results.extend(bench_broadcast(comm, tree_broadcast, "tree_broadcast"))

    if args.rank == 0:
        print("\n--- Allreduce benchmarks ---", flush=True)
    all_results.extend(bench_allreduce(comm, tree_allreduce, "tree_allreduce"))
    all_results.extend(bench_allreduce(comm, ring_allreduce, "ring_allreduce"))

    if args.rank == 0:
        os.makedirs(args.output_dir, exist_ok=True)
        filename = f"{args.output_dir}/benchmark_N{args.size}_{timestamp.replace(':', '')}.csv"

        fieldnames = [
            "student_id", "student_name", "run_uuid", "timestamp_utc",
            "instance_id", "instance_type", "az", "hostname",
            "world_size", "operation", "algorithm", "size_bytes",
            "rounds", "min_s", "median_s", "mean_s",
            "min_throughput_mbps",
        ]

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in all_results:
                throughput = r["size_bytes"] / r["min_s"] / 1e6 if r["min_s"] > 0 else 0
                row = {
                    "student_id": STUDENT_ID,
                    "student_name": STUDENT_NAME,
                    "run_uuid": run_uuid,
                    "timestamp_utc": timestamp,
                    "instance_id": meta.get("instance_id", "N/A"),
                    "instance_type": meta.get("instance_type", "N/A"),
                    "az": meta.get("az", "N/A"),
                    "hostname": meta.get("hostname", "N/A"),
                    "world_size": args.size,
                    "operation": r["operation"],
                    "algorithm": r["algorithm"],
                    "size_bytes": r["size_bytes"],
                    "rounds": r["rounds"],
                    "min_s": f"{r['min_s']:.6f}",
                    "median_s": f"{r['median_s']:.6f}",
                    "mean_s": f"{r['mean_s']:.6f}",
                    "min_throughput_mbps": f"{throughput:.1f}",
                }
                writer.writerow(row)

        print(f"\nResults written to {filename}", flush=True)

    comm.close()
    if args.rank == 0:
        print("Benchmark complete.", flush=True)


if __name__ == "__main__":
    main()
