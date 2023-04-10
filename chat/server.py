import argparse
import logging
import select
import socket
import sys
import csv
import time
import threading
import os

from queue import Queue

from chat_service import Chat, User
from wire_protocol import pack_packet, unpack_packet

from machines import MACHINES, get_other_machines

# global variables and configurations
logging.basicConfig(format='[%(asctime)-15s]: %(message)s', level=logging.INFO)

FREQUENCY = 1 # Frequency of heartbeat in seconds

class Server:
    def __init__(self, server_number):
        # Setting up the server
        self.server_number = server_number
        self.machine = MACHINES[server_number]
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.machine.ip, self.machine.client_port))
        self.server.listen(10)

        # Create a Chat object to handle all the chat logic
        logging.info('Starting Wire Protocol Server')
        self.chat_app = Chat()

        self.server_running = True

        self.queue = Queue()
        self.lockReady = threading.Lock()
        self.is_leader = False

        self.backups = get_other_machines(server_number)

    def setup_connections(self):
        """
        Sets up the connections to the other servers
        """
        for backup in self.backups:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            while sock.connect_ex((backup.ip, backup.heart_port)) != 0:
                logging.info(f"Heart Port Failed for {backup.id}")
                time.sleep(1)
        
        logging.info("Connection success")


    def instantiate_from_csv(self):
        """
        This function is used to re-instantiate the server from a csv file to its original state
        """
        # if file does not exist, create empty csv file
        if not os.path.exists(f'./chat/logs/{self.server_number}.csv'):
            with open(f'./chat/logs/{self.server_number}.csv', 'w') as csv_file:
                pass
        else:
            with open(f'./chat/logs/{self.server_number}.csv', 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                for line in csv_reader:
                    username, op_code, contents = line
                    user = User(None, username)
                    # import pdb; pdb.set_trace()
                    responses = self.chat_app.handler(user, int(op_code), contents)
                    # print(responses)
                

    def handle_client(self, conn):
        # Define a user object to keep track of the user and state for the thread
        curr_user = User(conn)

        inputs = [conn]

        try:
            # Continuously poll for messages while exit event has not been set
            while self.server_running:
                # Use select.select to poll for messages
                read_sockets, _, _ = select.select(inputs, [], [], 0.1)

                for sock in read_sockets:
                    # If the socket is the server socket, accept as a connection
                    if sock == conn:
                        data = sock.recv(1024)
                        if data:
                            curr_user.username, op_code, contents = unpack_packet(data)

                            if int(op_code) == 7:
                                sock.send(pack_packet("", 1, ""))
                            else:
                                """prints the message and address of the
                                user who just sent the message on the server
                                terminal"""
                                print(f"<{addr[0]}|{curr_user.username}> {op_code}|{contents}")

                                self.queue.put((curr_user, int(op_code), contents))
                        # If there is no data, we remove the connection
                        else:
                            self.queue.put((curr_user, 3, ""))
                            for sock in inputs:
                                sock.close()
        except:
            for sock in inputs:
                sock.close()


    def broadcast_update(self, username: str, op_code: int, contents: str):
        """
        Takes care of state-updates.
        """
        if not self.is_leader:
            return
        for backup in self.backups:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((backup.ip, backup.internal_port))
            conn.send(pack_packet(username, op_code, contents))
    
    def listen_internal(self):
        self.internal_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.internal_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.internal_socket.bind((self.machine.ip, self.machine.internal_port))
        self.internal_socket.listen(5)

        inputs = [server.internal_socket]

        try:
            while self.server_running:
                read_sockets, _, _ = select.select(inputs, [], [], 0.1)

                for sock in read_sockets:
                    # If the socket is the server socket, accept as a connection
                    if sock == self.internal_socket:
                        client, _ = sock.accept()
                        inputs.append(client)
                    # Otherwise, read the data from the socket
                    else:
                        data = sock.recv(1024)
                        if data:
                            username, op_code, contents = unpack_packet(data)
                            curr_user = User(None, username)
                            self.queue.put((curr_user, int(op_code), contents))
                        # If there is no data, then the connection has been closed
                        else:
                            sock.close()
                            inputs.remove(sock)
        except Exception as e:
            print(e)
            for conn in inputs:
                conn.close()
            self.heart_socket.close()
    
    def listen_heartbeat(self):
        self.heart_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.heart_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.heart_socket.bind((self.machine.ip, self.machine.heart_port))
        self.heart_socket.listen(5)

        inputs = [server.heart_socket]

        try:
            while self.server_running:
                read_sockets, _, _ = select.select(inputs, [], [], 0.1)

                for sock in read_sockets:
                    # If the socket is the server socket, accept as a connection
                    if sock == self.heart_socket:
                        client, _ = sock.accept()
                        inputs.append(client)
                    # Otherwise, read the data from the socket
                    else:
                        data = sock.recv(1024)
                        if data:
                            sock.send("ping".encode(encoding='utf-8'))
                        # If there is no data, then the connection has been closed
                        else:
                            sock.close()
                            inputs.remove(sock)
        except Exception as e:
            print(e)
            for conn in inputs:
                conn.close()
            self.heart_socket.close()

    def elect_leader(self):
        for backup in self.backups:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(FREQUENCY)
            try:
                sock.connect((backup.ip, backup.heart_port))
                sock.send("ping".encode(encoding='utf-8'))
                sock.recv(2048)
                sock.close()
            except:
                logging.info(f"Backup {backup.id} is not up")
                self.backups.remove(backup)
                pass

        if not self.is_leader:
            if len(self.backups) == 0 or self.server_number < min([server.id for server in self.backups]):
                self.is_leader = True
                logging.info(f"{self.server_number} is elected leader")

    def send_heartbeat(self):
        while self.server_running:
            self.elect_leader()
            time.sleep(FREQUENCY)

    def handle_queue(self):
        while self.server_running:
            if not self.queue.empty():
                user, op_code, contents = self.queue.get()
                name = user.get_name()
                logging.info(user.get_name(), op_code, contents)
                responses = self.chat_app.handler(user, op_code, contents)
                
                if op_code > 0:
                    # write user, op_code, contents to csv file
                    with open(f'./chat/logs/{self.server_number}.csv', 'a', newline='') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow([name, op_code, contents])

                if self.is_leader:
                    # update other servers
                    self.broadcast_update(name, op_code, contents)
                    # Iterate and send out each new response generated by the server
                    for recip_conn, response in responses:
                        if recip_conn:
                            output = pack_packet(user.get_name(), 1, response)
                            try:
                                recip_conn.send(output)
                            except Exception as e:
                                logging.info(e)

                            time.sleep(0.1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replicated Chat Server")

    parser.add_argument("--server_number", "-s", choices=[0, 1, 2], type=int)
    args = parser.parse_args()

    server = Server(args.server_number)
    server.instantiate_from_csv()
    threads = []

    try:
        threads.append(threading.Thread(target=server.listen_heartbeat))
        threads.append(threading.Thread(target=server.listen_internal))
        threads.append(threading.Thread(target=server.handle_queue))
        
        for eachThread in threads:
            eachThread.start()

        server.setup_connections()
        server.elect_leader()

        heartbeat_thread = threading.Thread(target=server.send_heartbeat)
        heartbeat_thread.start()
        threads.append(heartbeat_thread)

        inputs = [server.server]
        
        while server.server_running:
            read_sockets, _, _ = select.select(inputs, [], [], 0.1)

            for sock in read_sockets:
                conn, addr = sock.accept()

                if server.is_leader:
                    # prints the address of the user that just connected
                    logging.info(addr[0] + " connected.")
                    conn.send(pack_packet("", 1, "Server is the leader"))
                    # creates a new thread for incoming client
                    new_client = threading.Thread(target=server.handle_client, args=(conn,))
                    new_client.start()
                    threads.append(new_client)
                else:
                    # prints the address of the user that just connected
                    logging.info(addr[0] + " tried connecting.")

                    conn.send(pack_packet("", 0, "Server is not leader"))
                    conn.close()
    except:
        logging.info('Stopping Server.')
        server.server_running = False

        # if server.socket1 is not None:
        #     server.socket1.close()
        # if server.socket2 is not None:
        #     server.socket2.close()
        for eachThread in threads:
            eachThread.join()
        sys.exit()
