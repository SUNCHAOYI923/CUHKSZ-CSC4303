# client_app/benchmark.py
import time
import statistics
import sys
import os

# Add the rpc_lib directory to the Python path
# This allows importing modules from rpc_lib without needing to install it as a package
script_dir = os.path.dirname(
    os.path.abspath(__file__)
)  # Path to current script (main.py)
rpc_lib_path = os.path.abspath(os.path.join(script_dir, "..", "rpc_lib", "python"))
sys.path.insert(0, rpc_lib_path)

from rpc_client_stub import RPCClient
from rpc_exceptions import (
    RPCError,
    ConnectionError,
    FunctionNotFoundError,
    ExecutionError,
)


def test_basic_functionality(host, port):
    """Test basic RPC functionality with various data types."""
    print("\n=== Basic Functionality Test ===")
    with RPCClient(host, port) as client:
        # Test integer addition
        result = client.call("add", 42, 58)
        assert result == 100, f"add(42, 58) returned {result}, expected 100"
        print("✓ Integer addition works")

        # Test string operation
        result = client.call("greet", "World")
        assert (
            result == "Hello, World!"
        ), f"greet('World') returned {result}, expected 'Hello, World!'"
        print("✓ String operation works")

        # Test boolean return
        result = client.call("is_positive", 5)
        assert result is True, f"is_positive(5) returned {result}, expected True"
        result = client.call("is_positive", -5)
        assert result is False, f"is_positive(-5) returned {result}, expected False"
        print("✓ Boolean return works")

        # Test void function
        result = client.call("no_return")
        assert result is None, f"no_return() returned {result}, expected None"
        print("✓ Void function works")

        print("All basic functionality tests passed!")


def test_argument_validation(host, port):
    """Test how the RPC system handles incorrect argument scenarios."""
    print("\n=== Argument Validation Test ===")
    with RPCClient(host, port) as client:
        # Test too many arguments
        try:
            client.call("add", 1, 2, 3, 4, 5)  # add expects only 2 arguments
            print("❌ Failed to catch too many arguments")
        except ExecutionError:
            print("✓ Correctly caught too many arguments")
        except Exception as e:
            print(f"❌ Wrong exception type for too many arguments: {type(e).__name__}")

        # Test too few arguments
        try:
            client.call("add")  # Missing both arguments
            print("❌ Failed to catch missing arguments")
        except ExecutionError:
            print("✓ Correctly caught missing arguments")
        except Exception as e:
            print(f"❌ Wrong exception type for missing arguments: {type(e).__name__}")

        # Test wrong argument types
        try:
            client.call("add", "string", True)  # Wrong types
            print("❌ Failed to catch wrong argument types")
        except ExecutionError:
            print("✓ Correctly caught wrong argument types")
        except Exception as e:
            print(
                f"❌ Wrong exception type for wrong argument types: {type(e).__name__}"
            )

        # Test negative case with is_positive (valid but returns false)
        try:
            result = client.call("is_positive", -10)
            assert result is False, f"Expected False, got {result}"
            print("✓ Correctly handled negative value for is_positive")
        except Exception as e:
            print(f"❌ Failed with valid negative argument: {e}")

        # Test float when int expected
        try:
            client.call(
                "add", 1.5, 2.5
            )  # Should convert or error based on implementation
            print("✓ Handled float arguments for add")
        except ExecutionError:
            print("✓ Correctly rejected float arguments for add")
        except Exception as e:
            print(f"❌ Wrong exception type for float arguments: {type(e).__name__}")


def test_error_handling(host, port):
    """Test how the RPC system handles various errors."""
    print("\n=== Error Handling Test ===")
    with RPCClient(host, port) as client:
        # Test function not found
        try:
            client.call("non_existent_function")
            print("❌ Failed to catch non-existent function")
        except FunctionNotFoundError:
            print("✓ Correctly caught FunctionNotFoundError")
        except Exception as e:
            print(f"❌ Wrong exception type: {type(e).__name__}")

        # Test invalid arguments
        try:
            client.call("add", "not_a_number", 5)
            print("❌ Failed to catch invalid argument type")
        except ExecutionError:
            print("✓ Correctly caught ExecutionError for invalid argument")
        except Exception as e:
            print(f"❌ Wrong exception type: {type(e).__name__}")

        # Test division by zero
        try:
            client.call("divide", 10, 0)
            print("❌ Failed to catch division by zero")
        except ExecutionError:
            print("✓ Correctly caught ExecutionError for division by zero")
        except Exception as e:
            print(f"❌ Wrong exception type: {type(e).__name__}")


def test_reconnection(host, port):
    """Test client's ability to reconnect after a disconnect."""
    print("\n=== Reconnection Test ===")

    # First connection
    client = RPCClient(host, port)
    client.connect()

    try:
        result = client.call("add", 5, 7)
        print(f"✓ First connection successful: add(5, 7) = {result}")

        # Disconnect manually
        print("Disconnecting client...")
        client.disconnect()

        # Try to call after disconnect - should fail
        try:
            client.call("add", 1, 2)
            print("❌ Call succeeded when disconnected")
        except ConnectionError:
            print("✓ Correctly failed when disconnected")

        # Reconnect and try again
        print("Reconnecting client...")
        client.connect()
        result = client.call("add", 10, 20)
        print(f"✓ Reconnection successful: add(10, 20) = {result}")

    finally:
        client.disconnect()


def test_complex_data(host, port):
    """Test handling of more complex data structures."""
    print("\n=== Complex Data Test ===")
    with RPCClient(host, port) as client:
        # Test array handling
        try:
            numbers = [1, 2, 3, 4, 5]
            result = client.call("sum_array", numbers)
            print(f"✓ Array handling works: sum_array({numbers}) = {result}")
            assert result == 15, f"Expected 15, got {result}"
        except Exception as e:
            print(f"❌ Array test failed: {e}")

        # Test object/dict handling
        try:
            person = {"name": "Test User", "age": 30, "is_student": True}
            result = client.call("process_person", person)
            print(f"✓ Object handling works: {result}")
            assert "Test User" in result, f"Expected name in result, got {result}"
            assert "30" in result, f"Expected age in result, got {result}"
        except Exception as e:
            print(f"❌ Object test failed: {e}")

        # Test nested structures
        try:
            names = ["Alice", "Bob", "Charlie"]
            result = client.call("get_greetings", names)
            print(f"✓ Complex return handling works: {result}")
            assert len(result) == 3, f"Expected 3 items, got {len(result)}"
            assert "Hello, Alice!" in result, f"Missing greeting for Alice in {result}"
        except Exception as e:
            print(f"❌ Complex return test failed: {e}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
        if not (0 <= port <= 65535):
            raise ValueError("Port number must be between 0 and 65535")
    except ValueError:
        print("Invalid port number.")
        sys.exit(1)

    """Run all benchmark tests."""
    print("\n🔍 Starting RPC Benchmark Tests")
    print("===============================")

    try:
        test_basic_functionality(host, port)
        test_argument_validation(host, port)
        test_error_handling(host, port)
        test_reconnection(host, port)
        test_complex_data(host, port)

        print("\n✅ All benchmark tests completed!")
    except ConnectionError as e:
        print(f"\n❌ Benchmark failed: Could not connect to server: {e}")
    except Exception as e:
        print(f"\n❌ Benchmark failed with unexpected error: {e}")


if __name__ == "__main__":
    main()
