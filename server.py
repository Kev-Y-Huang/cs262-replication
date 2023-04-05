import logging
import socket
import sys
from _thread import *
from concurrent import futures

import grpc
import grpc_proto.chat_pb2_grpc as chat_pb2_grpc
from grpc_proto.server import ChatServer
from utils import get_server_config_from_file
from wire.server import client_thread
from wire.chat_service import Chat

# global variables and configurations
YAML_CONFIG_PATH = '../config.yaml'
IP_ADDRESS, PORT = get_server_config_from_file(YAML_CONFIG_PATH)
logging.basicConfig(format='[%(asctime)-15s]: %(message)s', level=logging.INFO)


def main():
    # Check if enough arguments are passed
    if len(sys.argv) != 2:
        print('Error: Incorrect Usage\n\
              Correct usage: server.py [implementation]')
        sys.exit()

    # Wire protocol implementation of the client
    if sys.argv[1] == 'wire':
        # Setting up the server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((IP_ADDRESS, PORT))
        server.listen(5)

        # Create a Chat object to handle all the chat logic
        logging.info('Starting Wire Protocol Server')
        chat_app = Chat()

        while True:
            try:
                # Listen for and establish connection with incoming clients
                conn, addr = server.accept()

                # prints the address of the user that just connected
                logging.info(addr[0] + " connected.")

                # creates a new thread for incoming client
                start_new_thread(client_thread, (chat_app, conn, addr))
            except KeyboardInterrupt:
                logging.info('Stopping Server.')
                break

        # Close the server socket
        conn.close()
        server.close()
    else:
        print('Error: Incorrect Usage\n\
              Correct usage: Implementation must be either "wire" or "grpc"')
    
    sys.exit()

if __name__ == "__main__":
    main()