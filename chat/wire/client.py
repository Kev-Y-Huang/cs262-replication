
from threading import *

from wire.wire_protocol import unpack_packet


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
