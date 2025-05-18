from ServerBL import *


class ServerGUI:

    server_logic: ServerBL
    
    def __init__(self):
        self.server_logic = ServerBL()

        self.server_logic.init_protocols()

        self.__start_server()

    def __start_server(self):
        """
        starts up the server on the inputted port
        :return:
        """
        port: str = input("Enter Port value of the server : ")
        ip_to_listen = "0.0.0.0"
        try:
            port: int = int(port)
        except Exception as e:
            print("Invalid port value")
            exit(-1)

        self.server_logic.start_server(ip_to_listen, port)

    def execute(self):
        """
        starts listening and connecting new clients
        :return:
        """
        self.server_logic.connection_manager()