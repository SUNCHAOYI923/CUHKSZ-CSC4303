from chord_node import Node
import time
import random

# Global list to track all created nodes for cleanup
all_created_nodes = []

def print_fingers(nodes):
    print("=========================")
    for node in nodes:
        print(f"NODE {node.node_id} FINGER:")
        for finger_addr in node.finger[1:]:
            if finger_addr:
                finger_id, finger_host, finger_port = finger_addr
                print(f"  - {finger_id} at {finger_host}:{finger_port}")
    print("=========================")

def create_chord_network():
    """Test basic DHT operations with a small ring."""
    print("=== Creating Chord Network ===")
    node1 = Node(1, "127.0.0.1", 5001, m=5)
    node1.create()
    all_created_nodes.append(node1)
    print(f"Created node {node1.node_id}")

    # Add more nodes
    nodes = [node1]
    for i, node_id in enumerate([8, 15, 23], start=2):
        node = Node(node_id, "127.0.0.1", 5000 + i, m=5)
        # Pass the address tuple of the existing node
        node.join((node1.node_id, node1.host, node1.port))
        nodes.append(node)
        all_created_nodes.append(node)
        print(f"Node {node_id} joined")
        time.sleep(1)  # Allow time for join

    # Stabilize the ring: Simulate periodic stabilization protocol
    print("\nStabilizing ring...")
    for _ in range(10):
        for node in nodes:
            node.stabilize()
            node.fix_fingers()
        time.sleep(1)
    print_fingers(nodes)

    return nodes

def test_chord_key_storage(nodes):
    """Test key storage, retrieval, and distribution in Chord."""
    print("\n=== Testing Chord Key Storage and Retrieval ===")
    
    # Store multiple key-value pairs
    test_data = {
        f"key{i}": f"value{i}" for i in range(20)
    }
    
    print("\nStoring key-value pairs in the Chord network:")
    for key, value in test_data.items():
        # Store from random nodes to test routing
        node = random.choice(nodes)
        success = node.put(key, value)
        print(f"Storing {key}: {value} from node {node.node_id} - {'Success' if success else 'Failed'}")

    # Display key distribution across nodes
    print("\nCurrent key distribution across nodes:")
    for node in nodes:
        print(f"Node {node.node_id} data: {node.data}")

    # Test retrieval from every node for every key
    print("\nTesting retrieval of all keys from all nodes:")
    all_successful = True
    for key, expected_value in test_data.items():
        print(f"\nTesting retrieval of key: {key}")
        for node in nodes:
            retrieved_value = node.get(key)
            success = retrieved_value == expected_value
            all_successful &= success
            print(f"  Node {node.node_id}: {'Success' if success else 'Failed'} "
                    f"(got: {retrieved_value}, expected: {expected_value})")

    print(f"\nAll retrieval tests: {'Success' if all_successful else 'Failed'}")

    return test_data

def test_edge_cases(nodes):
    """Test various edge cases."""
    print("\n=== Testing Edge Cases ===")

    # Test 1: Non-existent keys
    print("\nTesting non-existent keys:")
    result = nodes[0].get("nonexistent_key")
    print(f"Get non-existent key: {'Success' if result is None else 'Failed'}")

    # Test 2: Duplicate keys
    print("\nTesting duplicate keys:")
    duplicate_key = "duplicate_key"
    value1 = "value1"
    value2 = "value2"

    nodes[0].put(duplicate_key, value1)
    nodes[0].put(duplicate_key, value2)  # Inserting the duplicate
    retrieved_value = nodes[0].get(duplicate_key)
    print(f"Duplicate key test (overwrite): {'Success' if retrieved_value == value2 else 'Failed'}")

