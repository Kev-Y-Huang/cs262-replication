# CS 262 Replication

## Description

This is an implementations for Design Exercise 3 for Harvard's
CS 262: Introduction to Distributed Computing.

## How to run the app

1. Modify the `config.yaml` file to change the host so that it matches in the server and client. To get `host`, you'll need the the IP address of the machine of the server (run `ipconfig getifaddr en0` for Mac or `ipconfig getifaddr eth0` for Linux or run `ipconfig` and look for the IPv4 address for Windows).

2. Navigate into the `chat` folder and run `python3 server.py` on the server first, and then on the other machine navigate into the `chat` folder and run `python3 client.py` on the client. 

3. After the client has connected to the server, type in a command in the client terminal, following the commands below.

### Commands for the client

All messages sent by the client be an op code followed by the pipe "|" character.

```
Format: <command>|<text>
0|<regex>           -> list user accounts
1|<username>        -> create an account with name username
2|<username>        -> login to an account with name username
3|                  -> logout from current account
4|                  -> delete current account
5|<username>|<text> -> send message to username
6|                  -> deliver all unsent messages to current user
```

### Disconnecting the client

To shut down the client and disconnect from the server, type `quit` in the client terminal. 

## How to run the tests

Navigate into the `chat` folder and run `python3 tests.py`. Tests should all pass with a `All tests passed!` message in the console. 

## Design Considerations

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


## Folder Structure
```
├── chat                        # All of the code is here
|   ├── wire                    # wire implementation in here
|   |   ├── chat_service.py     # Code for defining classes (User, Chat) used by the client and server
|   |   ├── client.py           # Client specific code to wire protocol
|   |   ├── server.py           # Server specific code to wire protocol
|   |   └── wire_protocol.py    # Code for defining the wire protocol
|   ├── __init__.py	            # Initializes application from config file
│   ├── client.py               # Contains the common code for client
│   ├── server.py               # Contains the common code for server
|   ├── tests.py                # Unit tests for the wire protocol application
|   └── utils.py                # Defines common functions used by the application
├── .gitignore	
├── config.yaml                 # Configuration file for host and port
├── requirements_macOS.txt      # Dependencies for Mac
├── requirements_win64.txt      # Dependencies for Windows
├── NOTEBOOK.md                 # Engineering notebook	
└── README.md                   # README
```