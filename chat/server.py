import argparse
import logging
import socket
import sys
import sqlite3
from threading import Event, Thread

from wire.chat_service import Chat
from wire.server import client_thread

# global variables and configurations
YAML_CONFIG_PATH = '../config.yaml'
IP_ADDRESS = 'localhost'
PORTS = [5555, 6666, 7777]
logging.basicConfig(format='[%(asctime)-15s]: %(message)s', level=logging.INFO)


def run_server(server_number):
    # Setting up the server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP_ADDRESS, PORTS[server_number]))
    server.listen(5)

    # Create a Chat object to handle all the chat logic
    logging.info('Starting Wire Protocol Server')
    chat_app = Chat()

    # read the id column from latest entry by timestamp in the database
    sql_conn = sqlite3.connect('./logs/chat.db')
    c = sql_conn.cursor()
    id = c.execute("SELECT id FROM messages ORDER BY timestamp DESC LIMIT 1")

    while True:
        try:
            # Listen for and establish connection with incoming clients
            conn, addr = server.accept()

            # prints the address of the user that just connected
            logging.info(addr[0] + " connected.")
            # creates a new thread for incoming client
            start_new_thread(client_thread, (chat_app, conn, addr, id))
        except KeyboardInterrupt:
            logging.info('Stopping Server.')
            break

    # Close the server socket
    conn.close()
    server.close()
    
    sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replicated Chat Server")

    parser.add_argument("--server_number", "-s", type=int)

    args = parser.parse_args()
    
    run_server(args.server_number)
