class Machine:
    """
    A class that represents the identity of a machine. Most crucially
    this stores information about which ip/port the machine is listening
    on, as well as which other machines it is responsible for connecting
    to.
    """

    def __init__(
        self,
        id: int,
        ip: str,
        internal_port: int,
        client_port: int,
        health_port: int,
        # notif_port: int,
        # num_listens: int,
        # connections: List[str],
    ) -> None:
        # The name of the machine (in our experiments "A" | "B" | "C")
        self.id = id
        # The ip address the machine should listen on for new connections
        self.ip = ip
        # The port the machine should listen on for connections from other machines
        self.internal_port = internal_port
        # The port the machine should listen on for connections to clients
        self.client_port = client_port
        # The port the machine should listen on for health checks
        self.health_port = health_port

        # # The port the machine should listen on for notification sub requests
        # self.notif_port = notif_port
        # # The number of connections the machine should listen for
        # self.num_listens = num_listens
        # # The names of the machines that this machine should connect to
        # self.connections = connections


MACHINE_A = Machine(
    id=0,
    ip="localhost",
    internal_port=26201,
    client_port=26202,
    health_port=26203,

    # notif_port=26204,
    # num_listens=2,
    # connections=[]
)

MACHINE_B = Machine(
    id=1,
    ip="localhost",
    internal_port=26211,
    client_port=26212,
    health_port=26213,

    # notif_port=50064,
    # num_listens=1,
    # connections=["A"]
)

MACHINE_C = Machine(
    id=2,
    ip="localhost",
    internal_port=26221,
    client_port=26222,
    health_port=26223,

    # notif_port=50074,
    # num_listens=0,
    # connections=["A", "B"],
)

# Create a mapping from machine name to information about it
MACHINES = [MACHINE_A, MACHINE_B, MACHINE_C]
