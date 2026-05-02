#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Bonus: Distributed SGD with Ring Allreduce

Train a simple neural network on MNIST using data-parallel distributed SGD.
Each worker holds a shard of the training data and computes local gradients,
then all workers synchronize gradients via YOUR ring_allreduce implementation.

Usage (4 nodes):
    python3 network/launcher.py --script bonus/distributed_sgd.py

Or manually:
    python3 bonus/distributed_sgd.py --rank 0 --size 4 --hosts <ips>

Requirements:
    pip3 install numpy

NOTE: This implementation uses numpy only (no PyTorch/TensorFlow) so it
runs on any EC2 instance without GPU or deep learning frameworks.

Scoring (4 bonus points):
    - (2 pt) Working distributed training, correct gradient averaging,
             convergence to >=95% test accuracy.
    - (1 pt) Throughput analysis: samples/sec vs single-node baseline.
    - (1 pt) Scaling analysis: time-to-accuracy with N in {1, 2, 4}.
"""
import argparse
import os
import sys
import time
import struct
import gzip

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from network.comm import Comm
from collective.allreduce import ring_allreduce


# ── MNIST loader (no external dependencies) ────────────────────────

MNIST_URL = "https://ossci-datasets.s3.amazonaws.com/mnist/"
MNIST_FILES = {
    "train_images": "train-images-idx3-ubyte.gz",
    "train_labels": "train-labels-idx1-ubyte.gz",
    "test_images": "t10k-images-idx3-ubyte.gz",
    "test_labels": "t10k-labels-idx1-ubyte.gz",
}


def download_mnist(data_dir="data/mnist"):
    """Download MNIST if not cached. Returns (train_X, train_y, test_X, test_y)."""
    os.makedirs(data_dir, exist_ok=True)

    def fetch(filename):
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            import urllib.request
            url = MNIST_URL + filename
            print(f"Downloading {url}...", flush=True)
            urllib.request.urlretrieve(url, path)
        return path

    def read_images(path):
        with gzip.open(path, "rb") as f:
            magic, n, rows, cols = struct.unpack(">IIII", f.read(16))
            return np.frombuffer(f.read(), dtype=np.uint8).reshape(n, rows * cols) / 255.0

    def read_labels(path):
        with gzip.open(path, "rb") as f:
            magic, n = struct.unpack(">II", f.read(8))
            return np.frombuffer(f.read(), dtype=np.uint8)

    train_X = read_images(fetch(MNIST_FILES["train_images"]))
    train_y = read_labels(fetch(MNIST_FILES["train_labels"]))
    test_X = read_images(fetch(MNIST_FILES["test_images"]))
    test_y = read_labels(fetch(MNIST_FILES["test_labels"]))
    return train_X, train_y, test_X, test_y


# ── Simple neural network (numpy only) ─────────────────────────────

def softmax(z):
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def one_hot(y, k=10):
    n = len(y)
    oh = np.zeros((n, k))
    oh[np.arange(n), y] = 1.0
    return oh


class SimpleNet:
    """Two-layer neural network: 784 -> hidden -> 10."""

    def __init__(self, hidden=128, seed=42):
        rng = np.random.RandomState(seed)
        scale1 = np.sqrt(2.0 / 784)
        scale2 = np.sqrt(2.0 / hidden)
        self.W1 = rng.randn(784, hidden) * scale1
        self.b1 = np.zeros(hidden)
        self.W2 = rng.randn(hidden, 10) * scale2
        self.b2 = np.zeros(10)

    def forward(self, X):
        """Returns (probs, cache) where cache is needed for backward."""
        z1 = X @ self.W1 + self.b1
        a1 = np.maximum(0, z1)  # ReLU
        z2 = a1 @ self.W2 + self.b2
        probs = softmax(z2)
        return probs, (X, z1, a1)

    def backward(self, probs, y, cache):
        """Compute gradients of cross-entropy loss. Returns dict of gradients."""
        X, z1, a1 = cache
        m = X.shape[0]
        dz2 = probs - one_hot(y)  # (m, 10)
        dW2 = a1.T @ dz2 / m
        db2 = dz2.mean(axis=0)
        da1 = dz2 @ self.W2.T
        dz1 = da1 * (z1 > 0)  # ReLU derivative
        dW1 = X.T @ dz1 / m
        db1 = dz1.mean(axis=0)
        return {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}

    def params_to_flat(self):
        """Flatten all parameters into a single 1-D array."""
        return np.concatenate([self.W1.ravel(), self.b1, self.W2.ravel(), self.b2])

    def grads_to_flat(self, grads):
        """Flatten gradient dict into a single 1-D array (same order as params)."""
        return np.concatenate([
            grads["W1"].ravel(), grads["b1"],
            grads["W2"].ravel(), grads["b2"],
        ])

    def flat_to_grads(self, flat):
        """Unpack a flat array back into gradient dict."""
        idx = 0
        shapes = [
            ("W1", self.W1.shape), ("b1", self.b1.shape),
            ("W2", self.W2.shape), ("b2", self.b2.shape),
        ]
        grads = {}
        for name, shape in shapes:
            size = np.prod(shape)
            grads[name] = flat[idx:idx + size].reshape(shape)
            idx += size
        return grads

    def apply_grads(self, grads, lr):
        """SGD update."""
        self.W1 -= lr * grads["W1"]
        self.b1 -= lr * grads["b1"]
        self.W2 -= lr * grads["W2"]
        self.b2 -= lr * grads["b2"]

    def predict(self, X):
        probs, _ = self.forward(X)
        return probs.argmax(axis=1)

    def accuracy(self, X, y):
        return (self.predict(X) == y).mean()


# ── Distributed training ───────────────────────────────────────────

def train_distributed(comm, epochs=10, batch_size=64, lr=0.1):
    """
    Data-parallel distributed SGD.

    Each rank:
    1. Loads MNIST and takes its shard of training data.
    2. For each mini-batch:
       a. Forward + backward on local shard.
       b. Flatten gradients into a single array.
       c. ring_allreduce to sum gradients across all workers.
       d. Divide by world_size to get average gradient.
       e. Apply gradient update.
    3. Evaluate on test set.

    TODO: Fill in the allreduce step below (~5 lines).
    """
    rank = comm.rank()
    size = comm.size()

    # Load data — all ranks load full dataset, then shard
    train_X, train_y, test_X, test_y = download_mnist()

    # Shard training data
    n_train = len(train_X)
    shard_size = n_train // size
    start = rank * shard_size
    end = start + shard_size
    local_X = train_X[start:end]
    local_y = train_y[start:end]

    if rank == 0:
        print(f"World size: {size}, shard size: {shard_size}", flush=True)
        print(f"Total params: {784*128 + 128 + 128*10 + 10}", flush=True)

    # All ranks start with identical model (same seed)
    model = SimpleNet(hidden=128, seed=42)

    n_local = len(local_X)
    n_param = len(model.params_to_flat())
    # Ensure n_param is divisible by size (pad if needed)
    pad = (size - n_param % size) % size

    for epoch in range(epochs):
        # Shuffle local data
        perm = np.random.permutation(n_local)
        local_X = local_X[perm]
        local_y = local_y[perm]

        epoch_loss = 0.0
        n_batches = 0
        total_compute_s = 0.0
        total_comm_s = 0.0
        t0 = time.perf_counter()

        for i in range(0, n_local, batch_size):
            X_batch = local_X[i:i + batch_size]
            y_batch = local_y[i:i + batch_size]
            if len(X_batch) == 0:
                break

            # Forward + backward (local)
            t_comp_start = time.perf_counter()
            probs, cache = model.forward(X_batch)
            grads = model.backward(probs, y_batch, cache)
            flat_grads = model.grads_to_flat(grads)
            t_comp_end = time.perf_counter()
            total_compute_s += t_comp_end - t_comp_start

            # ── DISTRIBUTED GRADIENT AVERAGING ──
            # TODO: Use ring_allreduce to sum flat_grads across all workers,
            #       then divide by size to get the average gradient.
            #
            # Hints:
            #   - ring_allreduce expects len(arr) divisible by comm.size()
            #   - You may need to pad flat_grads (see `pad` variable above)
            #   - After allreduce, divide by size and unpad
            #   - Then call model.flat_to_grads() and model.apply_grads()
            #
            # TODO (analysis): Measure the time spent in allreduce by
            #   wrapping it with time.perf_counter(). Accumulate into
            #   total_comm_s so you can report compute vs communication
            #   breakdown per epoch.

            # ── YOUR CODE HERE (~5 lines + timing) ──
            if pad > 0:
                flat_grads_padded = np.pad(flat_grads, (0, pad), constant_values=0)
            else:
                flat_grads_padded = flat_grads
            t_comm_start = time.perf_counter()
            sum_grads = ring_allreduce(comm, flat_grads_padded)
            t_comm_end = time.perf_counter()
            total_comm_s += t_comm_end - t_comm_start
            avg_grads = sum_grads / size
            if pad > 0:
                avg_grads = avg_grads[:-pad]
            grads_avg_dict = model.flat_to_grads(avg_grads)
            model.apply_grads(grads_avg_dict, lr)

            # Compute loss for logging
            loss = -np.log(probs[np.arange(len(y_batch)), y_batch] + 1e-12).mean()
            epoch_loss += loss
            n_batches += 1

        epoch_time = time.perf_counter() - t0
        avg_loss = epoch_loss / max(n_batches, 1)

        # Evaluate on test set (all ranks, for consistency check)
        acc = model.accuracy(test_X, test_y)
        samples_per_sec = n_local / epoch_time
        compute_pct = total_compute_s / epoch_time * 100 if epoch_time > 0 else 0
        comm_pct = total_comm_s / epoch_time * 100 if epoch_time > 0 else 0

        if rank == 0:
            print(f"Epoch {epoch+1}/{epochs}: loss={avg_loss:.4f}, "
                  f"test_acc={acc:.4f}, "
                  f"time={epoch_time:.1f}s, "
                  f"throughput={samples_per_sec * size:.0f} samples/s, "
                  f"compute={compute_pct:.1f}%, comm={comm_pct:.1f}%",
                  flush=True)

        comm.barrier()

    if rank == 0:
        final_acc = model.accuracy(test_X, test_y)
        print(f"\nFinal test accuracy: {final_acc:.4f}", flush=True)
        if final_acc >= 0.95:
            print("PASS: accuracy >= 95%", flush=True)
        else:
            print("FAIL: accuracy < 95% — check your gradient averaging", flush=True)

    return model


# ── main ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank", type=int, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--hosts", required=True)
    parser.add_argument("--base-port", type=int, default=20000)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.1)
    args = parser.parse_args()

    hosts = args.hosts.split(",")
    comm = Comm(args.rank, args.size, hosts, args.base_port)

    if args.rank == 0:
        print(f"Distributed SGD: {args.size} workers, "
              f"{args.epochs} epochs, batch_size={args.batch_size}, lr={args.lr}",
              flush=True)

    train_distributed(comm, args.epochs, args.batch_size, args.lr)
    comm.close()


if __name__ == "__main__":
    main()
