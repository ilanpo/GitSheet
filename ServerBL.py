from Protocol.CommProtocol import *
import threading


class ClientHandle:
    comtocol: ComProtocol
    Thread: threading.Thread
    ip: str
    port: int

    def __init__(self, ip, port, socket_obj):
        self.comtocol = ComProtocol()
        self.comtocol.attach(ip, port, socket_obj)
        self.connected = True
        self.last_error = "no error registered"

    def Handle_Client(self):
        try:
            while self.connected:
                data = self.comtocol.receive()
                if data:
                    write_to_log(f"[ClientHandle] received {data} from {self.comtocol.whos_there()}")
                    if data == DISCONNECT_MESSAGE:
                        write_to_log("Got disconnect message!")
                        self.connected = False
        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on handle client {e}")
            self.last_error = f"Exception in [ClientHandle] handle client: {e}"
            return False


class ServerBL:
    comtocol: ComProtocol
    ip: str
    port: int

    def __init__(self):
        self.flags = {
            "running": False  # flag for if the server is running
        }
        self.last_error = "no error registered"

        with open(LOG_FILE_PATH, "wb"):
            pass

    def init_protocols(self):
        self.comtocol = ComProtocol()

    def start_server(self, ip: str, port: int) -> bool:
        write_to_log("[ServerBL] Server starting")

        try:
            if not self.comtocol.connect(ip, port, SERVER_CONNECTION_TYPE):
                self.last_error = self.comtocol.return_error()
                write_to_log(f"[ServerBL] Exception on start server {self.last_error}")
                return False
            return True

        except Exception as e:
            write_to_log(f"[ServerBL] Exception on start server {e}")
            self.last_error = f"Exception in [ServerBL] start server: {e}"
            return False

    def connection_manager(self):
        self.flags["running"] = True
        try:
            while self.flags["running"]:
                cl_socket, cl_addr = self.comtocol.accept_handler(5)
                if cl_socket:
                    new_client = ClientHandle(cl_addr[0], cl_addr[1], cl_socket)
                    thread = threading.Thread(target=new_client.Handle_Client)
                    write_to_log(f"[ServerBL] Active connections: {threading.active_count()}")
                    thread.start()
                if input() == 'STOP':
                    self.flags["running"] = False
        except Exception as e:
            write_to_log(f"[ServerBL] Exception on connection manager {e}")
            self.last_error = f"Exception in [ServerBL] connection manager: {e}"
            return False


if __name__ == "__main__":
    SerBL = ServerBL()
    SerBL.init_protocols()
    SerBL.start_server("0.0.0.0", 6969)
    SerBL.connection_manager()

    """comtocol = ComProtocol()
    comtocol.connect("0.0.0.0", 4565, SERVER_CONNECTION_TYPE)
    c_socket, c_addr = comtocol.accept_handler()
    client = ComProtocol()
    client.attach(c_addr[0], c_addr[1], c_socket)
    print(client.receive())
    print(client.receive())"""
