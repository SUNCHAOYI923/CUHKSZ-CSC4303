#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Multi-node Launcher

Spawns a command on N EC2 instances via SSH and streams their output.

Usage:
    python3 network/launcher.py --script benchmark/run_benchmark.py

Reads host list from config/my_config.py. Each host gets --rank and --size
arguments appended automatically.
"""
import argparse
import subprocess
import sys
import threading
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.my_config import HOSTS, BASE_PORT


def _stream_lines(stream, prefix, tag=""):
    for line in stream:
        print(f"{prefix}{tag} {line}", end="", flush=True)


def stream_output(proc, rank):
    prefix = f"[rank {rank}]"
    t_err = threading.Thread(target=_stream_lines, args=(proc.stderr, prefix, " [ERR]"), daemon=True)
    t_err.start()
    _stream_lines(proc.stdout, prefix)
    t_err.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description="Launch script on EC2 cluster")
    parser.add_argument("--script", required=True, help="Python script to run")
    parser.add_argument("--key", default="~/.ssh/csc4303-a6.pem", help="SSH key file")
    parser.add_argument("--user", default="ubuntu", help="SSH username")
    parser.add_argument("--remote-dir", default="~/Assignment-6",
                        help="Working directory on remote hosts")
    parser.add_argument("--extra-args", default="", help="Extra args to pass")
    args = parser.parse_args()

    size = len(HOSTS)
    if size == 0:
        print("ERROR: HOSTS list is empty in config/my_config.py")
        sys.exit(1)

    hosts_str = ",".join(HOSTS)
    procs = []
    threads = []

    key_path = os.path.expanduser(args.key)
    if not os.path.isabs(key_path):
        key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                key_path)

    for rank in range(size):
        host = HOSTS[rank]
        remote_cmd = (
            f"cd {args.remote_dir} && "
            f"python3 {args.script} "
            f"--rank {rank} --size {size} "
            f"--hosts {hosts_str} --base-port {BASE_PORT} "
            f"{args.extra_args}"
        )
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-i", key_path,
            f"{args.user}@{host}",
            remote_cmd,
        ]
        print(f"Launching rank {rank} on {host}...", flush=True)
        proc = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        procs.append(proc)

        t = threading.Thread(target=stream_output, args=(proc, rank), daemon=True)
        t.start()
        threads.append(t)

    exit_codes = []
    for rank, proc in enumerate(procs):
        proc.wait()
        exit_codes.append(proc.returncode)

    for t in threads:
        t.join(timeout=5)

    print("\n" + "=" * 60)
    for rank, code in enumerate(exit_codes):
        status = "OK" if code == 0 else f"FAILED (exit {code})"
        print(f"  Rank {rank}: {status}")
    print("=" * 60)

    if any(c != 0 for c in exit_codes):
        sys.exit(1)


if __name__ == "__main__":
    main()
