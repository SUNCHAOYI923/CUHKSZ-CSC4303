1. SSH Key Permission `chmod 400 key.pem`

2. `iperf`/`iperf3`

```bash
sudo apt-get update
sudo apt-get install iperf -y
```

- Important Parameter **TCP Window Size** `-w`

    Default TCP window size (typically 64KB) severely limits throughput, especially in high-latency scenarios. The `-w` parameter eliminates TCP flow control bottlenecks, revealing the actual network capacity.

3. Cross-Region Connectivity

    - Public IP

    - VPC Peering [Referrence](https://zhuanlan.zhihu.com/p/665952205)