def test_key_transfer_with_new_node(nodes):
    """Test key transfers when a new node joins an existing network with data."""
    print("\n=== Testing Key Transfer with New Node ===")
    
    # Store some initial data across the existing nodes
    initial_data = {
        f"transfer_key{i}": f"transfer_value{i}" for i in range(10)
    }
    
    print("\nStoring initial data:")
    for key, value in initial_data.items():
        nodes[0].put(key, value)
        print(f"Stored {key}: {value}")
    
    # Print current data distribution
    print("\nInitial data distribution:")
    for node in nodes:
        print(f"Node {node.node_id} data: {node.data}")
    
    # Create a new node and join via a node other than node1
    new_node_id = 30
    node2 = nodes[2]
    print(f"\nCreating new node {new_node_id} and joining via node {node2.node_id}")
    new_node = Node(new_node_id, "127.0.0.1", 5010, m=5)
    all_created_nodes.append(new_node)

    # Join via a different node (nodes[2] instead of nodes[0])
    # Pass the address tuple
    new_node.join((node2.node_id, node2.host, node2.port))
    print(f"Node {new_node_id} joined")
    
    # Allow time for key transfer and stabilization
    print("\nStabilizing ring after new node joined...")
    all_nodes = nodes + [new_node]
    for _ in range(10):
        for node in all_nodes:
            node.stabilize()
            node.fix_fingers()
        time.sleep(1)
    
    # Print updated data distribution
    print("\nData distribution after new node joined:")
    for node in all_nodes:
        print(f"Node {node.node_id} data: {node.data}")
    
    # Verify all keys are still accessible
    print("\nVerifying all keys are still accessible after transfer:")
    all_accessible = True
    for key, expected_value in initial_data.items():
        # Try getting from the new node to test routing
        retrieved_value = new_node.get(key)
        success = retrieved_value == expected_value
        all_accessible &= success
        print(f"Key {key}: {'Success' if success else 'Failed'} (got: {retrieved_value})")
    
    print(f"\nAll keys accessible after transfer: {'Success' if all_accessible else 'Failed'}")
    
    return all_nodes

def test_node_failure_recovery(nodes):
    """Test finger table maintenance after node failure."""
    print("\n=== Testing Node Failure Recovery ===")
    
    # Print initial finger tables
    print("\nInitial finger tables:")
    print_fingers(nodes)
    
    # Select a node to fail (nodes[2])
    failing_node = nodes[2]
    print(f"\nSimulating failure of node {failing_node.node_id}")
    
    # Store failing node's address before stopping it
    failing_node_addr = (failing_node.node_id, failing_node.host, failing_node.port)
    
    # Stop the failing node's server AND mark it as stopped
    failing_node.stop()
    print(f"Stopped server for node {failing_node.node_id}")
    
    # Now run check_predecessor
    print("\nRunning check_predecessor on remaining nodes...")
    remaining_nodes = [n for n in nodes if n != failing_node]
    for node in remaining_nodes:
        if node.predecessor and node.predecessor[0] == failing_node.node_id:
            print(f"Node {node.node_id} checking failed predecessor {failing_node.node_id}")
            node.check_predecessor() # Simulate periodic call of check_predecessor
            pred_id = node.predecessor[0] if node.predecessor else None
            print(f"Node {node.node_id} predecessor is now {pred_id}")
    
    # Run stabilize to repair finger tables
    print("\nStabilizing remaining nodes...")
    for _ in range(10):
        for node in remaining_nodes:
            node.stabilize()
            node.fix_fingers()
        time.sleep(0.5)
    
    # Print final finger tables
    print("\nFinger tables after recovery:")
    print_fingers(remaining_nodes)
    
    return remaining_nodes

def main():
    try:
        # Create initial network
        nodes = create_chord_network()

        # Run existing tests
        test_chord_key_storage(nodes)
        test_edge_cases(nodes)

        # Run new tests
        all_nodes = test_key_transfer_with_new_node(nodes)

        print("\n=== All tests completed ===")

        test_node_failure_recovery(all_nodes)

        print("\n=== Failure recovery success ===")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        # Clean up - stop all nodes that were created during the test
        print("\nShutting down all nodes...")
        for node in all_created_nodes:
            if not node.stopped:
                node.stop()
        print("\nTest suite finished")

if __name__ == "__main__":
    main()