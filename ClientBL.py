from Protocol.CommProtocol import *


class ClientBl:
    comtocol: ComProtocol
    ip: str
    port: int

    def __init__(self):
        self.flags = {
            "running": False  # flag for if the client is running
        }
        self.last_error = "no error registered"

    def init_protocols(self):
        self.comtocol = ComProtocol()

    def start_client(self, ip: str, port: int) -> bool:
        write_to_log("[ClientBL] Server starting")

        try:
            if not self.comtocol.connect(ip, port, CLIENT_CONNECTION_TYPE):
                self.last_error = self.comtocol.return_error()
                write_to_log(f"[ClientBL] Exception on start client in comtocol connect {self.last_error}")
                return False
            return True

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on start client {e}")
            self.last_error = f"Exception in [ClientBL] start client: {e}"
            return False

    def console_handle(self):
        msg = ""
        while msg != DISCONNECT_MESSAGE:
            msg = input()
            self.comtocol.send(msg)


if __name__ == "__main__":
    Client = ClientBl()
    Client.init_protocols()
    Client.start_client("127.0.0.1", 6969)
    Client.console_handle()

    """comtocol = ComProtocol()
    comtocol.connect("127.0.0.1", 6969, CLIENT_CONNECTION_TYPE)
    comtocol.send("Hello!!!!")
    comtocol.send_raw("LUPOV".encode())
    comtocol.send(DISCONNECT_MESSAGE)"""
