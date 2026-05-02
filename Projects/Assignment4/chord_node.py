import socket
import threading
import hashlib
import json
import time
import math

class Node:
    def __init__(self, node_id, host, port, m=5):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.m = m  # number of bits in the identifier space
        self.max_id = 2 ** m  # size of the identifier ring (e.g. 32 for m=5)
        self.predecessor = None  # (node_id, host, port) tuple or None
        self.successor = (node_id, host, port)  # initially points to self
        # Finger table: indices 1..m; finger[i] stores the successor of (node_id + 2^(i-1)) mod 2^m
        self.finger = [None] * (m + 1)
        for i in range(1, m + 1):
            self.finger[i] = (node_id, host, port)
        self.next = 1  # index of the next finger to fix
        self.data = {}  # local key-value storage
        self.running = True  # server control flag
        self.stopped = False  # whether the node has been stopped

        # Initialize the server socket before starting the thread
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Start the TCP server thread
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    # ========================================================================
    # Helper Methods (provided)
    # ========================================================================

    def in_interval(self, id, start, end, inclusive_right=True):
        """
        Check if 'id' falls within an interval on the Chord ring.

        By default checks the half-open interval (start, end].
        Set inclusive_right=False to check the open interval (start, end).

        Must handle ring wraparound (e.g. when start > end).

        Args:
            id: The identifier to check
            start: Start of the interval (exclusive)
            end: End of the interval
            inclusive_right: If True, check (start, end]; if False, check (start, end)

        Returns:
            True if id is in the interval, False otherwise
        """
        # TODO: Implement interval check, considering ring wraparound
        if start == end :
            return inclusive_right or id != start
        if start <= end : 
            if inclusive_right : return start < id <= end 
            else : return start < id < end
        else :
            if inclusive_right : return id > start or id <= end
            else : return id > start or id < end

    # ========================================================================
    # Core Chord Protocol (Section 1)
    # ========================================================================

    def find_successor(self, id):
        """
        Find the successor node responsible for a given identifier.

        This is the core lookup operation of Chord. It should:
        1. Check if 'id' falls in (self.node_id, self.successor], if so return self.successor
        2. Otherwise, find the closest preceding node and ask it to continue the search

        Hint: Use self.in_interval(), self.closest_preceding_node(), and self.remote_call().

        Args:
            id: The identifier to find successor for

        Returns:
            (node_id, host, port) of the successor
        """
        # TODO: Implement this method
        if self.in_interval (id, self.node_id, self.successor[0]) : return self.successor
        u = self.closest_preceding_node (id)
        if u[0] == self.node_id: return self.successor
        try :
            res = self.remote_call (u, "find_successor", {"id" : id})
            return res if res else self.successor
        except Exception : return self.successor

    def closest_preceding_node(self, id):
        """
        Find the closest preceding node for a given identifier by scanning the finger table.

        Search the finger table from index m down to 1. Return the first finger
        whose node_id falls in the open interval (self.node_id, id).

        Args:
            id: The identifier to find closest preceding node for

        Returns:
            (node_id, host, port) of the closest preceding node, or self's address if none found
        """
        # TODO: Implement this method
        for i in range (self.m, 0, -1) :
            if self.finger[i] and self.in_interval (self.finger[i][0], self.node_id, id, inclusive_right = False) : 
                try:
                    if self.finger[i][0] == self.node_id or self.remote_call (self.finger[i], "ping", {}) == "pong" : return self.finger[i]
                except Exception : continue
        return (self.node_id, self.host, self.port)

    def create(self):
        """
        Create a new Chord ring with this node as the only member.

        Should set predecessor to None and successor to self.
        """
        # TODO: Implement this method
        self.predecessor = None
        self.successor = (self.node_id, self.host, self.port)

    def join(self, existing_node_addr):
        """
        Join an existing Chord ring via a known node.

        Should set predecessor to None, and ask the existing node to find
        this node's successor using find_successor.

        Args:
            existing_node_addr: (node_id, host, port) of a node already in the ring
        """
        # TODO: Implement this method
        self.predecessor = None
        succ = self.remote_call (existing_node_addr, "find_successor", {"id": self.node_id})
        if succ : 
            self.successor = succ
            self.remote_call (succ, "transfer_keys", {"node_id": self.node_id, "host": self.host, "port": self.port})

    def stabilize(self):
        """
        Periodically verify this node's immediate successor and inform the successor about this node.

        Steps:
        1. Ask successor for its predecessor (x)
        2. If x is between self and successor, update successor to x
        3. Notify the (possibly new) successor about self

        Hint: Use remote_call with "get_predecessor" and "notify" commands.
        """
        try :
            self.remote_call (self.successor, "ping", {})
            try :
                prev = self.remote_call (self.successor, "get_predecessor", {})
                if prev and self.in_interval (prev[0], self.node_id, self.successor[0], inclusive_right = False) : self.successor = prev
                self.remote_call (self.successor, "notify", {"node_id": self.node_id, "host" : self.host, "port" : self.port})
            except Exception : pass
        except Exception :
            for i in range (1,self.m + 1) :
                if not self.finger[i] or self.finger[i][0] == self.successor[0]: continue
                try :
                    self.remote_call (self.finger[i], "ping", {})
                    self.successor = self.finger[i]
                    break
                except : continue
            else : self.successor = (self.node_id, self.host, self.port)

    def notify(self, node_addr):
        """
        Handle notification from a node that thinks it is this node's predecessor.

        Update self.predecessor if:
        - Current predecessor is None, OR
        - node_addr falls in (self.predecessor, self) on the ring

        Args:
            node_addr: (node_id, host, port) of the potential predecessor
        """
        # TODO: Implement this method
        if self.predecessor == None or self.in_interval (node_addr[0], self.predecessor[0], self.node_id, inclusive_right = False) : self.predecessor = node_addr

    def fix_fingers(self):
        """
        Refresh one finger table entry per call.

        Use self.next to track which finger to fix (cycling from 1 to m).
        finger[i] should be the successor of (self.node_id + 2^(i-1)) mod 2^m.
        """
        # TODO: Implement this method
        self.finger[self.next] = self.find_successor ((self.node_id + 2 ** (self.next - 1)) % self.max_id)
        self.next = self.next % self.m + 1

    def check_predecessor(self):
        """
        Check if the predecessor has failed by pinging it.

        If the predecessor does not respond, set self.predecessor to None.

        Hint: Use remote_call with "ping" command and handle exceptions.
        """
        # TODO: Implement this method (Optional / Bonus)
        if self.predecessor :
            try : 
                if self.remote_call (self.predecessor, "ping", {}) != "pong" : self.predecessor = None
            except Exception : 
                self.predecessor = None
    # ========================================================================
    # Key Storage (Section 2)
    # ========================================================================

    def hash_key(self, key):
        """
        Hash a string key to an identifier in the Chord ring space [0, 2^m - 1].

        Use a standard hash function (e.g. SHA-1 from hashlib) and take modulo 2^m.

        Args:
            key: The string key to hash

        Returns:
            An integer identifier in [0, 2^m - 1]
        """
        # TODO: Implement this method
        return int (hashlib.sha1 (key.encode ()).hexdigest (), 16) % self.max_id

    def put(self, key, value):
        """
        Store a key-value pair in the DHT.

        Steps:
        1. Hash the key to get an identifier
        2. Find the successor node responsible for that identifier
        3. Store the key-value pair on that node using remote_call with "store" command

        Args:
            key: The key to store
            value: The value to store

        Returns:
            True if the operation succeeded, False otherwise
        """
        # TODO: Implement this method
        succ = self.find_successor (self.hash_key (key))
        if succ :
            try : 
                self.remote_call (succ, "store", {"key" : key, "value" : value})
                return True
            except Exception : return False
        else : return False
    def get(self, key):
        """
        Retrieve a value from the DHT by key.

        Steps:
        1. Hash the key to get an identifier
        2. Find the successor node responsible for that identifier
        3. Retrieve the value from that node using remote_call with "retrieve" command

        Args:
            key: The key to retrieve

        Returns:
            The associated value, or None if the key is not found
        """
        # TODO: Implement this method
        succ = self.find_successor (self.hash_key (key))
        if succ : 
            try :
                return self.remote_call (succ, "retrieve", {"key": key})
            except Exception : return None
        else : return None
    def transfer_keys(self, new_node_addr):
        """
        Transfer keys that should now belong to a new node.

        When a new node joins, this node (the successor) should transfer any keys
        whose hashed identifier falls in the range that the new node is now responsible for.

        Use remote_call with "store" command to send each key-value pair to the new node,
        then remove the transferred keys from self.data.

        Args:
            new_node_addr: (node_id, host, port) of the new node
        """
        # TODO: Implement this method
        lst = []
        for key, value in self.data.items ():
            id = self.hash_key (key)
            if self.in_interval (id, self.node_id, new_node_addr[0]) : lst.append ((key,value))
        for key, value in lst :
            try : 
                self.remote_call (new_node_addr, "store", {"key" : key, "value" : value})
                del self.data[key]
            except Exception : pass

    # ========================================================================
    # Network Communication (provided - do not modify)
    # ========================================================================

    def remote_call(self, node_addr, command, params, timeout=5.0):
        """
        Make a remote call to another node. Handles both local and remote calls transparently.

        Args:
            node_addr: (node_id, host, port) of the target node
            command: The command to execute (e.g. "find_successor", "notify", "store", "retrieve", ...)
            params: Dictionary of parameters for the command
            timeout: Socket timeout in seconds

        Returns:
            The result of the remote call, or None if it failed

        Raises:
            Exception: If the target node cannot be contacted
        """
        target_id, target_host, target_port = node_addr

        # Local call: if the target is this node, handle directly
        if target_id == self.node_id and target_host == self.host and target_port == self.port:
            if command == "find_successor":
                return self.find_successor(params.get("id"))
            elif command == "closest_preceding_node":
                return self.closest_preceding_node(params.get("id"))
            elif command == "get_predecessor":
                return self.predecessor
            elif command == "notify":
                n_id = params.get("node_id")
                n_host = params.get("host")
                n_port = params.get("port")
                self.notify((n_id, n_host, n_port))
                return (self.node_id, self.host, self.port)
            elif command == "ping":
                return "pong"
            elif command == "store":
                self.data[params.get("key")] = params.get("value")
                return True
            elif command == "retrieve":
                return self.data.get(params.get("key"))
            elif command == "get_data":
                return self.data
            elif command == "transfer_keys":
                n_id = params.get("node_id")
                n_host = params.get("host")
                n_port = params.get("port")
                self.transfer_keys((n_id, n_host, n_port))
                return True
            else:
                return "Unknown command"

        # Remote call: send request over TCP
        if target_id == -1 or target_host == "" or target_port == 0:
            raise Exception(f"Cannot contact node {target_id} - node address is invalid")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((target_host, target_port))
                message = json.dumps({"command": command, "params": params})
                s.sendall(message.encode())
                data = s.recv(4096)
                if data:
                    response = json.loads(data.decode())
                    return response.get("result")
            return None
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            raise Exception(f"Failed to connect to node {target_id} at {target_host}:{target_port} - {str(e)}")

    # TCP server: listens for incoming requests and handles them in separate threads.
    def run_server(self):
        # Implementation provided - handles TCP server operation
        try:
            # Socket is already initialized in __init__, just bind and listen
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            
            while self.running:
                try:
                    self.server.settimeout(1)  # Add timeout to check running flag
                    client, addr = self.server.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(client,))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # Only print error if we're supposed to be running
                        print(f"Server error: {e}")
        except Exception as e:
            print(f"Failed to start server: {e}")

    def handle_client(self, client_socket):
        # Implementation provided - handles incoming client connections
        try:
            data = client_socket.recv(4096)
            if not data:
                client_socket.close()
                return
            request = json.loads(data.decode())
            command = request.get("command")
            params = request.get("params")
            result = None

            if command == "find_successor":
                id = params.get("id")
                result = self.find_successor(id)
            elif command == "closest_preceding_node":
                id = params.get("id")
                result = self.closest_preceding_node(id)
            elif command == "get_predecessor":
                result = self.predecessor
            elif command == "notify":
                node_id = params.get("node_id")
                host = params.get("host")
                port = params.get("port")
                node_addr = (node_id, host, port)
                self.notify(node_addr)
                result = (self.node_id, self.host, self.port)
            elif command == "ping":
                result = "pong"
            elif command == "store":
                # Handle store operation
                key = params.get("key")
                value = params.get("value")
                self.data[key] = value
                result = True
            elif command == "retrieve":
                # Handle retrieve operation
                key = params.get("key")
                result = self.data.get(key)
            elif command == "get_data":
                # Return all data stored in this node
                result = self.data
            elif command == "transfer_keys":
                # Handle transfer_keys operation
                node_id = params.get("node_id")
                host = params.get("host")
                port = params.get("port")
                node_addr = (node_id, host, port)
                self.transfer_keys(node_addr)
                result = True
            else:
                result = "Unknown command"

            response = json.dumps({"result": result})
            client_socket.sendall(response.encode())
        except Exception as e:
            error_response = json.dumps({"result": None, "error": str(e)})
            client_socket.sendall(error_response.encode())
        finally:
            client_socket.close()

    def stop(self):
        """Stop the node's server thread and mark as stopped."""
        self.running = False
        self.stopped = True
        if self.server:
            self.server.close()