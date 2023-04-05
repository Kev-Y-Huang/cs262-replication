import struct

# Packet format:
# - 4 byte unsigned integer for data length (N)
# - 1 byte unsigned integer for operation code
# - N bytes for packet data


def pack_packet(operation: int, input: str) -> bytes:
    data = input.encode('utf-8')
    return struct.pack("!IB", len(data), operation) + data


def unpack_packet(packet: bytes) -> tuple:
    data_len, operation = struct.unpack("!IB", packet[:5])
    data = packet[5:5 + data_len]
    output = data.decode('utf-8')
    return operation, output