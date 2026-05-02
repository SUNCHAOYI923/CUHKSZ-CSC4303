[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/z0l_vubR)
# CSC4303 Assignment 6: Collective Communication (12 + 4 bonus points)

### Deadline: April 24, 23:59

### Name: Chaoyi, Sun

### Student ID: 124090550

---

## Overview

In this assignment you will implement six collective communication primitives
and measure their performance on real EC2 instances. The goal is not just
working code — it's understanding **why** different algorithms have different
performance characteristics, and validating theory against measurement.

You will implement:

1. **Tree broadcast** — binary-tree dissemination (log₂N steps)
2. **Scatter** — root splits data into N chunks, one per rank
3. **Gather** — inverse of scatter, root collects from all ranks
4. **Tree reduce** — binary-tree reduction (bottom-up sum)
5. **Tree allreduce** — tree reduce + tree broadcast (latency-optimal)
6. **Ring allreduce** — reduce-scatter + allgather (bandwidth-optimal)

Two reference implementations (`naive_broadcast` and `naive_allreduce`) are
provided so you can study the Comm API before tackling the tree/ring variants.

Then benchmark them on ≥4 EC2 instances and analyze results using the
α+nβ cost model from lecture.

---

## Getting Started

### 1. Fill in your config

Edit `config/my_config.py` with your student ID and EC2 private IPs.

### 2. Implement the algorithms

Fill in the TODO sections in:

- `collective/broadcast.py` — `tree_broadcast()`
- `collective/scatter.py` — `scatter()`
- `collective/gather.py` — `gather()`
- `collective/reduce.py` — `tree_reduce()`
- `collective/allreduce.py` — `tree_allreduce()` and `ring_allreduce()`

Each function has detailed docstrings explaining the algorithm and API.
Use only the provided `Comm` API (`send`, `recv`, `sendrecv`, `barrier`).

### 3. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Test locally

```bash
python3 -m pytest tests/test_correctness.py -v
```

This runs multi-process tests on your local machine (no EC2 needed).

### 5. Set up EC2

See `AWS_SETUP.md` for a step-by-step guide. You need ≥4 c5n.large instances
in the same availability zone with the `csc4303-a6-sg` security group.

**Why c5n.large?** t3 instances have burst credits that cause unpredictable
3× slowdowns, making scientific measurement impossible. Use c5n.large for
stable, reproducible network benchmarks.

### 6. Run benchmarks on EC2

```bash
# Option A: use the launcher (runs on all nodes via SSH)
python3 network/launcher.py --script benchmark/run_benchmark.py

# Option B: manually on each node
# (on each node, in separate terminals)
python3 benchmark/run_benchmark.py --rank <R> --size <N> --hosts <ip1>,<ip2>,...
```

Run benchmarks for N ∈ {4, 8} (or more if you have instances).

### 7. Generate plots

```bash
python3 benchmark/fit_pingpong.py raw_data/pingpong_*.csv
python3 benchmark/plot.py raw_data/benchmark_*.csv --alpha-us <your_alpha> --beta-ns <your_beta>
```

### 8. Write your report

Create `report.md` (or `report.pdf`) covering all parts below.

---

## Grading Rubric (12 + 4 bonus)

### Part 1: Correctness (5 points)

Your code must pass the autograder:


| Component        | Points |
| ---------------- | ------ |
| `tree_broadcast` | 1.0    |
| `scatter`        | 0.5    |
| `gather`         | 0.5    |
| `tree_reduce`    | 0.5    |
| `tree_allreduce` | 1.0    |
| `ring_allreduce` | 1.5    |


We will run `pytest tests/test_correctness.py` with N ∈ {2, 4, 8} and
various message sizes.

### Part 2: α/β Measurement (2 points)

Using `benchmark/ping_pong.py` on your EC2 instances:

1. **(0.5 pt)** Run ping-pong and include the raw CSV in `raw_data/`.
2. **(1.5 pt)** Fit α (per-message latency) and β (per-byte cost) from your
  data. Show your fitting method (e.g., linear regression on RTT vs size).
   Report α in μs and β in ns/byte. Sanity-check your values and explain
   whether they are reasonable for your instance type and network setup.

### Part 3: Broadcast Analysis (2 points)

1. **(0.5 pt)** Benchmark data: naive vs tree broadcast, N ∈ {4, 8},
  message sizes 64B–64MB (≥8 log-spaced points). Include CSV.
2. **(1.0 pt)** Plot: log-log time vs message size, both algorithms on one
  figure. Discuss: does tree always beat naive? By how much? Does the
   speedup match the theoretical log₂N / (N-1) ratio?
3. **(0.5 pt)** Anomaly hunt: identify ≥1 data point deviating >30% from
  the cost-model prediction. Report the point quantitatively (size, measured
   time, predicted time, % deviation). Propose a hypothesis (TCP slow start,
   OS scheduling, MTU boundary effects, etc.).

