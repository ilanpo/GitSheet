from Protocol.CommProtocol import *
from Protocol.DB_Manager import *
import threading


class ClientHandle:
    comtocol: ComProtocol
    DB: DatabaseManager
    Thread: threading.Thread
    ip: str
    port: int

    def __init__(self, ip, port, socket_obj):
        self.headers = {
            "file": "FILE",
            "fetch": "FTCH"
        }
        self.comtocol = ComProtocol()
        self.comtocol.attach(ip, port, socket_obj)
        self.DB = DatabaseManager("mongodb://localhost:27017/")
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
                    self.Handle_Message(data)
        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on handle client {e}")
            self.last_error = f"Exception in [ClientHandle] handle client: {e}"
            return False

    def Handle_Message(self, message):
        if message.split(HEADER_SEPARATOR)[0] == self.headers["file"]:
            self.file_reception(message)

    def file_reception(self, message):
        file_name = message.split(HEADER_SEPARATOR)[1]
        try:
            with open("file_name.png", "wb") as file:
                raw = self.comtocol.receive()
                file.write(raw)
            return True
        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on handle message {e}")
            self.last_error = f"Exception in [ClientHandle] handle message: {e}"
            return False

    def find_projects(self, user_id):
        x = self.DB.fetch_projects(user_id)
        return x

    def find_veins_and_nodes(self, user_id, project_id):
        x = self.DB.fetch_veins_and_nodes(user_id, project_id)
        return x

    def find_files(self, user_id, node_id):
        x = self.DB.fetch_files(user_id, node_id)
        return x

    def delete_entry(self, entry_id, collection):
        x = self.DB.remove_entry(entry_id, collection)
        # allowed collections are as follows: "users" "projects" "nodes" "veins" "files"
        return x

    def update_entry(self, entry_id, collection, operation: str, change, change_field):
        # allowed operations are: "add" "replace" "discard"
        # allowed collections are as follows: "users" "projects" "nodes" "veins" "files"
        x = self.DB.push_to_dict(entry_id, collection, operation, change, change_field)
        return x


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
    SerBL.start_server("0.0.0.0", 36969)
    SerBL.connection_manager()

    """comtocol = ComProtocol()
    comtocol.connect("0.0.0.0", 4565, SERVER_CONNECTION_TYPE)
    c_socket, c_addr = comtocol.accept_handler()
    client = ComProtocol()
    client.attach(c_addr[0], c_addr[1], c_socket)
    print(client.receive())
    print(client.receive())"""
