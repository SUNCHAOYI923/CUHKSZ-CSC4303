# client_app/benchmark.py
import time
import statistics
import sys
import os
import socket

# Add the rpc_lib directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
rpc_lib_path = os.path.abspath(os.path.join(script_dir, "..", "rpc_lib", "python"))
sys.path.insert(0, rpc_lib_path)

from rpc_client_stub import RPCClient
from rpc_exceptions import (
    RPCError,
    ConnectionError,
    FunctionNotFoundError,
    ExecutionError,
)


def test_paper_inspired_performance(host, port):
    """Test RPC performance with scenarios inspired by the RPC paper."""
    print("\n=== Paper-Inspired Performance Test ===")

    with RPCClient(host, port) as client:
        # Warmup
        for _ in range(10):
            client.call("add", 1, 1)

        # Table for results
        print("Table: Performance Results for Different Argument/Result Combinations")
        print("=" * 70)
        print(
            "{:<25} {:<10} {:<10} {:<10} {:<10}".format(
                "Test Case", "Min (ms)", "Median (ms)", "Avg (ms)", "Max (ms)"
            )
        )
        print("-" * 70)

        # Test cases
        test_cases = [
            ("no_return", [], "No args/results"),
            ("is_positive", [5], "1 arg/result"),
            ("add", [5, 10], "2 args/1 result"),
            ("echo", ["x" * 4], "4-byte payload"),
            ("echo", ["x" * 40], "40-byte payload"),
            ("echo", ["x" * 100], "100-byte payload"),
            ("echo", ["x" * 1000], "1000-byte payload"),
            ("sum_array", [[1]], "1 word array"),
            ("sum_array", [[1, 2, 3, 4]], "4 word array"),
            ("sum_array", [list(range(10))], "10 word array"),
            ("sum_array", [list(range(40))], "40 word array"),
            ("sum_array", [list(range(100))], "100 word array"),
        ]

        iterations = 25

        for function, args, label in test_cases:
            latencies = []

            for _ in range(iterations):
                start_time = time.time()
                result = client.call(function, *args)
                latency = (time.time() - start_time) * 1000  # ms
                latencies.append(latency)

            # Calculate statistics
            min_latency = min(latencies)
            max_latency = max(latencies)
            avg_latency = sum(latencies) / len(latencies)
            median_latency = statistics.median(latencies)

            print(
                "{:<25} {:<10.2f} {:<10.2f} {:<10.2f} {:<10.2f}".format(
                    label, min_latency, median_latency, avg_latency, max_latency
                )
            )

        # Compare with local operation (approximate)
        print("\nTransmission Overhead Estimation:")
        local_start = time.time()
        for _ in range(1000):
            # Simulate local function call
            sum(range(40))
        local_time = (time.time() - local_start) * 1000 / 1000  # ms per call
        print(f"Estimated local call time: {local_time:.3f} ms")


def test_data_size_scaling(host, port):
    """Test how performance scales with increasing data sizes."""
    print("\n=== Data Size Scaling Test ===")

    with RPCClient(host, port) as client:
        # Warmup
        for _ in range(5):
            client.call("echo", "warmup")

        # Data sizes to test (in bytes)
        data_sizes = [10, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]

        # Measure performance for each size
        print(
            "\n{:<15} {:<15} {:<15} {:<15}".format(
                "Size (bytes)", "Min (ms)", "Median (ms)", "Max (ms)"
            )
        )
        print("-" * 60)

        for size in data_sizes:
            # Create test data - string of specified size
            test_data = "x" * size

            # Iterations - fewer for larger sizes
            iterations = max(3, min(20, int(10000 / max(size, 1))))

            latencies = []

            for _ in range(iterations):
                start_time = time.time()
                result = client.call("echo", test_data)
                latency = (time.time() - start_time) * 1000
                latencies.append(latency)

                # Validate result
                if len(result) != size:
                    print(f"Warning: Result size mismatch: {len(result)} != {size}")

            # Calculate statistics
            min_latency = min(latencies)
            max_latency = max(latencies)
            median_latency = statistics.median(latencies)

            # Print results
            print(
                "{:<15} {:<15.2f} {:<15.2f} {:<15.2f}".format(
                    size, min_latency, median_latency, max_latency
                )
            )


def test_throughput(host, port):
    """Test maximum throughput of the RPC system."""
    print("\n=== Throughput Test ===")

    with RPCClient(host, port) as client:
        print("Performing rapid successive calls to measure throughput...")

        # Small payload test (add)
        iterations = 1000
        start_time = time.time()
        success_count = 0

        for i in range(iterations):
            try:
                result = client.call("add", i, i)
                if result == i * 2:
                    success_count += 1
            except Exception as e:
                pass  # Count failures by omission

        total_time = time.time() - start_time

        print(f"\nSmall Payload (add) Results:")
        print(
            f"Completed {success_count}/{iterations} calls successfully in {total_time:.2f} seconds"
        )
        print(f"Throughput: {success_count/total_time:.2f} calls/second")

        # Medium payload test (echo 1KB)
        iterations = 500
        payload = "x" * 1000
        start_time = time.time()
        success_count = 0

        for i in range(iterations):
            try:
                result = client.call("echo", payload)
                if len(result) == 1000:
                    success_count += 1
            except Exception as e:
                pass

        total_time = time.time() - start_time

        print(f"\nMedium Payload (1KB echo) Results:")
        print(
            f"Completed {success_count}/{iterations} calls successfully in {total_time:.2f} seconds"
        )
        print(f"Throughput: {success_count/total_time:.2f} calls/second")


def main():
    if len(sys.argv) != 3:
        print("Usage: python benchmark.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
        if not (0 <= port <= 65535):
            raise ValueError("Port number must be between 0 and 65535")
    except ValueError:
        print("Invalid port number.")
        sys.exit(1)

    print("\n🔍 Starting RPC Performance Benchmark")
    print("===============================")

    try:
        # Run the paper-inspired performance tests
        test_paper_inspired_performance(host, port)

        # Run data size scaling test
        test_data_size_scaling(host, port)

        # Run throughput test
        test_throughput(host, port)

        print("\n✅ All benchmark tests completed!")
    except ConnectionError as e:
        print(f"\n❌ Benchmark failed: Could not connect to server: {e}")
        print(f"   Make sure the server is running on {host}:{port}")
    except Exception as e:
        print(f"\n❌ Benchmark failed with unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
