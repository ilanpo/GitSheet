from Protocol.CommProtocol import *
from Protocol.DB_Manager import *
import threading
import json


class ClientHandle:
    comtocol: ComProtocol
    DB: DatabaseManager
    Thread: threading.Thread
    ip: str
    port: int

    def __init__(self, ip, port, socket_obj):
        self.user_id = "123"  # PLACEHOLDER WHILE LOGIN DOESNT EXIST
        self.comtocol = ComProtocol()
        self.comtocol.attach(ip, port, socket_obj)
        self.DB = DatabaseManager("mongodb://localhost:27017/")
        self.connected = True
        self.last_error = "no error registered"

    def handle_client(self):
        try:
            self.comtocol.send_public_key()
            success, sym_key = self.comtocol.receive_asym()
            success, init_vec = self.comtocol.receive_asym()
            self.comtocol.set_symmetric_key(sym_key, init_vec)
            while self.connected:
                success, data = self.comtocol.receive_sym()
                if data:
                    write_to_log(f"[ClientHandle] received {data} from {self.comtocol.whos_there()}")
                    data = data.decode()
                    if data == DISCONNECT_MESSAGE:
                        write_to_log("Got disconnect message!")
                        self.connected = False
                    self.handle_message(data)

        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on handle client {e}")
            self.last_error = f"Exception in [ClientHandle] handle client: {e}"
            return False

    def handle_message(self, message):
        try:
            if message.split(HEADER_SEPARATOR)[0] == HEADERS["file"]:
                self.file_reception(message)
            if message.split(HEADER_SEPARATOR)[0] == HEADERS["fetch"]:
                path_collection = {
                    "projects": self.find_projects,
                    "nodes": self.find_nodes,
                    "veins": self.find_veins,
                    "files": self.find_files
                }
                x = FAILURE_MESSAGE
                i = 0
                message_start = message.split(PARAMETER_SEPARATOR)[0]
                fetch_type = message_start.split(HEADER_SEPARATOR)[1]
                chosen_path = path_collection[fetch_type]
                if fetch_type == "projects":
                    found_info = chosen_path(self.user_id)
                    if not found_info:
                        x = FAILURE_MESSAGE
                        x = HEADERS["fetch"] + "<" + x
                        self.comtocol.send_sym(x.encode())
                    else:
                        for x in found_info:
                            success, found_info[i] = self.serialize(x, fetch_type)
                            i += 1
                        found_info = json.dumps(found_info)
                        found_info = HEADERS["fetch"] + "<" + found_info
                        write_to_log(f"found info serialized is: {found_info}")
                        self.comtocol.send_sym(found_info.encode())

                else:
                    col_id = message.split(PARAMETER_SEPARATOR)[1]
                    col_id = ObjectId(col_id)
                    found_info = chosen_path(self.user_id, col_id)
                    if not found_info:
                        x = FAILURE_MESSAGE
                        x = HEADERS["fetch"] + "<" + x
                        self.comtocol.send_sym(x.encode())
                    else:
                        for x in found_info:
                            success, found_info[i] = self.serialize(x, fetch_type)
                            i += 1
                        found_info = json.dumps(found_info)
                        found_info = HEADERS["fetch"] + "<" + found_info
                        write_to_log(f"found info serialized is: {found_info}")
                        self.comtocol.send_sym(found_info.encode())

        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on handle message {e}")
            self.last_error = f"Exception in [ClientHandle] handle message: {e}"

    def serialize(self, document_info: dict, fetch_type: str):
        try:
            document_info['_id'] = str(document_info['_id'])

            if fetch_type == "projects":
                temp_list = []
                for x in document_info['nodes']:
                    temp_list.append(str(x))
                document_info['nodes'] = temp_list
                temp_list = []
                for x in document_info['veins']:
                    temp_list.append(str(x))
                document_info['veins'] = temp_list
            elif fetch_type == "nodes":
                temp_list = []
                for x in document_info['files']:
                    temp_list.append(str(x))
                document_info['files'] = temp_list
            elif fetch_type == "files":  # temp fix that has fetch for files not include the file itself
                document_info['file'] = "PLACEHOLDER"
            # document_info = json.dumps(document_info)    no longer necessary as I just dump the whole list
            # print(f"document_info is: {document_info}")  instead of dumping every dict
            return True, document_info
        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on serialize {e}")
            self.last_error = f"Exception in [ClientHandle] serialize: {e}"
            return False, None

    def file_reception(self, message):
        file_name = message.split(HEADER_SEPARATOR)[1]
        try:
            with open(f"{file_name}", "wb") as file:
                success, raw = self.comtocol.receive_raw_sym()
                file.write(raw)
            return True
        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on file reception {e}")
            self.last_error = f"Exception in [ClientHandle] file reception: {e}"
            return False

    def find_projects(self, user_id) -> list:
        x = self.DB.fetch_projects(user_id)
        print(f"found projects: {x}")
        return x

    def find_veins(self, user_id, project_id) -> list:
        x = self.DB.fetch_veins_and_nodes(user_id, project_id)
        print(x[0])
        return x[0]

    def find_nodes(self, user_id, project_id) -> list:
        print(user_id)
        print(project_id)
        x = self.DB.fetch_veins_and_nodes(user_id, project_id)
        print(f"nodes are: {x[1]}")
        return x[1]

    def find_files(self, user_id, node_id) -> list:
        x = self.DB.fetch_files(user_id, node_id)
        print(x)
        return x

    def delete_entry(self, entry_id, collection):
        x = self.DB.remove_entry(entry_id, collection)
        # allowed collections are as follows: "users" "projects" "nodes" "veins" "files"
        print(x)
        return x

    def update_entry(self, entry_id, collection, operation: str, change, change_field):
        # allowed operations are: "add" "replace" "discard"
        # allowed collections are as follows: "users" "projects" "nodes" "veins" "files"
        x = self.DB.push_to_dict(entry_id, collection, operation, change, change_field)
        print(x)
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
                    thread = threading.Thread(target=new_client.handle_client)
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
