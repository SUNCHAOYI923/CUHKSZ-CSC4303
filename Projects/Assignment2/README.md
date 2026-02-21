[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/5OK2jzOe)
# CSC4303 Assignment-2: Socket Programming (10 points)

### Deadline: February 6th, 2026, 23:59

### Name: Chaoyi, Sun

### Student Id: 124090550

This is not a group assignment. **You are not allowed to copy or look at code
from other students.** However, you are welcome to discuss the assignments with
other students without sharing code.

Let's get started!

## Basic Socket Programming (6 points)

This section will give you experience with basic socket programming. You will write a pair of TCP client and server programs for sending and receiving text messages over the network.

**Requirements:**
- Implement a server program `socket_server.c` and a client program `socket_client.c`
- Must be written in C on a Unix-like Operating System (gcc version >= 9, cmake >= 3.10)
- **For Windows users:** Install Ubuntu 20.04 or 22.04 via WSL2 (Windows Subsystem for Linux)
  - Open PowerShell as Administrator and run: `wsl --install -d Ubuntu-22.04`
  - See [Microsoft WSL Installation Guide](https://learn.microsoft.com/en-us/windows/wsl/install) for details
  - ⚠️ **Recommended: Use WSL2** (not WSL1) for better compatibility
- You may also use a virtual machine locally or on AWS EC2 as your development environment
- ⚠️ **Keep an eye on AWS Cost Billing if you choose EC2!**

The client and server programs should meet the following specifications. **Be sure to read these carefully before and after programming to make sure your implementation fulfills them:**

### Server specification

-   Each server program should listen on a socket, wait for a client to connect,
    receive a message from the client, **echo back the message to the client**, and then wait
    for the next client indefinitely.
-   Each server should accept and process client communications in an infinite
    loop, allowing multiple clients to send messages to the same server. The
    server should only exit in response to an external signal (e.g. SIGINT from
    pressing `ctrl-c`).
-   Each server maintains a short (backlog of 3) client queue and handles multiple
    client connection attempts using I/O multiplexing (`poll()`).
-   Each server should gracefully handle error values potentially returned by
    socket programming library functions.
    Errors related to handling client connections should not cause the server to
    exit after handling the error; all others should.

### Client specification

-   Each client program should connect to the server, send a message, receive a response, and exit.
-   Each client uses a fixed-size buffer `buffer[1024]` for sending and receiving messages.
-   Each client should gracefully handle error values potentially returned by
    socket programming library functions.

### Getting started

We have provided the code skeleton in the root of GitHub repository. _You should read and understand this code before starting to program._

You should program only in the locations of the provided files marked with `TODO` comments:
- **`socket_server.c`**: 7 TODOs
- **`socket_client.c`**: 5 TODOs

You can add helper functions if you wish, but **do not change file names**, as they will be used for automated testing.

### References

Here are some references that might be helpful:
https://beej.us/guide/bgnet/html/.  
The [system call section](https://beej.us/guide/bgnet/html/#system-calls-or-bust) and [client/server example section](https://beej.us/guide/bgnet/html/#client-server-background) will
be most relevant.
The man pages are also useful for looking up individual
functions (e.g. `man socket`).

For error handling, you can call `perror` for socket programming functions that set the global variable `errno` . For
those that don't, simply print a message to standard error.

### Build

You should build your solution by:

1. In the root of GitHub repository, create a `build` directory:
   ```bash
   mkdir build
   cd build
   ```
2. Run CMake and Make:
   ```bash
   cmake ..
   make
   ```

Your code **must** build successfully using the provided CMakeLists.txt.

### Testing

You should test your implementations by attempting to send messages from your client(s) to your server. Use `127.0.0.1` as the server IP address.

#### Test 1: Single Client-to-Server Communication
1. Open a terminal, navigate to `build/`
2. Start the server: `./socket_server`
3. Open another terminal, navigate to the same directory
4. Run the client: `./socket_client`

#### Test 2: Concurrent Clients-to-Server Communication
1. Copy `con.sh` to the `build/` directory
2. If you get a permissions error, run: `chmod +x con.sh`
3. Start the server in one terminal: `./socket_server`
4. Run the script in another terminal: `./con.sh`

The script simulates **30 concurrent clients** connecting to the server.

⚠️ **Make sure to build your code before running tests!**

### Other Hints

-   There are defined constants (`BUFFER_SIZE`, `MAX_CLIENTS`, `PORT`) in the code skeleton. **Use them!** If you find yourself hard-coding values like `1024` or `8080`, you're doing something wrong.
-   Remember to close the socket at the end of the client program.
-   When testing, make sure you are using `127.0.0.1` as the server IP address.

### Troubleshooting

| Error | Solution |
|-------|----------|
| "Address already in use" | A server is already running. Kill it with `pkill socket_server` or `pkill file_server` |
| "Connection refused" | Make sure the server is running before starting the client |
| "Permission denied" on scripts | Run `chmod +x *.sh` to make scripts executable |
| Build fails with "cmake not found" | Install cmake: `sudo apt install cmake` (Ubuntu/WSL) or `brew install cmake` (macOS) |
| Build fails with "gcc not found" | Install build tools: `sudo apt install build-essential` (Ubuntu/WSL) or `xcode-select --install` (macOS) |

### Criteria

-   (3/6) points for implementing client-to-server socket communication.
-   (6/6) points for implementing the concurrent clients-to-server communication scheme.
-   (0/6) for late submission.
-   Plagiarism is strictly prohibited.

## Simple File Transfer (3 points)

In this section, you'll implement a **simple file transfer** feature for the server-client pair. This is a common test in network programming job assessments!

### Files to Implement
- **`file_server.c`**: Contains TODOs for both socket setup (same as `socket_server.c`) and file receiving
- **`file_client.c`**: Contains TODOs for both socket setup (same as `socket_client.c`) and file sending

💡 **Tip:** The socket setup code (socket, setsockopt, bind, listen, accept for server; socket, inet_pton, connect for client) is the same as in Part 1. You can reuse your implementation!

### Specification

-   The **server** receives file data from the client and saves it to the current working directory (i.e., the `build/` directory where you run the server).
-   The **client** first sends the filename to the server, then sends the file contents.

### Testing

1. **Generate test files** by running `./generator.sh` from the root of GitHub repository:
   ```bash
   chmod +x generator.sh
   ./generator.sh
   ```
   This creates 5 small files (`file1.zip` ~ `file5.zip`, 10MB each) and 2 large files (`bigfile1.zip` ~ `bigfile2.zip`, 50MB each).

2. **Test single file transfer:**
   - In `build/` directory, start the server: `./file_server`
   - In another terminal, run: `./file_client ../file1.zip`

3. **Test concurrent file transfer:**
   - Copy `con_file.sh` to the `build/` directory
   - Update the file paths in `con_file.sh` to point to your test files
   - Run: `./con_file.sh`

4. **Verify file integrity:** If the implementation is correct, files should be copied to the `build/` directory **without corruption**. You can verify using:
   ```bash
   md5sum ../file1.zip ./file1.zip  # Linux
   md5 ../file1.zip ./file1.zip     # macOS
   ```

### Criteria

-   (3/3) points for implementing the simple file transfer successfully.
-   (0/3) for late submission.
-   Plagiarism is strictly prohibited.

## Dive Deeper: Overcoming File Size Limits (1 point)

If you're up for a challenge, consider addressing the file size limitation. Currently, files **larger than 32 MB cannot be transferred correctly**. Try modifying the implementation to remove this restriction and allow unlimited file sizes.

### Hint

Think about why large files fail. Consider:
- How does the server know when the file transfer is complete?
- What happens if the file size exceeds the buffer's capacity to track?

### Specification

Directly modify your code in `file_client.c` and `file_server.c` to enable large file transfer.

### Testing

1. Test with large files:
   - Run the server: `./file_server`
   - Run the client: `./file_client ../bigfile1.zip`

2. Verify the transferred file is **not corrupted**:
   ```bash
   md5sum ../bigfile1.zip ./bigfile1.zip  # Linux
   md5 ../bigfile1.zip ./bigfile1.zip     # macOS
   ```

### Criteria

-   (1/1) point for successfully transferring large files (50MB+) without corruption.
-   (0/1) for late submission.
-   Plagiarism is strictly prohibited.
