[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/lm_rjVJ7)
# CSC4303 Assignment-1: EC2 Measurement (2 questions)

### Deadline: 23:59, Jan 23, Friday
---

### Name: Chaoyi, Sun
### Student Id: 124090550

---

## Question: Measure the EC2 Network performance

The following TCP bandwidth measurements were performed using a fixed window size of 256 KB (`-w 256K`).

1. (2 mark) The metrics of network performance include **TCP bandwidth** and **round-trip time (RTT)**. Within the same region, what network performance is experienced between instances of the same type and different types? In order to answer this question, you need to complete the following table and briefly explain your observation. 

    | Type          | TCP b/w (Mbps) | RTT (ms) |
    |---------------|----------------|----------|
    | `t3.medium`-`t3.medium` | 4300 | 0.313 |
    | `m5.large`-`m5.large`  | 4825 | 0.221 |
    | `c5n.large`-`c5n.large` | 4960 | 0.181 |
    | `t3.medium`-`c5n.large`   | 3910 | 0.354 |
    | `m5.large`-`c5n.large`  | 2192 | 0.670 |
    | `m5.large`-`t3.medium` | 2035 | 0.832 |

    > Region: US East (N. Virginia)

    - $\text{\large Observation}$
    
        - Among the three types, `c5n.large` offers the best network performance, followed by `m5.large`, and then `t3.medium` in the same AWS region.

        - Within the same AWS region, connections with similar type having overall better performance compared to instances of different types.

2. (2 mark) What about the network performance for instances deployed in different regions? In order to answer this question, you need to complete the following table and briefly explain your observation. 

    | Connection | TCP b/w (Mbps)  | RTT (ms) |
    |------------|-----------------|----------|
    | N. Virginia-Oregon | 34.9 | 58.6 |
    | N. Virginia-N. Virginia  | 4950 | 0.136 |
    | Oregon-Oregon | 4943 | 0.144 |

    > All instances are `c5.large`.

    - $\text{\large Observation}$

        - Network performance between EC2 instances across regions is drastically lower than within the same region, with far reduced bandwidth and much higher latency.

