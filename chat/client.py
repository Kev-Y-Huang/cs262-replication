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

class Client:
    def __init__(self):
        self.__server = None
        self.__username = ""
        self.__thread_running = True
        self.__dest = 0
        self.__inputs = []

    def ping_server(self):
        """
        Checks the primary regularly and relogs in if needed
        """
        FREQUENCY = 1
        time.sleep(FREQUENCY)
        while True:
            okay = self.connector.ping_server()
            if not okay:
                self.connector.attempt_connection()
                self.relogin()
            time.sleep(FREQUENCY)

    def attempt_connection(self):
        """
        Attempts to connect to the server at the given host and port.
        """
        while not self.__server:
            print("test")
            machine = MACHINES[self.__dest]
            try:
                self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__server.connect((machine.ip, machine.client_port))
                user, op, _ = unpack_packet(self.__server.recv(2048))
                if op == 0:
                    self.iconn = None
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.iconn = None
            self.__dest = (self.__dest + 1) % len(MACHINES)

        print(self.__dest)
        self.__inputs.append(self.__server)
    
    
    def receive_messages(self):
        while self.__thread_running:
            # Use select.select to poll for messages
            read_sockets, _, _ = select.select(self.__inputs, [], [], 0.1)

            for sock in read_sockets:
                # If the socket is the server socket, accept as a connection
                if sock == self.__server:
                    client, _ = sock.accept()
                    self.__inputs.append(client)
                # Otherwise, read the data from the socket
                else:
                    data = sock.recv(1024)
                    if data:
                        # Read in the data as a big-endian integer
                        self.__username, _, output = unpack_packet(data)
                        print(output)
                    # If there is no data, then the connection has been closed
                    else:
                        sock.close()
                        self.__inputs.remove(sock)

        # Close all socket connections
        for sock in self.__inputs:
            sock.close()
        


    def send_user_input(self):
        # Continuously listen for user inputs in the terminal
        while self.__thread_running:
            usr_input = input()
            # Exit program upon quiting
            if usr_input == "quit":
                raise KeyboardInterrupt
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
                        output = pack_packet(self.__username, op_code, content)
                        not_sent = True
                        while not_sent:
                            # Try to send the message to the server
                            try:
                                self.__server.send(output)
                                not_sent = False
                            # If the message cannot be sent, connect to new server
                            except:
                                self.__server.close()
                                self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                machine = MACHINES[(self.__dest + 1) % 3]
                                self.__server.connect((machine.ip, machine.client_port))
                else:
                    print(ERROR_MSG)
       

def main():
    i = 0
    client = Client()

    client.attempt_connection()

    threads = []

    try:
        # Separate thread for processing incomming messages from the server
        threads.append(Thread(target=client.receive_messages))
        threads.append(Thread(target=client.send_user_input))

        for eachThread in threads:
            eachThread.start()
        while client.__thread_running:
            continue
    except:
        client.__thread_running = False
        for eachThread in threads:
            eachThread.join()
        sys.exit()


if __name__ == "__main__":
    main()