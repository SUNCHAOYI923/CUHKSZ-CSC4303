### Task 1

| Type          | TCP b/w (Mbps) | RTT (ms) |
|---------------|----------------|----------|
| `t3.medium`-`t3.medium` |  4430 4410 3970 4390|   rtt min/avg/max/mdev = 0.211/0.279/0.740/0.098 ms <br> rtt min/avg/max/mdev = 0.303/0.346/0.787/0.081 ms       |
| `m5.large`-`m5.large`  |    4780 4830 4950 4740|    rtt min/avg/max/mdev = 0.203/0.218/0.259/0.011 ms <br> rtt min/avg/max/mdev = 0.193/0.224/0.327/0.027 ms      |
| `c5n.large`-`c5n.large` |      4960 4960 4960          |   rtt min/avg/max/mdev = 0.135/0.160/0.441/0.049 ms <br> rtt min/avg/max/mdev = 0.159/0.203/0.307/0.050 ms       |
| `t3.medium`-`c5n.large`   | 4010 4110 3590 3960  3660   4130          |    rtt min/avg/max/mdev = 0.312/0.350/0.669/0.063 ms <br> rtt min/avg/max/mdev = 0.338/0.358/0.393/0.011 ms      |
| `m5.large`-`c5n.large`  |     2200 2090 2120    2180 2370       |      rtt min/avg/max/mdev = 0.689/0.739/1.581/0.146 ms <br> rtt min/avg/max/mdev = 0.575/0.601/0.693/0.023 ms    |
| `m5.large`-`t3.medium` |    2020 2050            |   rtt min/avg/max/mdev = 0.777/0.849/1.609/0.150 ms <br> rtt min/avg/max/mdev = 0.750/0.815/1.087/0.078 ms       |

### Task 2

| Connection | TCP b/w (Mbps)  | RTT (ms) |
|------------|-----------------|--------------------|
| N. Virginia-Oregon |       34.8 35 34.9          |     rtt min/avg/max/mdev = 58.668/58.686/58.739/0.016 ms <br> rtt min/avg/max/mdev = 58.661/58.680/58.731/0.015 ms               |
| N. Virginia-N. Virginia  |    4940 4950 4960             |      rtt min/avg/max/mdev = 0.117/0.145/0.628/0.081 ms <br> rtt min/avg/max/mdev = 0.112/0.127/0.164/0.011 ms           |
| Oregon-Oregon |    4940 4940 4950             |  rtt min/avg/max/mdev = 0.093/0.136/0.285/0.043 ms <br> rtt min/avg/max/mdev = 0.102/0.152/0.618/0.087 ms                  |