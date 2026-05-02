[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DADXlkHR)
# CSC4303 Assignment 5: JSON RPC Library (12 + 3 points)

### Deadline: April 10, 23:59

### Name: Chaoyi, Sun

### Student ID: 124090550

## Overview

In this assignment, you will implement a minimal custom Remote Procedure Call (RPC) library from scratch. The assignment involves using **JSON** for message formatting over TCP sockets. This includes implementing server and client stubs to enable communication between a C server and a Python client using JSON messages. Optional credits are given if you can optimize the RPC performance.

The goal is to understand the fundamental components of an RPC system (stubs, dispatch, network communication, error handling) using a common serialization format.

## Directory Structure
```
.
├── README.md # This file
├── rpc_lib/ # Core library components (You will implement parts here)
│ ├── c/ # C Server Library Parts
│ │ ├── include/
│ │ │ ├── cJSON.h # cJSON library header
│ │ │ ├── rpc_connection.h # Handles socket connection and length-prefixing
│ │ │ └── rpc_server_stub.h # Declares RPC Server functions (JSON-based)
│ │ ├── src/
│ │ │ ├── cJSON.c # cJSON library
│ │ │ ├── rpc_connection.c # Implements Connection functions
│ │ │ └── rpc_server_stub.c # Implements RPC Server functions (JSON-based)
│ └── python/ # Python Client Library Parts
│ │ └── rpc_client_stub.py # Implements Python RPCClient class (JSON-based)
│ └──── rpc_exceptions.py # Defines custom Python exceptions
├── server_app/ # Example Server Application (Uses rpc_lib)
│ ├── Makefile
│ ├── main.c # Uses cJSON, registers functions with wrappers
│ ├── functions.h # Declares C functions with basic types
│ └── functions.c # Implements C functions with basic types
│── client_app/ # Example Client Application (Uses rpc_lib)
│ ├── main.py # Uses json module
│ ├── benchmark.py
└─└── test.py
```

## Task: Implementation (9 points)

Your primary goal is to implement the core JSON-based RPC components. Each file contains detailed TODO comments to guide your implementation.

You should ensure the security of the program while realizing the functions. Failing to do so (for example, memory leak or overflow) will result in point deductions.

You should not use any other external libraries or packages. Use only the libraries or packages already included or imported. Otherwise, you will get a 0 on this assignment.

Hint: You can implement the Python part first before implementing the C part. It is much easier and make you better understand the exceptions that needed to be implemented.

1. **Understand the JSON Protocol**
   * Familiarize yourself with the JSON request/response formats.
   * Request: `{"function": "<name>", "args": [arg1, arg2, ...]}`
   * Response (Success): `{"status": "success", "result": <value>}`
   * Response (Error): `{"status": "error", "message": "<error_string>"}`
   * JSON Library: cJSON. Read the document before starting: https://github.com/DaveGamble/cJSON/

2. **Implement C Connection Handling (2 points)**
   * Complete the `rpc_connection.c` file (3 TODOs) with socket I/O functionality
   * Implement data sending/receiving with proper error handling
   * Handle connection lifecycle (opening, closing, state management)

3. **Implement C Server Stub (3 points)**
   * Complete the `rpc_server_stub.c` file (4 TODOs) to process RPC requests
   * Implement function registration, lookup, and invocation
   * Handle JSON parsing/generation and error conditions

4. **Implement Python Client Stub (3 points)**
   * Complete the `rpc_client_stub.py` file (6 TODOs) to make RPC calls
   * Implement JSON serialization/deserialization of requests/responses
   * Handle socket communication and error propagation

5. **Implement the Server Application (1 points)**
   * Complete the 9 TODOs in `server_app/main.c` 
   * Implement function registrations
   * Return NULL pointer when there is any execution error.

## Task: Report (3 points)
Submit a `report.md` file describing your understanding of the JSON RPC system design (2 points) and presenting benchmark results obtained by running `benchmark.py` (1 point).

## Building and Testing

* Build the server: `cd server_app && make`
* Run the server: `./server_app/server <port>`
* Run the client: `python client_app/main.py localhost <port>`
* Run the test:   `python client_app/test.py localhost <port>`
* Run benchmarks: `python client_app/benchmark.py localhost <port>`

## Bonus: Optimizing the RPC System (3 points)

For extra credit, implement and evaluate performance optimizations for your RPC system. Some ideas:

* Replace JSON with a binary protocol for more efficient serialization
* Optimize function dispatch with faster lookup mechanisms
* Implement other performance improvements

Requirements:
* Create a `/bonus` directory containing all code for your optimized system. This should be a separate implementation; **DO NOT modify your original submission.**
* The `/bonus` directory must also include a `report.md` file detailing your optimization strategies and presenting benchmark results obtained by running `benchmark.py` comparing the original and optimized systems.
* Instructions for running your optimized RPC system must also be included in the `report.md`.
* Bonus points will be added to your assignment score, but the total score for all assignments (including bonus points) cannot exceed 60 points (60% of the final grade).

---
Good luck, have fun!

Author: Fang Zihao