### Part 4: Allreduce Analysis (3 points)

1. **(0.5 pt)** Benchmark data: tree vs ring allreduce, N ∈ {4, 8},
  message sizes 64B–64MB. Include CSV.
2. **(1.5 pt)** Plot with theory overlay: measured times AND α+nβ predictions
  (using YOUR fitted α, β) on the same figure.
  - Where does the crossover occur? (tree faster for small n, ring for large n)
  - Does the measured crossover match the theoretical prediction?
  - Why does ring win for large messages? (explain in terms of per-step data volume)
3. **(1.0 pt)** Anomaly hunt: same as Part 3. Find ≥1 anomalous point,
  quantify deviation, propose hypothesis.

### Part 5: Bonus — Distributed SGD (4 points)

Implement distributed SGD for MNIST using your `ring_allreduce`.
See `bonus/distributed_sgd.py` for the template.

1. **(2 pt)** Working distributed training on 4 nodes, correct gradient
  averaging, convergence to ≥95% test accuracy.
2. **(1 pt)** Communication breakdown: the template prints per-epoch
  `compute%` and `comm%`. Report these numbers and explain: where is
   the bottleneck? How does the gradient size (~800KB for this model)
   relate to the allreduce times you measured in Part 4? What would
   happen if the model had 10× more parameters?
3. **(1 pt)** Scaling analysis: how does time-to-accuracy change with
  N ∈ {1, 2, 4}? Is it linear speedup? Why or why not? (Hint: think
   about how communication overhead changes with N.)

---

## Deliverables

Submit via **GitHub Classroom**. Push all your work to the assigned repo.
Make sure the following files are present before the deadline:

```
collective/
├── broadcast.py
├── scatter.py
├── gather.py
├── reduce.py
└── allreduce.py
raw_data/
├── pingpong_*.csv
└── benchmark_*.csv
plots/
├── pingpong_fitting.png
├── broadcast_comparison_N4.png
├── broadcast_comparison_N8.png
├── allreduce_theory_N4.png
└── allreduce_theory_N8.png
report.md                        (use the provided template)
config/my_config.py
bonus/distributed_sgd.py         (optional)
```

> **Important:** Use the provided `report.md` template. Do not rename section
> headers or image filenames — they are used for grading. Place all plots in
> the `plots/` directory with the exact filenames shown above.

---

## Academic Integrity

- You may use AI tools to help understand algorithms and debug code.
- Your benchmark data **must** come from your own EC2 instances. CSV files
from `benchmark/run_benchmark.py` contain metadata (timestamps, UUIDs, instance
info) that we cross-check
across submissions.
- Your analysis and anomaly hunts must reference your own plots and data.
- Sharing raw data or CSVs between students will be flagged automatically.

---

## Provided Files


| File                         | Description                              |
| ---------------------------- | ---------------------------------------- |
| `network/comm.py`            | TCP communication layer (DO NOT MODIFY)  |
| `network/launcher.py`        | Multi-node SSH launcher                  |
| `benchmark/ping_pong.py`     | Latency/bandwidth measurement            |
| `benchmark/fit_pingpong.py`  | α/β fitting + ping-pong plot generation  |
| `benchmark/run_benchmark.py` | Benchmark driver with forensic metadata  |
| `benchmark/plot.py`          | CSV → PNG plotting                       |
| `tests/test_correctness.py`  | Local autograder                         |
| `config/my_config.py`        | Student config template                  |
| `report.md`                  | Report template (fill in, do not rename) |
| `AWS_SETUP.md`               | EC2 setup guide                          |


---

## Quick Reference: Cost Models


| Algorithm       | Cost                                         |
| --------------- | -------------------------------------------- |
| Naive broadcast | (N-1) · (α + nβ)                             |
| Tree broadcast  | ⌈log₂N⌉ · (α + nβ)                           |
| Scatter         | (N-1) · (α + n/N · β)                        |
| Gather          | (N-1) · (α + n/N · β)                        |
| Tree reduce     | ⌈log₂N⌉ · α + ⌈log₂N⌉ · nβ + ⌈log₂N⌉ · nγ    |
| Tree allreduce  | 2⌈log₂N⌉ · α + 2⌈log₂N⌉ · nβ + ⌈log₂N⌉ · nγ  |
| Ring allreduce  | 2(N-1) · α + 2 · (N-1)/N · nβ + (N-1)/N · nγ |


Where:

- α = per-message latency (fixed overhead per send/recv)
- β = per-byte transfer cost (network)
- γ = per-byte computation cost (reduction operation, e.g., addition)
- n = message size in bytes, N = number of processes

> **Note:** In practice for part 1 to part 4 γ ≪ β — computation is much cheaper than network  
> transfer. For your plots and analysis you may simplify by dropping γ.

