# AWS EC2 Setup Guide

This guide walks you through launching EC2 instances for Assignment 6.
You need **4 instances** (minimum) of type **c5n.large** in the **same
availability zone**.

---

## Step 1: Log in to AWS Academy

1. Go to your AWS Academy course on Canvas.
2. Click **Modules** > **Learner Lab**.
3. Click **Start Lab** (wait for the dot to turn green).
4. Click **AWS** to open the console.

> Your lab has a $50 credit budget. c5n.large costs ~$0.054/hr per
> instance. Four instances for 10 hours = ~$2.16. You have plenty of
> budget, but **stop instances when not in use**.

---

## Step 2: Create a Key Pair

1. Go to **EC2** > **Key Pairs** (left sidebar, under Network & Security).
2. Click **Create key pair**.
   - Name: `csc4303-a6`
   - Type: RSA
   - Format: `.pem`
3. Download `csc4303-a6.pem`. Save it in `~/.ssh/` (do **not** put private keys inside this assignment repo).
4. Set permissions: `chmod 400 ~/.ssh/csc4303-a6.pem`

---

## Step 3: Create a Security Group

1. Go to **EC2** > **Security Groups** (left sidebar).
2. Click **Create security group**.
   - Name: `csc4303-a6-sg`
   - Description: `Assignment 6 collective communication`
   - VPC: default
3. **Inbound rules** — add these:

| Type | Port Range | Source | Purpose |
|---|---|---|---|
| SSH | 22 | My IP | SSH access |
| Custom TCP | 20000-20100 | `csc4303-a6-sg` (self-reference) | Inter-node comm |
| All ICMP - IPv4 | All | `csc4303-a6-sg` | Ping between nodes |

4. Click **Create security group**.

> The self-referencing rule means instances in this group can talk to
> each other on ports 20000-20100. This is how your Comm layer connects.

---

## Step 4: Launch Instances

1. Go to **EC2** > **Instances** > **Launch instances**.
2. Settings:
   - **Name:** `a6-node` (AWS will auto-suffix -1, -2, etc.)
   - **AMI:** Ubuntu Server 24.04 LTS (free tier eligible)
   - **Instance type:** `c5n.large` (2 vCPU, 5.25 GB RAM, 25 Gbps network)
   - **Key pair:** `csc4303-a6`
   - **Network settings:** click Edit
     - Subnet: pick a **specific** subnet (e.g., `us-east-1a`) — all nodes must be in the same AZ
     - Security group: select existing `csc4303-a6-sg`
   - **Number of instances:** `4`
3. Click **Launch instance**.
4. Wait for all 4 to show **Running** and **2/2 checks passed**.

---

## Step 5: Note Private IPs

1. Go to **EC2** > **Instances**.
2. For each instance, note the **Private IPv4 address** (e.g., `172.31.x.x`).
3. Edit `config/my_config.py`:

```python
STUDENT_ID = "123456789"
STUDENT_NAME = "Your Name"
HOSTS = [
    "172.31.1.10",   # rank 0
    "172.31.1.11",   # rank 1
    "172.31.1.12",   # rank 2
    "172.31.1.13",   # rank 3
]
```

---

## Step 6: Install Dependencies

SSH into **each** node and install numpy:

```bash
ssh -i ~/.ssh/csc4303-a6.pem ubuntu@<PUBLIC_IP>
sudo apt-get update && sudo apt-get install -y python3-numpy python3-matplotlib
```

Or from your local machine in a loop:

```bash
PUBLIC_IPS=("1.2.3.4" "1.2.3.5" "1.2.3.6" "1.2.3.7")
for ip in "${PUBLIC_IPS[@]}"; do
    ssh -i ~/.ssh/csc4303-a6.pem ubuntu@${ip} "sudo apt-get update && sudo apt-get install -y python3-numpy python3-matplotlib" &
done
wait
```

---

## Step 7: Upload Code to All Nodes

From your local machine (in the Assignment-6 directory):

