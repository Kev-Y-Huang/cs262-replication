from typing import List

class Machine:
    """
    A class that represents the identity of a machine. Stores information about which 
    ip/port the machine is listening on and what machines it connects to.
    """

    def __init__(
        self,
        id: int,
        ip: str,
        client_port: int,
        internal_port: int,
        heart_port: int
    ) -> None:
        self.id = id
        self.ip = ip
        self.client_port = client_port
        self.internal_port = internal_port
        self.heart_port = heart_port


MACHINE_ZERO = Machine(
    id=0,
    # ip="localhost",
    ip="10.250.29.21",
    client_port=26201,
    internal_port=26202,
    heart_port=26203
)

MACHINE_ONE = Machine(
    id=1,
    # ip="localhost",
    ip="10.250.29.21",
    client_port=26211,
    internal_port=26212,
    heart_port=26213
)

MACHINE_TWO = Machine(
    id=2,
    # ip="localhost",
    ip="10.250.193.46",
    client_port=26221,
    internal_port=26222,
    heart_port=26223
)

# Create a mapping from machine name to information about it
MACHINES = [MACHINE_ZERO, MACHINE_ONE, MACHINE_TWO]

def get_other_machines(id: int) -> List[Machine]:
    """
    Returns a list of all the machines that are not the machine with the given id.
    """
    return [machine for machine in MACHINES if machine.id != id]
