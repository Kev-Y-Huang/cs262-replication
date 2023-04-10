import re
import socket
import sys
from threading import *

from utils import get_server_config_from_file
from wire_protocol import pack_packet, unpack_packet
     
# global variables
YAML_CONFIG_PATH = '../config.yaml'
IP_ADDRESS, PORTS = get_server_config_from_file(YAML_CONFIG_PATH)
ERROR_MSG = """<client> Invalid input string, please use format <command>|<text>.
    0|                  -> list user accounts
    1|<username>        -> create an account with name username
    2|<username>        -> login to an account with name username
    3|                  -> logout from current account
    4|                  -> delete current account
    5|<username>|<text> -> send message to username
    6|                  -> deliver all unsent messages to current user"""

class ReceiveMessages(Thread):
    def __init__(self, server):
        super().__init__()
        self.__server = server

    def run(self):
        while True:
            try:
                message = self.__server.recv(1024)
                _, data = unpack_packet(message)
                print(data)
            except:
                break
       

def main():
    i = 0
    # Setup connection to server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((IP_ADDRESS, PORTS[i]))

    # Separate thread for processing incomming messages from the server
    server_listening = ReceiveMessages(server)
    server_listening.start()

    # Continuously listen for user inputs in the terminal
    while True:
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
                    output = pack_packet(op_code, content)
                    not_sent = True
                    while not_sent:
                        # Try to send the message to the server
                        try:
                            server.send(output)
                            not_sent = False
                        # If the message cannot be sent, connect to new server
                        except:
                            server.close()
                            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            server.connect((IP_ADDRESS, PORTS[(i + 1) % 3]))
            else:
                print(ERROR_MSG)

    # Close the connection to the server and wait for server_listening to finish
    server.close()
    server_listening.join()
    
    sys.exit()


if __name__ == "__main__":
    main()