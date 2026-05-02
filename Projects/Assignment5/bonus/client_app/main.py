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

    try:
        # Using a context manager (with statement) is recommended for automatic connection handling
        with RPCClient(host, port) as client:
            # --- Basic Data Types ---
            result1 = client.call("add", 10, 5)
            print(f"add(10, 5) = {result1}")  # Expected: 15

            result2 = client.call("greet", "World")
            print(f"greet('World') = {result2}")  # Expected: "Hello, World!"

            result3 = client.call("is_positive", -2.5)
            print(f"is_positive(-2.5) = {result3}")  # Expected: False

            result4 = client.call("echo", "This is a test string.")
            print(f"echo(...) = {result4}")

            # Example of calling a function that returns void (None)
            result5 = client.call("no_return")
            print(f"no_return() = {result5}")

            # Example of calling a non-existent function
            # We catch the broader RPCError here, as the client stub might raise
            # FunctionNotFoundError or ExecutionError depending on the server message.
            try:
                client.call("nonexistent_function", 1, 2, 3)
            except FunctionNotFoundError as e:
                print(f"Expected error: {e}")

            # Example of triggering a server-side execution error
            try:
                client.call(
                    "divide", 10, 0
                )  # Assuming 'divide' is registered and throws on division by zero
            except ExecutionError as e:
                print(f"Expected error: {e}")

            # --- Complex Data Types ---
            print("\n--- Complex Types ---")
            try:
                # Example: Sum an array of integers
                numbers_to_sum = [1, 2, 3, 4, 5, -1]
                sum_result = client.call("sum_array", numbers_to_sum)
                print(f"sum_array({numbers_to_sum}) = {sum_result}")  # Expected: 14

                # Example: Process a person object (dictionary)
                person_obj = {"name": "Alice", "age": 30, "is_student": False}
                person_result = client.call("process_person", person_obj)
                print(f"process_person({person_obj}) = {person_result}")

                # Example: Get greetings for a list of names
                names_list = ["Bob", "Charlie"]
                greetings_list = client.call("get_greetings", names_list)
                print(f"get_greetings({names_list}) = {greetings_list}")

            except RPCError as e:
                print(f"Error during bonus calls: {e}")

    except ConnectionError as e:
        print(f"Connection error: {e}")
    except RPCError as e:
        print(f"RPC error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
