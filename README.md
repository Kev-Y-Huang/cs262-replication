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