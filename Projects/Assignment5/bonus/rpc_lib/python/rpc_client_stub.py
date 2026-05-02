import socket
import struct
import json  # Use standard json module
from typing import Any, List, Tuple, Union

# Import only exceptions, not marshal functions
# Use absolute import because rpc_lib/python is added to sys.path
from rpc_exceptions import (
    ConnectionError,
    RPCError,
    FunctionNotFoundError,
    ExecutionError,
    ProtocolError,
    MarshalingError,  # Keep for JSON encoding/decoding issues
)

# Type alias for RPC values in Python (can be any JSON-serializable type)
RPCValue = Union[int, float, str, bool, None, List[Any], dict]


class RPCClient:
    """Client stub for making RPC calls to a C++ server using JSON."""

    def __init__(self, host: str, port: int):
        """
        Initializes the RPC client but does not connect yet.
        Args:
            host: The hostname or IP address of the server.
            port: The port number of the server.
        """
        self.host = host
        self.port = port
        self.sock: Union[socket.socket, None] = None
        self._is_connected = False

    def connect(self):
        """
        TODO: Establish a connection to the RPC server.

        Your implementation should:
        1. Check if already connected
        2. Create a new socket
        3. Connect to the server using the host and port
        4. Handle any socket errors appropriately
        5. Update the connection state
        """
        # Your implementation here
        if self._is_connected: return
        try:
            self.sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect ((self.host, self.port))
            self._is_connected = True
        except OSError as e:
            self._handle_socket_error (e, "connect")
        

    def disconnect(self):
        """
        TODO: Close the connection to the RPC server.

        Your implementation should:
        1. Check if already disconnected
        2. Properly shutdown the socket
        3. Close the socket
        4. Handle any socket errors
        5. Update the connection state
        """
        # Your implementation here
        if not self._is_connected or self.sock is None: return
        try: 
            self.sock.shutdown (socket.SHUT_RDWR)
        except OSError: 
            pass
        try: 
            self.sock.close ()
        except OSError: 
            pass
        self.sock = None
        self._is_connected = False

    def _send_all(self, data: bytes):
        """
        TODO: Helper method to send all data reliably.

        Your implementation should:
        1. Check if connected
        2. Use sock.sendall() to send data
        3. Handle socket errors and timeouts
        """
        # Your implementation here
        if not self._is_connected or self.sock is None:
            raise ConnectionError("Not connected to server")
        try:
            self.sock.sendall (data)
        except socket.error as e:
            self._handle_socket_error (e, "send")

    def _recv_all(self, num_bytes: int) -> bytes:
        """
        TODO: Helper method to receive an exact number of bytes reliably.

        Your implementation should:
        1. Check if connected
        2. Create a buffer to store received data
        3. Loop until all requested bytes are received
        4. Handle partial receives, socket errors, and timeouts
        5. Return the complete received data
        """
        # Your implementation here
        if not self._is_connected or self.sock is None:
            raise ConnectionError("Not connected to server")
        data = bytearray ()
        while len (data) < num_bytes: 
            try:
                chunk = self.sock.recv (num_bytes - len (data))
            except OSError as e:
                self._handle_socket_error (e, "receive")
            if not chunk:
                self._handle_socket_error (ConnectionError ("Connection closed by peer"), "receive")
            data.extend (chunk)
        return bytes (data)

    def _handle_socket_error(self, e: Exception, operation: str):
        """
        TODO: Handles socket errors, updates connection state, and raises ConnectionError.

        Your implementation should:
        1. Disconnect the socket
        2. Raise a ConnectionError with appropriate message
        """
        # Your implementation here
        self.disconnect ()
        raise ConnectionError (f"Socket error during {operation}: {str (e)}")

    def call(self, func_name: str, *args: RPCValue):
        if not self._is_connected:
            raise ConnectionError ("Not connected")

        func_map = {"add": 1, "greet": 2, "is_positive": 3, "no_return": 4, "divide": 5, "sum_array": 6, "process_person": 7, "get_greetings": 8, "echo": 9}
        if func_name not in func_map:
            raise FunctionNotFoundError (f"Function {func_name} not found")
        func_id = func_map[func_name]
        payload = struct.pack ('!B', func_id)
        expected_args_count = {1: 2, 2: 1, 3: 1, 4: 0, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1}
        if func_id in expected_args_count:
            if len (args) != expected_args_count[func_id]:
                raise ExecutionError (f"Function expects {expected_args_count[func_id]} arguments, got {len (args)}")
        if func_id in (1, 5) and len (args) == 2:
            if not isinstance (args[0], int) or isinstance (args[0], bool) or not isinstance (args[1], int) or isinstance (args[1], bool):
                 raise ExecutionError ("Arguments must be integers")
        try:
            if func_id == 1:  # add(int, int)
                payload += struct.pack ('!ii', args[0], args[1])
            elif func_id in (2, 9):  # greet(str) or echo(str)
                name_bytes = args[0].encode ('utf-8')
                payload += struct.pack ('!I', len (name_bytes)) + name_bytes
            elif func_id == 3:  # is_positive(float)
                payload += struct.pack ('!f', args[0])
            elif func_id == 4:  # no_return()
                pass
            elif func_id == 5:  # divide(int, int)
                payload += struct.pack ('!ii', args[0], args[1])
            elif func_id == 6:  # sum_array(list[int])
                arr = args[0]
                payload += struct.pack ('!I', len (arr))
                for num in arr:
                    payload += struct.pack ('!i', num)
            elif func_id == 7:  # process_person(dict)
                person = args[0]
                name_bytes = person['name'].encode ('utf-8')
                payload += struct.pack ('!I', len (name_bytes)) + name_bytes
                payload += struct.pack ('!i B', person['age'], 1 if person['is_student'] else 0)
            elif func_id == 8:  # get_greetings(list[str])
                arr = args[0]
                payload += struct.pack ('!I', len (arr))
                for name in arr:
                    name_bytes = name.encode ('utf-8')
                    payload += struct.pack ('!I', len (name_bytes)) + name_bytes
        except RPCError:
            raise
        except Exception as e:
            raise MarshalingError (f"Failed to encode binary request: {e}")
        
        try:
            self._send_all (struct.pack ('!I', len (payload)) + payload)
        except ConnectionError:
            raise

        try:
            len_bytes = self._recv_all (4)
            resp_length = struct.unpack ('!I', len_bytes)[0]
            resp_data = self._recv_all (resp_length)
        except ConnectionError:
            raise

        status_code = resp_data[0]
        result_data = resp_data[1:]

        if status_code != 0:
            error_msg = result_data.decode ('utf-8', errors='ignore')
            if status_code == 2:
                raise FunctionNotFoundError (error_msg)
            elif status_code == 3:
                raise ExecutionError (error_msg)
            else:
                raise RPCError (error_msg)

        try:
            if func_id in (1, 5, 6):  # int
                return struct.unpack ('!i', result_data)[0]
            elif func_id in (2, 7, 9):  # string
                return result_data.decode ('utf-8')
            elif func_id == 3:  # bool
                return struct.unpack ('!?', result_data)[0]
            elif func_id == 4:  # None
                return None
            elif func_id == 8:  # list[str]
                count = struct.unpack ('!I', result_data[:4])[0]
                offset = 4
                res_list = []
                for _ in range (count):
                    slen = struct.unpack ('!I', result_data[offset:offset + 4])[0]
                    offset += 4
                    res_list.append (result_data[offset:offset + slen].decode ('utf-8'))
                    offset += slen
                return res_list
        except Exception as e:
            raise MarshalingError (f"Failed to decode binary response: {e}")

    # Context manager support - we provide these for convenience
    def __enter__(self):
        """Enter the runtime context related to this object."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object."""
        self.disconnect()
