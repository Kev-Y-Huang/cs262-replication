import re
import socket
import select
import sys
import time
from threading import *

from machines import MACHINES
from wire_protocol import pack_packet, unpack_packet
     
# global variables
ERROR_MSG = """<client> Invalid input string, please use format <command>|<text>.
    0|                  -> list user accounts
    1|<username>        -> create an account with name username
    2|<username>        -> login to an account with name username
    3|                  -> logout from current account
    4|                  -> delete current account
    5|<username>|<text> -> send message to username
    6|                  -> deliver all unsent messages to current user"""

FREQUENCY = 1 # Frequency of heartbeat in seconds

class Client:
    def __init__(self):
        self.server = None
        self.username = ""
        self.client_running = True
        self.dest = 0
        self.inputs = []

    # def ping_server(self):
    #     while self.client_running:
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         sock.settimeout(FREQUENCY)
    #         try:
    #             sock.connect((MACHINES[self.dest].ip, MACHINES[self.dest].heart_port))
    #             sock.send("ping".encode(encoding='utf-8'))
    #             sock.recv(2048)
    #             sock.close()
    #         except:
    #             self.server = None
    #             self.attempt_connection()
    #         time.sleep(FREQUENCY)
    
    def attempt_connection(self):
        """
        Attempts to connect to the server at the given host and port.
        """
        while not self.server and self.client_running:
            machine = MACHINES[self.dest]
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.connect((machine.ip, machine.client_port))
                _, op, _ = unpack_packet(self.server.recv(2048))
                
                if op == 0:
                    self.server = None
                    self.dest = (self.dest + 1) % len(MACHINES)
            except KeyboardInterrupt:
                break
            except:
                self.server = None
                self.dest = (self.dest + 1) % len(MACHINES)

        self.inputs.append(self.server)
        output = pack_packet(self.username, 7, "")
        self.server.send(output)
    
    def receive_messages(self):
        try:
            while self.client_running:
                # Use select.select to poll for messages
                read_sockets, _, _ = select.select(self.inputs, [], [], 0.1)

                for sock in read_sockets:
                    # If the socket is the server socket, accept as a connection
                    if sock == self.server:
                        data = sock.recv(1024)
                        if data:
                            # Read in the data as a big-endian integer
                            self.username, _, output = unpack_packet(data)
                            print(output)
                        # If there is no data, then the connection has been closed
                        else:
                            self.server = None
                            sock.close()
                            self.inputs.remove(sock)
                            self.attempt_connection()
        finally:
            # Close all socket connections
            for sock in self.inputs:
                sock.close()

    def send_user_input(self):
        # Continuously listen for user inputs in the terminal
        while self.client_running:
            usr_input = input()
            # Exit program upon quiting
            if usr_input == "quit":
                self.client_running = False
            # Parse message if non-empty
            elif usr_input != '':
                # Parses the user input to see if it is a valid input
                match = re.match(r"(\d)\|((\S| )*)", usr_input)
                # Check if the input is valid
                if match:
                    # Parse the user input into op_code and content
                    op_code, content = int(match.group(1)), match.group(2)
                    if len(content) >= 280:
                        print('<client> Message too long, please keep messages under 280 characters')
                    else:
                        # Pack the op_code and content and send it to the server
                        output = pack_packet(self.username, op_code, content)
                        not_sent = True
                        while not_sent:
                            # Try to send the message to the server
                            try:
                                self.server.send(output)
                                not_sent = False
                            # If the message cannot be sent, connect to new server
                            except:
                                self.server.close()
                                self.server = None
                                self.attempt_connection()
                else:
                    print(ERROR_MSG)
       

def main():
    client = Client()

    client.attempt_connection()

    threads = []

    try:
        # Separate thread for processing incomming messages from the server
        threads.append(Thread(target=client.receive_messages))
        threads.append(Thread(target=client.send_user_input))
        # threads.append(Thread(target=client.ping_server))

        for eachThread in threads:
            eachThread.start()
        while client.client_running:
            continue
    except:
        client.client_running = False
        for eachThread in threads:
            eachThread.join()
        sys.exit()


if __name__ == "__main__":
    main()