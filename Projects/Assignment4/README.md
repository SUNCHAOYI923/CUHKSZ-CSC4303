[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/5th6Ii6v)
# CSC4303 Assignment-4: Chord DHT (12 points)

### Deadline: March 27, 2026, 23:59

### Name: Chaoyi, Sun

### Student ID: 124090550

## Overview

This assignment involves implementing the **Chord Distributed Hash Table (DHT)** protocol, a scalable peer-to-peer lookup protocol that provides a way to locate keys in a distributed network environment. Chord is notable for its simplicity, provable correctness, and performance guarantees.

Your task is to implement the core algorithms of a Chord DHT including key lookup, node join, stabilization mechanisms, key storage, and (optionally) fault tolerance.

## Background

The Chord protocol specifies how to find the location of keys, how new nodes join the system, and how to recover from node failures. Each node in a Chord system maintains a routing table called a **finger table** that enables fast key lookups in **O(log N)** time, where N is the number of nodes in the system.

Chord arranges nodes in a logical ring where each node has a **successor** and a **predecessor**. Keys are assigned to nodes based on consistent hashing, which provides load balancing and minimizes the number of keys that must move when nodes join or leave the system.

## Project Structure

```
.
├── README.md           # This file
├── chord_node.py       # Node implementation (YOUR WORK HERE)
└── test_dht.py         # Test suite (do not modify)
```

### Key Classes and Attributes

The `Node` class in `chord_node.py` provides the following attributes:

| Attribute     | Type                          | Description                                      |
|---------------|-------------------------------|--------------------------------------------------|
| `node_id`     | `int`                         | This node's identifier on the ring               |
| `host`        | `str`                         | Hostname / IP address                            |
| `port`        | `int`                         | TCP port for the node's server                   |
| `m`           | `int`                         | Number of bits in the identifier space (default 5) |
| `max_id`      | `int`                         | Size of the ring: `2^m`                          |
| `predecessor` | `(id, host, port)` or `None`  | Predecessor node address                         |
| `successor`   | `(id, host, port)`            | Successor node address                           |
| `finger`      | `list` of `(id, host, port)`  | Finger table (1-indexed, size `m+1`)             |
| `next`        | `int`                         | Index of the next finger to fix (1 to m)         |
| `data`        | `dict`                        | Local key-value storage                          |

### Provided Methods (do not modify)

- `remote_call(node_addr, command, params)` — Send a command to another node (or handle locally). Supported commands: `"find_successor"`, `"closest_preceding_node"`, `"get_predecessor"`, `"notify"`, `"ping"`, `"store"`, `"retrieve"`, `"get_data"`, `"transfer_keys"`.
- `run_server()` / `handle_client()` — TCP server that dispatches incoming commands.
- `stop()` — Gracefully shut down the node.

## Assignment Requirements

### Part 1: Core Chord Protocol (4 points)

Implement the following methods in `chord_node.py`:

1. **`in_interval(id, start, end, inclusive_right=True)`** — Check if `id` falls within the interval `(start, end]` (or `(start, end)`) on the ring, handling wraparound.
2. **`find_successor(id)`** — Find the successor node for a given identifier.
3. **`closest_preceding_node(id)`** — Scan the finger table to find the closest preceding node.
4. **`create()`** — Create a new Chord ring with this node as the only member.
5. **`join(existing_node_addr)`** — Join an existing Chord ring via a known node.
6. **`stabilize()`** — Verify this node's immediate successor and notify it.
7. **`notify(node_addr)`** — Handle notification from a potential predecessor.
8. **`fix_fingers()`** — Refresh one finger table entry per call.

> **Note**: The stabilization protocol (`stabilize`, `fix_fingers`) is called manually in the test suite. In a real system, these would run periodically in the background.

### Part 2: Key Storage and Retrieval (4 + 2 points)

9. **`hash_key(key)`** — Hash a string key to an identifier in `[0, 2^m - 1]`. Use `hashlib` (e.g. SHA-1) and take modulo `2^m`.
10. **`put(key, value)`** — Store a key-value pair in the DHT by routing to the responsible node.
11. **`get(key)`** — Retrieve a value from the DHT by routing to the responsible node.
12. **`transfer_keys(new_node_addr)`** — Transfer keys to a newly joined node that is now responsible for them.

### Part 3: Failure Recovery (Bonus, 2 points)

13. **`check_predecessor()`** — Check if the predecessor has failed; if so, set it to `None`.

    The original Chord paper suggests maintaining a **successor-list** for fault tolerance. You may create additional helper methods as needed. `check_predecessor()` is called manually in the test suite to simulate periodic execution.

    > **Note**: Key replication for storage recovery is out of scope for this assignment.

## Testing

A comprehensive test suite is provided in `test_dht.py`. **Do not modify this file.** The test suite verifies:

| Test Function                    | What it tests                                        |
|----------------------------------|------------------------------------------------------|
| `create_chord_network`           | Ring creation, join, stabilization, finger tables    |
| `test_chord_key_storage`         | Key-value storage and retrieval from all nodes       |
| `test_edge_cases`                | Non-existent keys, duplicate key overwrites          |
| `test_key_transfer_with_new_node`| Key redistribution when a new node joins             |
| `test_node_failure_recovery`     | Finger table repair after a node failure (bonus)     |

To run:

```bash
python test_dht.py
```

Save the output to a file:

```bash
python test_dht.py > output_dht.txt 2>&1
```

## References

Stoica, I., Morris, R., Karger, D., Kaashoek, M. F., & Balakrishnan, H. (2001). Chord: A scalable peer-to-peer lookup service for internet applications. _ACM SIGCOMM Computer Communication Review_, 31(4), 149-160.

## Submission Guidelines

Submit the following files to your GitHub Classroom repository:

1. **`chord_node.py`** — Your completed implementation.
2. **`output_dht.txt`** — Test results from running `python test_dht.py`.
3. **A report in `.md` (Markdown) format** — See grading criteria below.

## Grading Criteria

| Component | Points | Requirements |
|-----------|--------|--------------|
| **Basic Chord Protocol** | 4 | Pass `create_chord_network` tests. Correct ring creation, stabilization, and finger table setup. Manual inspection of finger table correctness and routing behavior. |
| **Key Storage and Retrieval** | 4 | Pass `test_chord_key_storage` and `test_edge_cases`. Correct key-value storage, retrieval, and handling of non-existent / duplicate keys. |
| **Key Transfers** | 2 | Pass `test_key_transfer_with_new_node`. Correct transfer of responsibility and key redistribution after a new node joins. |
| **Implementation Report** | 2 | Brief explanation of each function: `find_successor`, `closest_preceding_node`, `create`, `join`, `stabilize`, `notify`, `fix_fingers`, `put`, `get`, `transfer_keys` (0.2 pts each). |
| **Failure Recovery (Bonus)** | +2 | Pass `test_node_failure_recovery`. Correctly detect node failure, update predecessor/finger tables, and maintain network stability. |

> **Note**: Bonus points will be added to your assignment score, but the total score for all assignments (including bonus) cannot exceed 60 points (60% of the final grade).

Good luck, and enjoy implementing your distributed hash table!