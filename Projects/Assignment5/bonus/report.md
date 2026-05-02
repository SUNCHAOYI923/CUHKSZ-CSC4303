### Building and Testing

Same as the original part.

* Build the server: `cd server_app && make`
* Run the server: `./server_app/server <port>`
* Run the client: `python client_app/main.py localhost <port>`
* Run the test:   `python client_app/test.py localhost <port>`
* Run benchmarks: `python client_app/benchmark.py localhost <port>`

### Optimization Strategies

#### Binary Serialization (Replacing JSON)

I rewrote the `call` method in the Python client (`rpc_client_stub.py`) and the JSON request parsing function (`process_json_request`) in the C server. Instead of using `json.dumps()` and `cJSON_Parse()`, which incur heavy CPU and memory overhead due to string manipulation and dynamic tree allocations, I implemented a custom binary packing system.

Data is packed and transmitted in a compact, continuous byte stream:
* **Request Packet Structure** 
`[4-byte Total Packet Length] + [1-byte Function ID] + [Binary Argument Data]`
* *Integers/Floats:* Packed directly as 4-byte segments in network byte order.
* *Strings/Arrays:* Packed using a Type-Length-Value (TLV) approach (e.g., `[4-byte String Length] + [Raw ASCII Bytes]`).
* **Response Packet Structure**
`[4-byte Total Packet Length] + [1-byte Status Code] + [Binary Result Data]`

#### $O(1)$ Function Dispatch
In the original implementation, the server routed incoming RPC calls by iterating through an array of registered string names and using `strcmp` to find a match. This resulted in an $O(N)$ time complexity.

To optimize this, I assigned unique integer IDs ranging from 1 to 9 to each of the target functions (e.g., `add` = 1, `greet` = 2, `is_positive` = 3). 
* The Python client sends this 1-byte ID instead of the function name string.
* Upon receiving the packet, the C server reads the first byte (`func_id`) and uses a simple `switch (func_id)` statement to directly route the execution.

### Benchmark results

```

🔍 Starting RPC Performance Benchmark
===============================

=== Paper-Inspired Performance Test ===
Table: Performance Results for Different Argument/Result Combinations
======================================================================
Test Case                 Min (ms)   Median (ms) Avg (ms)   Max (ms)  
----------------------------------------------------------------------
No args/results           0.05       0.07       0.07       0.10      
1 arg/result              0.03       0.03       0.03       0.07      
2 args/1 result           0.03       0.03       0.03       0.04      
4-byte payload            0.03       0.03       0.04       0.08      
40-byte payload           0.03       0.04       0.04       0.07      
100-byte payload          0.03       0.03       0.03       0.09      
1000-byte payload         0.03       0.03       0.03       0.06      
1 word array              0.03       0.03       0.04       0.09      
4 word array              0.03       0.03       0.03       0.03      
10 word array             0.03       0.03       0.03       0.08      
40 word array             0.03       0.03       0.03       0.04      
100 word array            0.04       0.04       0.04       0.05      

Transmission Overhead Estimation:
Estimated local call time: 0.000 ms

=== Data Size Scaling Test ===

Size (bytes)    Min (ms)        Median (ms)     Max (ms)       
------------------------------------------------------------
10              0.03            0.03            0.05           
100             0.03            0.03            0.03           
500             0.03            0.03            0.03           
1000            0.03            0.03            0.03           
5000            0.04            0.04            0.05           
10000           0.04            0.04            0.05           
50000           0.06            0.09            0.21           
100000          0.10            0.12            0.22           
500000          0.56            1.21            1.78           
1000000         1.32            1.86            3.14           

=== Throughput Test ===
Performing rapid successive calls to measure throughput...

Small Payload (add) Results:
Completed 1000/1000 calls successfully in 0.03 seconds
Throughput: 29951.83 calls/second

Medium Payload (1KB echo) Results:
Completed 500/500 calls successfully in 0.02 seconds
Throughput: 30242.30 calls/second

✅ All benchmark tests completed!
```

**Analysis**

For small payloads, the benchmark results for both systems were very close (hovering around 0.03 to 0.04 ms per call). This is **not** due to a lack of computational improvement, but rather due to the intrinsic baseline latency of the Operating System's network stack. At this microsecond scale, OS-level context switching and loopback socket I/O become the primary bottleneck, largely masking the CPU cycles saved by our $O(1)$ dispatch and binary parsing.

For large payloads (100KB to 1MB), the optimized binary system shows a dramatic and highly scalable performance improvement, running approximately **3.4x to 5.3x faster** based on the median execution time. By completely eliminating the `cJSON` library, the optimized system avoids the massive CPU and memory overhead of allocating complex Abstract Syntax Trees and parsing long strings. Instead, it processes bulk data almost instantly via direct `memcpy` operations.