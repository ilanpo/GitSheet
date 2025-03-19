from ClientBL import ClientBl as CBL


class ClientGUI:
    clientbl: CBL

    def __init__(self):
        self.last_error = "no error registered"
        self.userid = None

    def init_protocols(self):
        self.clientbl = CBL()
        self.clientbl.init_protocols()

    def load_projects(self):
        return self.clientbl.request_projects()


if __name__ == "__main__":
    Client = ClientGUI()
    Client.init_protocols()

