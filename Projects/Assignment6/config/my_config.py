#!/usr/bin/env python3
"""
CSC4303 Assignment-6 — Student Configuration

Fill in your details below. The benchmark scripts use these values
to tag every CSV row with forensic metadata.
"""

# ── REQUIRED: fill these in ──────────────────────────────────────────

STUDENT_ID = "124090550"          # e.g. "123456789"
STUDENT_NAME = "Chaoyi, Sun"        # e.g. "Zhang San"

# Private IPs of your EC2 instances (same AZ, same security group).
# Order matters: hosts[0] = rank 0, hosts[1] = rank 1, etc.
# Example for 4 nodes:
#   HOSTS = ["172.31.1.10", "172.31.1.11", "172.31.1.12", "172.31.1.13"]
HOSTS = ["172.31.15.219", "172.31.15.25"]
#("100.52.212.132" "100.31.238.5")
# Instance type (should be "c5n.large" unless instructed otherwise)
INSTANCE_TYPE = "c5n.large"

# Base port for inter-rank communication (default is fine)
BASE_PORT = 20000
