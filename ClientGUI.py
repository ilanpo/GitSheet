from ClientBL import ClientBl as CBL


class ClientGUI:
    clientbl: CBL

    def __init__(self):
        self.last_error = "no error registered"
        self.userid = None
        self.project_id = "67b4e1c937d13c178165618e"

    def init_protocols(self):
        self.clientbl = CBL()
        self.clientbl.init_protocols()

    def start_client(self, ip, port):
        self.clientbl.start_client(ip, port)

    def load_projects(self):
        return self.clientbl.request_projects()

    def load_nodes(self):
        return self.clientbl.request_data("nodes", self.project_id)

    def load_veins(self):
        return self.clientbl.request_data("veins", self.project_id)


if __name__ == "__main__":
    Client = ClientGUI()
    Client.init_protocols()
    Client.start_client("127.0.0.1", 36969)
    print(Client.load_projects())
    print(Client.load_nodes())
    print(Client.load_veins())

