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
            x = self.comtocol.receive()
            if x.split(HEADER_SEPARATOR)[0] == HEADERS["fetch"]:
                x = json.loads(x)
            if x.split(HEADER_SEPARATOR)[0] == HEADERS["keygen"]:
                self.comtocol.set_symmetric_key(x.split(HEADER_SEPARATOR)[1])
                self.flags["encrypted"] = True
            print(x)

    def console_handle(self):
        msg = ""
        while msg != DISCONNECT_MESSAGE:
            msg = input()

            if msg.split(HEADER_SEPARATOR)[0] == HEADERS["file"]:
                file_name = msg.split(HEADER_SEPARATOR)[1]
                self.comtocol.send(msg)
                self.file_send(msg.split(HEADER_SEPARATOR)[1])
            else:
                self.comtocol.send(msg)
        self.flags["running"] = False

    def file_send(self, file_name):
        with open(file_name, "rb") as file:
            self.comtocol.send_raw(file.read())


if __name__ == "__main__":
    Client = ClientBl()
    Client.init_protocols()
    Client.start_client("127.0.0.1", 36969)
    Client.console_handle()  # command should look like this: FTCH<nodes>67a8ee274a8273e4c778beb2
                                                    # (  type of command < parameter 1 > parameter 2 )

    """comtocol = ComProtocol()
    comtocol.connect("127.0.0.1", 6969, CLIENT_CONNECTION_TYPE)
    comtocol.send("Hello!!!!")
    comtocol.send_raw("LUPOV".encode())
    comtocol.send(DISCONNECT_MESSAGE)"""
