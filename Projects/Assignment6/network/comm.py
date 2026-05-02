#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Network Communication Layer (PROVIDED)

Provides point-to-point send/recv over persistent TCP connections.
Students use this to implement collective communication algorithms.

API:
    comm = Comm(rank, size, hosts, base_port=20000)
    comm.rank()             -> int
    comm.size()             -> int
    comm.send(dest, data)   -> None       (data: bytes)
    comm.recv(source)       -> bytes
    comm.sendrecv(dest, data, source) -> bytes  (concurrent send+recv)
    comm.barrier()          -> None
    comm.close()            -> None
"""
import socket
import struct
import threading
import time


def _recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(65536, n - len(buf)))
        if not chunk:
            raise ConnectionError("Connection closed unexpectedly")
        buf.extend(chunk)
    return bytes(buf)


class Comm:
    _BARRIER_TAG = 0xFFFF

    def __init__(self, rank, size, hosts, base_port=20000):
        """
        Args:
            rank:      this process's rank (0-indexed)
            size:      total number of processes
            hosts:     list of hostnames/IPs, length == size, hosts[i] is rank i
            base_port: rank i listens on base_port + i
        """
        if not (0 <= rank < size):
            raise ValueError(f"rank {rank} out of range [0, {size})")
        if len(hosts) != size:
            raise ValueError(f"hosts length {len(hosts)} != size {size}")

        self._rank = rank
        self._size = size
        self._hosts = hosts
        self._base_port = base_port
        self._send_socks = {}  # dest_rank -> socket (we write, they read)
        self._recv_socks = {}  # src_rank  -> socket (they write, we read)
        self._setup()

    def rank(self):
        return self._rank

    def size(self):
        return self._size

    def send(self, dest, data, tag=0):
        """Send bytes to rank dest."""
        sock = self._send_socks[dest]
        header = struct.pack("!II", tag, len(data))
        sock.sendall(header + data)

    def recv(self, source, tag=0):
        """Receive bytes from rank source."""
        sock = self._recv_socks[source]
        header = _recv_exact(sock, 8)
        msg_tag, length = struct.unpack("!II", header)
        if msg_tag != tag:
            raise RuntimeError(
                f"Rank {self._rank}: expected tag {tag} from rank {source}, "
                f"got tag {msg_tag}"
            )
        return _recv_exact(sock, length) if length > 0 else b""

    def sendrecv(self, dest, data, source, tag=0):
        """Send data to dest and receive from source concurrently.

        Essential for ring algorithms: avoids deadlock when every rank
        simultaneously sends to its right neighbor and receives from its
        left neighbor.

        Returns the received bytes.
        """
        received = [None]
        error = [None]

        def do_recv():
            try:
                received[0] = self.recv(source, tag)
            except Exception as e:
                error[0] = e

        t = threading.Thread(target=do_recv)
        t.start()
        self.send(dest, data, tag)
        t.join()
        if error[0] is not None:
            raise error[0]
        return received[0]

    def barrier(self):
        """Global barrier — all ranks must call this together."""
        tag = self._BARRIER_TAG
        if self._rank == 0:
            for i in range(1, self._size):
                self.recv(i, tag=tag)
            for i in range(1, self._size):
                self.send(i, b"", tag=tag)
        else:
            self.send(0, b"", tag=tag)
            self.recv(0, tag=tag)

    def close(self):
        """Shut down all connections."""
        for s in list(self._send_socks.values()) + list(self._recv_socks.values()):
            try:
                s.close()
            except Exception:
                pass

    # ── connection setup (students don't need to read below) ──────────

    def _setup(self):
        """Establish persistent TCP connections between all rank pairs.

        Protocol: for each pair (i, j) where i < j, rank i initiates two
        TCP connections to rank j:
          header (i, 0) -> i uses as send_sock[j], j uses as recv_sock[i]
          header (i, 1) -> j uses as send_sock[i], i uses as recv_sock[j]
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self._base_port + self._rank))
        server.listen(2 * self._size)

        n_incoming = 2 * self._rank  # connections from lower-ranked peers
        incoming = {}

        def accept_all():
            for _ in range(n_incoming):
                conn, _ = server.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                hdr = _recv_exact(conn, 8)
                peer, direction = struct.unpack("!II", hdr)
                incoming[(peer, direction)] = conn

        if n_incoming > 0:
            accept_thread = threading.Thread(target=accept_all)
            accept_thread.start()
        else:
            accept_thread = None

        time.sleep(1.0)

        for peer in range(self._rank + 1, self._size):
            for direction in (0, 1):
                for _ in range(120):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        s.connect((self._hosts[peer], self._base_port + peer))
                        s.sendall(struct.pack("!II", self._rank, direction))
                        if direction == 0:
                            self._send_socks[peer] = s
                        else:
                            self._recv_socks[peer] = s
                        break
                    except (ConnectionRefusedError, OSError):
                        time.sleep(0.5)
                else:
                    raise RuntimeError(
                        f"Rank {self._rank}: cannot connect to rank {peer} "
                        f"at {self._hosts[peer]}:{self._base_port + peer}"
                    )

        if accept_thread is not None:
            accept_thread.join(timeout=60)

        for (peer, direction), conn in incoming.items():
            if direction == 0:
                self._recv_socks[peer] = conn
            else:
                self._send_socks[peer] = conn

        server.close()

        expected = set(range(self._size)) - {self._rank}
        assert set(self._send_socks.keys()) == expected, "Missing send connections"
        assert set(self._recv_socks.keys()) == expected, "Missing recv connections"
