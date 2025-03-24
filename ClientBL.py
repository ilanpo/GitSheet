import os.path
import threading
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

    def init_protocols(self):
        self.comtocol = ComProtocol()

    def start_client(self, ip: str, port: int) -> bool:
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
            thread = threading.Thread(target=self.receive_handle)
            thread.start()
            return True

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on start client {e}")
            self.last_error = f"Exception in [ClientBL] start client: {e}"
            return False

    def receive_handle(self):
        while self.flags["running"]:
            success, x = self.comtocol.receive_sym()
            x = x.decode()
            if x.split(HEADER_SEPARATOR)[0] == HEADERS["fetch"]:
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
            while self.last_fetch_received is None:
                pass
            fetch = self.last_fetch_received
            self.last_fetch_received = None
            return fetch

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request projects {e}")
            self.last_error = f"Exception in [ClientBL] request projects: {e}"
            return None

    def request_data(self, data_type: str, project_id):  # valid types are: veins nodes
        try:
            self.comtocol.send_sym(f"FTCH<{data_type}>{project_id}".encode())
            while self.last_fetch_received is None:
                pass
            fetch = self.last_fetch_received
            self.last_fetch_received = None
            return fetch

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request projects {e}")
            self.last_error = f"Exception in [ClientBL] request projects: {e}"
            return None

    def request_files(self, node_id):
        try:
            self.comtocol.send_sym(f"FLFT<{node_id}")
        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request projects {e}")
            self.last_error = f"Exception in [ClientBL] request projects: {e}"
            return None

    def file_send(self, file_name):
        with open("example.pdf", "rb") as file:
            self.comtocol.send_raw_sym(file.read())


if __name__ == "__main__":
    Client = ClientBl()
    Client.init_protocols()
    Client.start_client("127.0.0.1", 36969)
    print(Client.request_projects()["_id"])
    Client.console_handle()  # command should look like this: FTCH<nodes>67a8ee274a8273e4c778beb2
                                                    # (  type of command < parameter 1 > parameter 2 )

    """comtocol = ComProtocol()
    comtocol.connect("127.0.0.1", 6969, CLIENT_CONNECTION_TYPE)
    comtocol.send("Hello!!!!")
    comtocol.send_raw("LUPOV".encode())
    comtocol.send(DISCONNECT_MESSAGE)"""
