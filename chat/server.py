import argparse
import logging
import select
import socket
import sys
import csv
import time
import threading

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

        self.thread_running = True

        self.queue = Queue()
        self.lockReady = threading.Lock()
        self.is_leader = False

        self.backups = get_other_machines(server_number)


    def instantiate_from_csv(self):
        """
        This function is used to re-instantiate the server from a csv file to its original state
        """
        with open(f'{self.server_number}.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for line in csv_reader:
                user, op_code, contents = line
                responses = self.chat_app.handler(user, op_code, contents)
                

    def handle_client(self, conn):
        # Define a user object to keep track of the user and state for the thread
        curr_user = User(conn)

        inputs = [self.server]

        # Continuously poll for messages while exit event has not been set
        while self.thread_running:
            try:
                # Use select.select to poll for messages
                read_sockets, _, _ = select.select(inputs, [], [], 0.1)

                for sock in read_sockets:
                    # If the socket is the server socket, accept as a connection
                    if sock == self.server:
                        client, _ = sock.accept()
                        inputs.append(client)
                    # Otherwise, read the data from the socket
                    else:
                        data = sock.recv(1024)
                        if data:
                            op_code, contents = unpack_packet(data)
                            self.queue.put((curr_user, int(op_code), contents))
                        # If there is no data, we remove the connection
                        else:
                            self.queue.put((curr_user, 3, ""))
            except:
                break

    def broadcast_update(self, user, op_code, contents):
        """
        Takes care of state-updates.
        NOTE: We let this be called on any kind of request, but notice
        that we only have to actually do stuff on account changes or messages
        NOTE: If this machine does not have `is_primary` we'll do nothing
        """
        if not self.is_leader:
            return
        for sibling in self.backups:
            pack_packet()
    
    def listen_heartbeat(self):
        self.health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.health_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.health_socket.bind((self.machine.ip, self.machine.health_port))
        self.health_socket.listen(5)
        try:
            while self.thread_running:
                conn, _ = self.health_socket.accept()
                conn.recv(2048)
                conn.send("ping".encode(encoding='utf-8'))
                conn.close()
        except:
            self.health_socket.close()

    def send_heartbeat(self):
        time.sleep(FREQUENCY)
        while self.thread_running:
            for backup in self.backups:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(FREQUENCY)
                try:
                    sock.connect((backup.ip, backup.health_port))
                    sock.send("ping".encode(encoding='utf-8'))
                    sock.recv(2048)
                    sock.close()
                except:
                    # TODO deal with error messaging
                    # print_error(f"Backup {sibling.name} is dead")
                    self.backups.remove(backup)

            if not self.is_leader:
                if self.server_number < min([server.id for server in self.backups]):
                    self.is_leader = True
                    print("elected leader")

                    # # TODO figure out takeover stuff
                    # print(f"Machine {self.identity.name} is now primary!")
                    # # Self-trigger an internal request to free control
                    # takeover_req = TakeoverRequest()
                    # self.internal_requests.put(takeover_req)
            time.sleep(FREQUENCY)

    def handle_queue(self):
        while self.thread_running:
            user, op_code, contents = self.queue.get()
            responses = self.chat_app.handler(user, op_code, self.server_number, contents)

            # write user, op_code, contents to csv file
            with open(f'{self.server_number}.csv', 'a') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([user, op_code, contents])

            if self.is_leader:
                # Iterate and send out each new response generated by the server
                for recip_conn, response in responses:
                    output = pack_packet(1, response)
                    recip_conn.send(output)
                    id += 1
                    time.sleep(0.1)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replicated Chat Server")

    parser.add_argument("--server_number", "-s", choices=[0, 1, 2], type=int)
    args = parser.parse_args()

    server = Server(args.server_number)
    threads = []
    try:
        threads.append(threading.Thread(target=server.listen_heartbeat))
        threads.append(threading.Thread(target=server.send_heartbeat))
        threads.append(threading.Thread(target=server.handle_queue))
        
        for eachThread in threads:
            eachThread.start()
        while server.thread_running and server.is_leader:
            # Listen for and establish connection with incoming clients
            conn, addr = server.server.accept()

            # prints the address of the user that just connected
            logging.info(addr[0] + " connected.")
            # creates a new thread for incoming client
            new_client = threading.Thread(target=server.handle_client, args=(conn))
            new_client.start()
            threads.append(new_client)
    except KeyboardInterrupt:
        logging.info('Stopping Server.')
        server.thread_running = False

        if server.socket1 is not None:
            server.socket1.close()
        if server.socket2 is not None:
            server.socket2.close()
        for eachThread in threads:
            eachThread.join()
        sys.exit()
