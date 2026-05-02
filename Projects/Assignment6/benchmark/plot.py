#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Plotting Script

Reads benchmark CSVs and generates comparison plots.

Usage:
    python3 benchmark/plot.py raw_data/benchmark_N4_*.csv
    python3 benchmark/plot.py raw_data/   # reads all CSVs in directory

Generates:
    - plots/broadcast_comparison_N{N}.png   (naive vs tree, time and throughput)
    - plots/allreduce_comparison_N{N}.png   (tree vs ring, time and throughput)
    - plots/allreduce_theory_N{N}.png       (measured vs alpha+n*beta prediction)
"""
import argparse
import csv
import glob
import os
import sys

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("WARNING: matplotlib not found. Install with: pip3 install matplotlib")
    print("Falling back to text-only summary.\n")


def load_csvs(paths):
    rows = []
    for p in paths:
        if os.path.isdir(p):
            files = sorted(glob.glob(os.path.join(p, "*.csv")))
        else:
            files = [p]
        for f in files:
            with open(f) as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    row["size_bytes"] = int(row["size_bytes"])
                    row["min_s"] = float(row["min_s"])
                    row["median_s"] = float(row["median_s"])
                    row["world_size"] = int(row["world_size"])
                    rows.append(row)
    return rows


def filter_rows(rows, operation, algorithm):
    return sorted(
        [r for r in rows if r["operation"] == operation and r["algorithm"] == algorithm],
        key=lambda r: r["size_bytes"],
    )


def print_summary(rows):
    operations = sorted(set(r["operation"] for r in rows))
    for op in operations:
        algos = sorted(set(r["algorithm"] for r in rows if r["operation"] == op))
        print(f"\n{'='*60}")
        print(f"  {op.upper()}")
        print(f"{'='*60}")
        print(f"  {'size':>12s}", end="")
        for algo in algos:
            print(f"  {algo:>14s}", end="")
        if len(algos) == 2:
            print(f"  {'speedup':>8s}", end="")
        print()

        sizes = sorted(set(r["size_bytes"] for r in rows if r["operation"] == op))
        for sz in sizes:
            print(f"  {sz:>12d}", end="")
            times = {}
            for algo in algos:
                matching = [r for r in rows
                           if r["operation"] == op and r["algorithm"] == algo
                           and r["size_bytes"] == sz]
                if matching:
                    t = matching[0]["min_s"]
                    times[algo] = t
                    print(f"  {t*1000:>12.3f}ms", end="")
                else:
                    print(f"  {'N/A':>14s}", end="")
            if len(algos) == 2 and all(a in times for a in algos):
                sp = times[algos[0]] / times[algos[1]] if times[algos[1]] > 0 else 0
                print(f"  {sp:>7.2f}x", end="")
            print()


def plot_comparison(rows, operation, algo1, algo2, output_dir):
    if not HAS_MATPLOTLIB:
        return

    d1 = filter_rows(rows, operation, algo1)
    d2 = filter_rows(rows, operation, algo2)
    if not d1 or not d2:
        return

    sizes1 = [r["size_bytes"] for r in d1]
    times1 = [r["min_s"] * 1000 for r in d1]
    sizes2 = [r["size_bytes"] for r in d2]
    times2 = [r["min_s"] * 1000 for r in d2]

    N = d1[0]["world_size"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.loglog(sizes1, times1, "o-", label=algo1, linewidth=2)
    ax1.loglog(sizes2, times2, "s-", label=algo2, linewidth=2)
    ax1.set_xlabel("Message Size (bytes)")
    ax1.set_ylabel("Time (ms)")
    ax1.set_title(f"{operation} Latency (N={N})")
    ax1.legend()
    ax1.grid(True, which="both", alpha=0.3)

    tp1 = [r["size_bytes"] / r["min_s"] / 1e6 for r in d1]
    tp2 = [r["size_bytes"] / r["min_s"] / 1e6 for r in d2]
    ax2.semilogx(sizes1, tp1, "o-", label=algo1, linewidth=2)
    ax2.semilogx(sizes2, tp2, "s-", label=algo2, linewidth=2)
    ax2.set_xlabel("Message Size (bytes)")
    ax2.set_ylabel("Throughput (MB/s)")
    ax2.set_title(f"{operation} Throughput (N={N})")
    ax2.legend()
    ax2.grid(True, which="both", alpha=0.3)

    plt.tight_layout()
    fname = os.path.join(output_dir, f"{operation}_comparison_N{N}.png")
    plt.savefig(fname, dpi=150)
    print(f"Saved: {fname}")
    plt.close()


def plot_theory_overlay(rows, alpha_s, beta_s_per_byte, output_dir):
    """Overlay measured allreduce with alpha+n*beta predictions."""
    if not HAS_MATPLOTLIB:
        return

    d_tree = filter_rows(rows, "allreduce", "tree_allreduce")
    d_ring = filter_rows(rows, "allreduce", "ring_allreduce")
    if not d_tree or not d_ring:
        return

    N = d_tree[0]["world_size"]
    log2N = np.ceil(np.log2(N))

    sizes = np.array([r["size_bytes"] for r in d_tree], dtype=float)
    tree_meas = np.array([r["min_s"] * 1000 for r in d_tree])
    ring_meas = np.array([r["min_s"] * 1000 for r in d_ring])

    tree_theory = 2 * log2N * (alpha_s + sizes * beta_s_per_byte) * 1000
    ring_theory = 2 * (N - 1) * (alpha_s + sizes / N * beta_s_per_byte) * 1000

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.loglog(sizes, tree_meas, "o-", label="tree measured", linewidth=2)
    ax.loglog(sizes, ring_meas, "s-", label="ring measured", linewidth=2)
    ax.loglog(sizes, tree_theory, "o--", alpha=0.5, label="tree theory")
    ax.loglog(sizes, ring_theory, "s--", alpha=0.5, label="ring theory")

    ax.set_xlabel("Message Size (bytes)")
    ax.set_ylabel("Time (ms)")
    ax.set_title(f"Allreduce: Measured vs Theory (N={N}, α={alpha_s*1e6:.0f}μs, β={beta_s_per_byte*1e9:.1f}ns/B)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)

    plt.tight_layout()
    fname = os.path.join(output_dir, f"allreduce_theory_N{N}.png")
    plt.savefig(fname, dpi=150)
    print(f"Saved: {fname}")
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="CSV files or directories")
    parser.add_argument("--alpha-us", type=float, default=56.0,
                        help="Fitted alpha in microseconds")
    parser.add_argument("--beta-ns", type=float, default=2.4,
                        help="Fitted beta in ns/byte")
    parser.add_argument("--output-dir", default="plots",
                        help="Directory for output PNG files")
    args = parser.parse_args()

    rows = load_csvs(args.inputs)
    if not rows:
        print("No data found.")
        sys.exit(1)

    print(f"Loaded {len(rows)} data points.")
    print_summary(rows)

    os.makedirs(args.output_dir, exist_ok=True)

    plot_comparison(rows, "broadcast", "naive_broadcast", "tree_broadcast",
                    args.output_dir)
    plot_comparison(rows, "allreduce", "tree_allreduce", "ring_allreduce",
                    args.output_dir)
    plot_theory_overlay(rows, args.alpha_us * 1e-6, args.beta_ns * 1e-9,
                        args.output_dir)


if __name__ == "__main__":
    main()
