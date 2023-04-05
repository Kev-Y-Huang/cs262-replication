# Python program to implement server side of chat room.
import time

from _thread import *

from wire.chat_service import User
from wire.wire_protocol import pack_packet, unpack_packet


def client_thread(chat_app, conn, addr):
    # sends a message to the client whose user object is conn
    message = '<server> Connected to server'
    output = pack_packet(1, message)
    conn.send(output)

    # Define a user object to keep track of the user and state for the thread
    curr_user = User(conn)

    while True:
        try:
            data = conn.recv(1024)

            if data:
                op_code, contents = unpack_packet(data)

                """prints the message and address of the
                user who just sent the message on the server
                terminal"""
                print(f"<{addr[0]}> {op_code}|{contents}")

                responses = chat_app.handler(
                    curr_user, int(op_code), contents)

                # Iterate and send out each new response generated by the server
                for recip_conn, response in responses:
                    output = pack_packet(1, response)
                    recip_conn.send(output)
                    time.sleep(0.1)

            # If data has no content, we remove the connection
            else:
                chat_app.handler(curr_user, 3)

        except:
            break
