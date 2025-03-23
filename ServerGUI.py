from ServerBL import *

class ServerGUI:

    server_logic: ServerBL
    
    def __init__(self):
        self.server_logic = ServerBL()

        # Initialize protocols
        self.server_logic.init_protocols()

        self.__start_server( )

    def __start_server(self):
        ip_to_listen: str = input( "Type IP for the server to listen : " )
        port: str = input( "Enter Port value of the server : " )

        try:
            port: int = int(port)
        except Exception as e:
            print("Invalid port value")
            exit(-1)

        self.server_logic.start_server(ip_to_listen, port)

    def execute(self):
        # Start listening and connecting new clients
        self.server_logic.connection_manager( )