import os.path
# import threading
import json

from Protocol.CommProtocol import *


class ClientBl:
    comtocol: ComProtocol
    ip: str
    port: int

    def __init__(self):
        self.flags = {
            "running": False,   # flag for if the client is running
            "encrypted": False  # flag for if the communication is encrypted
        }
        self.last_error = "no error registered"
        self.last_fetch_received = None
        self.last_file_received = None
        self.last_login_request = None

    def init_protocols(self):
        """
        This function starts the comprotocol
        :return: none
        """
        self.comtocol = ComProtocol()

    def start_client(self, ip: str, port: int) -> bool:
        """
        Recieves public key then generates and sends symmetric key
        :param ip: ip of server
        :param port: port of server
        :return: True or False if the function succeeded
        """
        write_to_log("[ClientBL] Client starting")

        try:
            if not self.comtocol.connect(ip, port, CLIENT_CONNECTION_TYPE):
                self.last_error = self.comtocol.return_error()
                write_to_log(f"[ClientBL] Exception on start client in comtocol connect {self.last_error}")
                return False
            self.flags["running"] = True
            self.comtocol.receive_public_key()
            sym_key, init_vec = self.comtocol.gen_symmetric_key()
            self.comtocol.send_asym(sym_key)
            self.comtocol.send_asym(init_vec)
            # success, x = self.comtocol.receive_sym()
            # self.comtocol.set_symmetric_key(x.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[0],
            #                                 x.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[1])
            self.flags["encrypted"] = True
            # thread = threading.Thread(target=self.receive_handle)
            # thread.start()
            return True

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on start client {e}")
            self.last_error = f"Exception in [ClientBL] start client: {e}"
            return False

    def receive_handle(self):
        """

        :return:
        """
        while self.flags["running"]:
            success, x = self.comtocol.receive_sym()
            x = x.decode()
            if x == "Disconnecting":
                return
            elif x.split(HEADER_SEPARATOR)[0] == HEADERS["fetch"]:
                x = x.split(HEADER_SEPARATOR)[1]
                if x == FAILURE_MESSAGE:
                    write_to_log("[ClientBl] receive handle received failure message from server")
                    self.last_fetch_received = "Server failed to find requested data"
                else:
                    x = json.loads(x)
                    self.last_fetch_received = x
            elif x.split(HEADER_SEPARATOR)[0] == HEADERS["keygen"]:
                self.comtocol.set_symmetric_key(x.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[0],
                                                x.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[1])
                self.flags["encrypted"] = True
            elif x.split(HEADER_SEPARATOR[0] == HEADERS["file_fetch"]):
                self.last_file_received = x.split(HEADER_SEPARATOR)[1]
            elif x.split(HEADER_SEPARATOR[0] == HEADERS["login"]):
                self.last_login_received = x.split(HEADER_SEPARATOR)[1]
        

    def console_handle(self):
        msg = ""
        while msg != DISCONNECT_MESSAGE:
            msg = input()

            if msg.split(HEADER_SEPARATOR)[0] == HEADERS["file"]:
                self.comtocol.send_raw_sym(msg.encode())
                self.file_send(msg.split(HEADER_SEPARATOR)[1])
            else:
                self.comtocol.send_sym(msg.encode())
        self.flags["running"] = False

    def request_projects(self):
        try:
            self.comtocol.send_sym(f"FTCH<projects".encode())
            success, x = self.comtocol.receive_sym()
            x = x.decode()
            x = x.split(HEADER_SEPARATOR)[1]
            if x == FAILURE_MESSAGE:
                write_to_log("[ClientBl] request projects received failure message from server")
                fetch = "Server failed to find requested projects"
            else:
                x = json.loads(x)
                fetch = x
            return fetch

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request projects {e}")
            self.last_error = f"Exception in [ClientBL] request projects: {e}"
            return None

    def request_data(self, data_type: str, project_id):  # valid types are: veins nodes files (when requesting files
                                                         # note that you're requesting the file INFO not the file itself)
        try:                                             # also for files you need to input node_id not project id
            self.comtocol.send_sym(f"FTCH<{data_type}>{project_id}".encode())
            success, x = self.comtocol.receive_sym()
            x = x.decode()
            x = x.split(HEADER_SEPARATOR)[1]
            if x == FAILURE_MESSAGE:
                write_to_log("[ClientBl] request data received failure message from server")
                fetch = "Server failed to find requested data"
            else:
                x = json.loads(x)
                fetch = x
            return fetch

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request projects {e}")
            self.last_error = f"Exception in [ClientBL] request projects: {e}"
            return None

    def request_file(self, node_id, file_id, file_name):
        try:
            file_dir = os.path.dirname(os.path.realpath('__file__'))
            file_name = os.path.join(file_dir, f'Files/{file_name}')
            self.comtocol.send_sym(f"FLFT<{node_id}>{file_id}".encode())
            success, file = self.comtocol.receive_raw_sym()
            with open(file_name, "wb") as new_file:
                new_file.write(file)
            return success
        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request projects {e}")
            self.last_error = f"Exception in [ClientBL] request projects: {e}"
            return False

    def login(self, username, password):
        self.comtocol.send_sym(f"LGIN<{username}>{password}")
        success, x = self.comtocol.receive_sym()
        return x

    def register(self, username, password):
        self.comtocol.send_sym(f"CRET<user>{username}>{password}".encode())

    def upload_file(self, file_name, node_id):
        self.comtocol.send_sym(f"FILE<{file_name}>{node_id}".encode())
        self.file_send(file_name)

    def file_send(self, file_name):
        with open(file_name, "rb") as file:
            self.comtocol.send_raw_sym(file.read())

    def update_position(self, collection: str, item_id: str, settings: dict) -> str:
        settings = json.dumps(settings)
        print(settings)
        self.comtocol.send_sym(f"UPDT<{item_id}>{collection}>settings>{settings}".encode())
        success, x = self.comtocol.receive_sym()
        if not success:
            return FAILURE_MESSAGE
        else:
            return x

    def disconnect(self):
        msg = DISCONNECT_MESSAGE
        self.comtocol.send_sym(msg.encode())
        self.flags["running"] = False


if __name__ == "__main__":
    Client = ClientBl()
    Client.init_protocols()
    Client.start_client("127.0.0.1", 36969)
    projects = Client.request_projects()
    print(projects)
    node_id = Client.request_data("nodes", projects[0]["_id"])[0]
    print(node_id)
    print(Client.request_data("files", node_id["_id"]))
    # Client.upload_file("Example.txt", "67e2b91e9a082c22cae2e99c")
    # print(Client.request_file("67e2b91e9a082c22cae2e99c", "67e2cfdf2ee6b3f796bfa17d", "Example.txt"))
    Client.console_handle()  # command should look like this: FTCH<nodes>67a8ee274a8273e4c778beb2
                                                    # (  type of command < parameter 1 > parameter 2 )

    """comtocol = ComProtocol()
    comtocol.connect("127.0.0.1", 6969, CLIENT_CONNECTION_TYPE)
    comtocol.send("Hello!!!!")
    comtocol.send_raw("LUPOV".encode())
    comtocol.send(DISCONNECT_MESSAGE)"""
