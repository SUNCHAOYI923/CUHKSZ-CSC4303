#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Ping-pong latency/bandwidth probe

Measures one-way latency (alpha) and per-byte cost (beta) between two EC2
instances using plain TCP. Run on two instances in the same AZ.

Usage:
    # On the "server" instance (receives first):
    python3 benchmark/ping_pong.py server 0.0.0.0 20000

    # On the "client" instance (initiates), using the server's PRIVATE IP:
    python3 benchmark/ping_pong.py client <server_private_ip> 20000

Output (client side): CSV to stdout, one row per message size.
    size_bytes,rounds,min_us,median_us,mean_us,stdev_us,throughput_mbps

Interpretation:
    - min_us for size=1 is ~ 2*alpha (round-trip).
    - slope of min_us vs size at large n gives 2*beta.
    - throughput at large n approaches 1/beta (per direction).
"""
import sys
import socket
import time
import statistics

# Sizes in bytes, spanning 7 orders of magnitude to catch crossover behavior.
SIZES = [1, 64, 1024, 16 * 1024, 256 * 1024, 1024 * 1024, 4 * 1024 * 1024, 16 * 1024 * 1024]


def recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(1 << 20, n - len(buf)))
        if not chunk:
            raise ConnectionError("peer closed mid-message")
        buf.extend(chunk)
    return bytes(buf)


def server(host, port):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(1)
    print(f"[server] listening on {host}:{port} (accepts multiple clients, Ctrl-C to stop)", flush=True)
    try:
        while True:
            conn, addr = s.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"[server] connected by {addr}", flush=True)
            try:
                while True:
                    hdr = recv_exact(conn, 8)
                    n = int.from_bytes(hdr, "big")
                    if n == 0:
                        break
                    data = recv_exact(conn, n)
                    conn.sendall(hdr + data)
            finally:
                conn.close()
            print(f"[server] client {addr} done, waiting for next...", flush=True)
    except KeyboardInterrupt:
        print("\n[server] stopped", flush=True)
    finally:
        s.close()


def client(host, port):
    time.sleep(1.0)  # give server a beat to bind
    s = socket.socket()
    s.connect((host, port))
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    print("size_bytes,rounds,min_us,median_us,mean_us,stdev_us,throughput_mbps")
    for n in SIZES:
        rounds = 100 if n <= 65536 else (30 if n <= 1024 * 1024 else 10)
        payload = b"x" * n

        # warmup (3 rounds, ignored)
        for _ in range(3):
            s.sendall(n.to_bytes(8, "big") + payload)
            recv_exact(s, 8 + n)

        # measure
        rtts = []
        for _ in range(rounds):
            t0 = time.perf_counter()
            s.sendall(n.to_bytes(8, "big") + payload)
            recv_exact(s, 8 + n)
            rtts.append((time.perf_counter() - t0) * 1e6)

        rtts.sort()
        mn = rtts[0]
        med = statistics.median(rtts)
        mean = statistics.mean(rtts)
        sd = statistics.stdev(rtts) if len(rtts) > 1 else 0.0
        # throughput assumes one-way = RTT/2, both directions each carry n bytes
        # effective = n bytes sent + n bytes echoed during RTT
        throughput_mbps = (2 * n * 8) / (med) if med > 0 else 0.0  # bits per microsecond == Mbps

        print(f"{n},{rounds},{mn:.1f},{med:.1f},{mean:.1f},{sd:.1f},{throughput_mbps:.1f}")

    s.sendall((0).to_bytes(8, "big"))
    s.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    if mode == "server":
        server(host, port)
    elif mode == "client":
        client(host, port)
    else:
        print("mode must be 'server' or 'client'")
        sys.exit(1)
