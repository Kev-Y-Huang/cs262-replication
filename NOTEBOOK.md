
## Design Considerations

### Architecture Overview

We implemented the primary secondary backup model using our custom wire protocol between client and server and socket communication with one primary replica and two secondary replicas. This allowed us to be 2-fault tolerant, since if 2 servers go down, we will still have one server left that will allow the user to interact with the system with no noticeable effect. We ended up using logs (csv files for each of the servers) to keep state to ensure persistence. We also implemented a heartbeat protocol to ensure that the servers are still alive and to detect when a server goes down. If a server goes down, we automatically elected a new leader and continued to serve the client’s requests.

### Persistence

- When all the servers go down and are brought back up the system should still work as expected and all unsent messages should still be - queued to send
- Achieve persistence through saving the state of each of the servers to database/file
    - We choose to save these to separate files in order to have a state file for each machine, which would be the case in the real-world
- We use log files to keep track of every single message that has been sent to the server
    - Once all the servers die, we can rerun commands in the log files to instantiate the original state before the servers died

### 2-Fault Tolerance for Crash/Failstop Failures

Under the primary-backup protocol, 2-fault tolerance for crash/failstop failures can be achieved by having 3 machines that are in constant communication with each other such that when one machine is ingesting a request, the internal state of each of those machines is the same. This guarantees that even if 2 of those machines (2-fault) go down, there is still 1 machine left to take on the primary role and serve the client’s requests.
- To ensure strong consistency, we persist any update that is made to the state of the primary server to the backup servers.
- This is implemented by sending updates using the same wire protocol that is used for communication between client and server as it is already rich in data (user information, operation, and operation input) that informs the update to the server instance.

#### Heartbeats

A critical aspect of peer-to-peer communication that is necessary for a successful primary-backup protocol is that “heartbeats” are regularly sent such that each of the servers know whether or not other peer servers are still online. This is implemented through 2 processes:
- listen_heartbeat: This function listens for any messages that are sent over a “heartbeat” socket and replies immediately with a heartbeat response.
- send_heartbeat: This function sends out “heartbeat” messages on a regular interval (set to 1 second but could be set to any value depending on how restrictive we want to be) to peer server processes and waits 1 second for responses sent back over the connection.

#### Leader Election

In the event that a “heartbeat response” is not heard from one of the peer server processes, that initiates a leader election process. First, we evaluate if a new leader needs to be chosen. If so, we then begin the process of electing a new leader.

## Testing

We performed testing manually and through our old unit tests from Design Exercise 1. We manually tested several cases:

- Two fault tolerance: clients experience was still the same after killing two servers, and stopped after killing the third
- Persistence: after all servers go down and come back on, there was no impact on the client
- Tested on two separate machines, with clients on either machine as well

## Working Log


### April 9th

* For persistence, we either need to save the logs of each server to a database or save the logs to a file
    * File is probably more straightforward
        * Each server could iterate through the logs and then execute the statments to get to the current state
* Heartbeat
    * We will have a heartbeat thread that will send a heartbeat to all the other servers every 1 seconds
    * If a server a server isn't able to connect, it will assume that the server is down
    * If a server is down, we will need to pick a new leader


### April 8th

* For fault tolerance, we will use the primary backup model
    * We will have three servers - one is the primary, the other two are backup
        * Determined by the order in which they are created
        * If the first server (which will be the primary server) goes down, the next lowest server ID will be the primary server
    * Clients knows all the servers
        * If primary server goes down, the client will ping all the other servers until it finds the primary server
        * If a client pings a server that is not the primary, the request will not be processed
* Server Process Architecture:
    * Threads:
        * Listen for incoming messages from clients
        * Manage primary/backup process and elections
        * Worker for running through queue
        * Heartbeat/fault detector
* Client Process Architecture:
    * Threads:
        * Listen for messages from user input and from server
* Implementing state updates
    * Whenever a state is updated, it needs to:
        * Lock the resource
        * Send an update to all the replicants
        * Wait for acknowledgement from at least one of the replicants
        * Unlock the resource and send back a response to the client if needed

