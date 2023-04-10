import re
import socket
import sys
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
    def __init__(self, server):
        self.__server = server
        self.__username = ""
        self.__thread_running = True

    def receive_messages(self):
        try:
            while self.__thread_running:
                message = self.__server.recv(1024)
                self.__username, _, data = unpack_packet(message)
                print(data)
        except:
            return
        
    def send_user_input(self):
        # Continuously listen for user inputs in the terminal
        while self.__thread_running:
            usr_input = input()
            # Exit program upon quiting
            if usr_input == "quit":
                break
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
                                self.__server.connect((IP_ADDRESS, PORTS[(i + 1) % 3]))
                else:
                    print(ERROR_MSG)
       

def main():
    i = 0
    # Setup connection to server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((MACHINES[0].ip, MACHINES[0].client_port))

    client = Client(server)
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