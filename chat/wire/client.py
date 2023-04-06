
from threading import *
import sqlite3

from wire.wire_protocol import unpack_packet

class ReceiveMessages(Thread):
    def __init__(self, server):
        super().__init__()
        self.__server = server

    def run(self):
        sql_conn = sqlite3.connect('../logs/chat.db')
        c = sql_conn.cursor()
        while True:
            try:
                message = self.__server.recv(1024)
                _, data = unpack_packet(message)
                # get all values in the data column of the database
                messages = c.execute("SELECT data FROM messages")
                # check if data in messages
                if data in messages:
                    # delete the earliest row based on timestamp where the message is from the database
                    c.execute("DELETE FROM messages WHERE data = ? ORDER BY timestamp ASC LIMIT 1", (data,))
                    break
                print(data)
            except:
                break
