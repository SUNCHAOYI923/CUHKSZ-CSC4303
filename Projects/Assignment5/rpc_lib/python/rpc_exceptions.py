# Define custom exceptions for the RPC library


class RPCError(Exception):
    """Base class for exceptions in this RPC library."""

    pass


class ConnectionError(RPCError):
    """Exception raised for errors in the connection phase."""

    pass


class MarshalingError(RPCError):
    """Exception raised for errors during marshaling or unmarshaling."""

    pass


class FunctionNotFoundError(RPCError):
    """Exception raised when the server cannot find the requested function."""

    pass


class ExecutionError(RPCError):
    """Exception raised when an error occurs during function execution on the server."""

    pass


class ProtocolError(RPCError):
    """Exception raised for violations of the RPC protocol."""

    pass