```bash
# For each node (replace <PUBLIC_IP> with each instance's public IP).
# Exclude key files and caches.
rsync -az --exclude='*.pem' --exclude='*.key' --exclude='__pycache__/' --exclude='.pytest_cache/' \
  -e "ssh -i ~/.ssh/csc4303-a6.pem" ./ ubuntu@<PUBLIC_IP>:~/Assignment-6/
```

Or use a loop:

```bash
PUBLIC_IPS=("1.2.3.4" "1.2.3.5" "1.2.3.6" "1.2.3.7")
for ip in "${PUBLIC_IPS[@]}"; do
    rsync -az --exclude='*.pem' --exclude='*.key' --exclude='__pycache__/' --exclude='.pytest_cache/' \
      -e "ssh -i ~/.ssh/csc4303-a6.pem" ./ ubuntu@${ip}:~/Assignment-6/ &
done
wait
```

---

## Step 8: Test Connectivity

From rank 0's node, verify you can reach all other nodes:

```bash
# Test SSH
ssh -i ~/.ssh/csc4303-a6.pem ubuntu@<PRIVATE_IP_of_rank1> hostname

# Test ping
ping -c 3 <PRIVATE_IP_of_rank1>
```

---

## Running Benchmarks

Option A — use the launcher (from rank 0's node, NOT your local machine):

```bash
# SSH into rank 0 first
ssh -i ~/.ssh/csc4303-a6.pem ubuntu@<PUBLIC_IP_of_rank0>

# Copy your SSH key to rank 0 so it can SSH to other nodes.
# Keep it outside the assignment repo path if possible.
# (from your local machine):
scp -i ~/.ssh/csc4303-a6.pem ~/.ssh/csc4303-a6.pem ubuntu@<PUBLIC_IP_of_rank0>:~/.ssh/

# Then on rank 0:
cd ~/Assignment-6
python3 network/launcher.py --script benchmark/run_benchmark.py
```

> **Note:** The launcher uses private IPs from `config/my_config.py` to
> SSH into other nodes. This only works from within the VPC (i.e., from
> one of your EC2 instances), not from your local machine.

Option B — manually (SSH into each node in separate terminals):

```bash
# On node 0:
python3 benchmark/run_benchmark.py --rank 0 --size 4 --hosts 172.31.1.10,172.31.1.11,172.31.1.12,172.31.1.13

# On node 1:
python3 benchmark/run_benchmark.py --rank 1 --size 4 --hosts 172.31.1.10,172.31.1.11,172.31.1.12,172.31.1.13

# ... and so on for nodes 2, 3
```

> **Important:** Start all nodes within ~30 seconds of each other.
> The Comm layer retries connections for 60 seconds — if a node starts
> too late, other nodes will time out.

---

## Cost Management

- **Stop instances** when not benchmarking: select all > Instance State > Stop.
- Stopped instances cost $0 for compute (small EBS cost remains).
- Private IPs may change on restart — check and update `my_config.py`.
- The lab auto-stops after 4 hours of inactivity.
- **Do not terminate** instances until you have all your data — terminated
  instances cannot be recovered.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Connection refused` on port 20000+ | Check security group has self-referencing TCP 20000-20100 rule |
| `Address already in use` | A previous run left a port occupied. Wait 60s (TCP TIME_WAIT) or use `--base-port 20010` to pick different ports. You can also kill leftover processes: `pkill -f run_benchmark` |
| `Permission denied (publickey)` | Check key file permissions: `chmod 400 ~/.ssh/csc4303-a6.pem` |
| `cannot connect to rank X` | Nodes started too far apart in time. Kill all (`pkill -f run_benchmark` on each node) and restart all within 30s |
| `ModuleNotFoundError: numpy` | Run `sudo apt-get install -y python3-numpy` on that node |
| Instances in different AZs | Terminate and re-launch all in the same subnet |
| `c5n.large` not available | Try a different AZ in the same region |
| Metadata check fails | Ensure IMDSv2 is enabled in instance settings |
| Benchmark times vary wildly | Make sure you're using c5n.large, not t3 (burst credits cause 3× variance) |
