### Core Chord Protocol
- `find_successor (id)`
    
   Locates the successor for a given ID. It first checks if the ID is managed by the immediate successor (i.e. whether ID falls in $(node\_id, successor]$). If not, it routes the query to the closest preceding node found in the local finger table for recursive lookup.

   Remote lookups are safeguarded by `try-except` blocks to handle unexpected disconnections and maintain node stability.

- `closest_preceding_node (id)`

   Scans the local finger table in reverse order (from $m$ to $1$) to identify the highest known node whose ID falls in $(node\_id, id)$.

- `create ()`

   Initializes a new, standalone Chord ring. The node configures itself as the sole member by setting its predecessor to `None` and its immediate successor to itself.

- `join (existing_node_addr)`

   Integrates the current node into an existing Chord network. It queries a known entry node to find its successor and subsequently triggers a  `transfer_keys` request to assume responsibility for its designated ID space.

- `stabilize ()`
  
   Periodically verifies and updates the node's immediate successor to maintain ring consistency. It queries the successor for its predecessor and updates its own pointer if a new node has intervened. 
   
   Remote calls are wrapped in `try-except` blocks to gracefully handle sudden successor disconnections.

- `notify (node_addr)`
  
   Processes notifications from other nodes. It updates the current node's predecessor pointer if it is `None` or if the notifying node's ID falls in $(predecessor, node\_id)$.

- `fix_fingers ()`
   
   Periodically refreshes a specific entry in the finger table. This ensures that the node's routing paths remain accurate and up-to-date as the network topology changes (e.g., when nodes join or leave the ring).

### Key Storage

- `put (key, value)`

   Hashes a given string key to determine its target ID in the Chord space, locates the responsible successor, and stores the key-value pair on that remote node using a remote procedure call.

- `get (key)`

   Computes the hash of a given key to determine its target ID, locates the responsible node in the ring, and retrieves the associated value via RPC.

- `transfer_keys (new_node_addr)`

   Safely migrates keys whose hash falls in $(node\_id, new\_node\_addr]$ to a newly joined predecessor via RPC, using a list copy to avoid iteration errors while deleting transferred data locally.