#!/usr/bin/env python3
"""
Fit alpha/beta from ping-pong CSV and generate a fitting plot.

Usage:
    python3 benchmark/fit_pingpong.py raw_data/pingpong_*.csv

Output:
    - prints fitted alpha (us) and beta (ns/byte)
    - saves plots/pingpong_fitting.png
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
except ImportError:
    print("ERROR: matplotlib is required. Install with: pip3 install matplotlib", file=sys.stderr)
    sys.exit(1)


def load_rows(paths):
    rows = []
    for p in paths:
        if any(ch in p for ch in "*?[]"):
            files = sorted(glob.glob(p))
        elif os.path.isdir(p):
            files = sorted(glob.glob(os.path.join(p, "pingpong_*.csv")))
            if not files:
                files = sorted(glob.glob(os.path.join(p, "*.csv")))
        else:
            files = [p]

        for f in files:
            with open(f) as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    if "size_bytes" not in row or "min_us" not in row:
                        continue
                    rows.append((int(row["size_bytes"]), float(row["min_us"])))
    return rows


def fit_alpha_beta(rows):
    rows = sorted(rows, key=lambda x: x[0])
    sizes = np.array([r[0] for r in rows], dtype=float)
    min_us = np.array([r[1] for r in rows], dtype=float)

    # Fit RTT = c + m * size. Then alpha = c/2, beta = m/2.
    m, c = np.polyfit(sizes, min_us, 1)
    alpha_us = c / 2.0
    beta_ns_per_byte = (m / 2.0) * 1000.0
    return sizes, min_us, alpha_us, beta_ns_per_byte, m, c


def plot_fit(sizes, min_us, m, c, out_png):
    fit = m * sizes + c
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sizes, min_us, "o", label="measured min RTT")
    ax.plot(sizes, fit, "--", label="linear fit")
    ax.set_xscale("log")
    ax.set_xlabel("Message Size (bytes)")
    ax.set_ylabel("RTT (us)")
    ax.set_title("Ping-pong RTT Fitting")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="ping-pong CSV file(s), wildcard(s), or directory")
    parser.add_argument("--output", default="plots/pingpong_fitting.png", help="Output plot path")
    args = parser.parse_args()

    rows = load_rows(args.inputs)
    if not rows:
        print("No valid ping-pong data found.", file=sys.stderr)
        sys.exit(1)

    sizes, min_us, alpha_us, beta_ns_per_byte, m, c = fit_alpha_beta(rows)

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    plot_fit(sizes, min_us, m, c, args.output)

    print(f"alpha_us={alpha_us:.2f}")
    print(f"beta_ns_per_byte={beta_ns_per_byte:.3f}")
    print(f"saved_plot={args.output}")


if __name__ == "__main__":
    main()
