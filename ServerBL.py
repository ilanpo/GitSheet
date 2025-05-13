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
        self.user_id = None
        self.comtocol = ComProtocol()
        self.comtocol.attach(ip, port, socket_obj)
        self.DB = DatabaseManager("mongodb://localhost:27017/")
        self.connected = True
        self.last_error = "no error registered"

    def handle_client(self):
        """
        Sends public key, receives symmetric key from client and receives all messages from client
        :return: none
        """
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
                        # self.comtocol.send_sym("Disconnecting".encode())
                    self.handle_message(data)

        except Exception as e:
            write_to_log(f"[ClientHandle] Exception on handle client {e}")
            self.last_error = f"Exception in [ClientHandle] handle client: {e}"
            return False

    def handle_message(self, message):
        """

        :param message:
        :return:
        """
        try:
            if message.split(HEADER_SEPARATOR)[0] == HEADERS["login"]:
                username = message.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[0]
                print(username)
                password = message.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[1]
                print(password)
                success = self.login(username, password)
                if success:
                    self.comtocol.send_sym("login successful".encode())
                else:
                    self.comtocol.send_sym(FAILURE_MESSAGE.encode())
            if message.split(HEADER_SEPARATOR)[0] == HEADERS["create"]:
                data_type = message.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[0]
                print(message)
                try:
                    if data_type == "user":
                        username = message.split(PARAMETER_SEPARATOR)[1]
                        password = message.split(PARAMETER_SEPARATOR)[2]
                        self.add_entry(data_type, [username, password])
                    elif data_type == "node":
                        project_id = ObjectId(message.split(PARAMETER_SEPARATOR)[1])
                        permissions = json.loads(message.split(PARAMETER_SEPARATOR)[2])
                        item_data = json.loads(message.split(PARAMETER_SEPARATOR)[3])
                        settings = json.loads(message.split(PARAMETER_SEPARATOR)[4])
                        self.add_entry(data_type, [project_id, permissions, item_data, settings])
                    elif data_type == "vein":
                        project_id = ObjectId(message.split(PARAMETER_SEPARATOR)[1])
                        permissions = json.loads(message.split(PARAMETER_SEPARATOR)[2])
                        item_data = message.split(PARAMETER_SEPARATOR)[3]
                        settings = json.loads(message.split(PARAMETER_SEPARATOR)[4])
                        self.add_entry(data_type, [project_id, permissions, item_data, settings])
                    self.comtocol.send_sym(f"Successfully added {data_type}".encode())
                except Exception as e:
                    self.comtocol.send_sym(str(e).encode())
            if message.split(HEADER_SEPARATOR)[0] == HEADERS["file_fetch"]:
                node_id = message.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[0]
                file_id = message.split(HEADER_SEPARATOR)[1].split(PARAMETER_SEPARATOR)[1]
                files = self.find_files(self.user_id, ObjectId(node_id))
                file = None
                for x in files:
                    if x["_id"] == ObjectId(file_id):
                        file = x
                if file:
                    self.comtocol.send_raw_sym(file["file"])
            if message.split(HEADER_SEPARATOR)[0] == HEADERS["file"]:
                self.file_reception(message)
            if message.split(HEADER_SEPARATOR)[0] == HEADERS["update"]:
                x = FAILURE_MESSAGE
                message_start = message.split(PARAMETER_SEPARATOR)[0]
                item_id = message_start.split(HEADER_SEPARATOR)[1]
                collection = message.split(PARAMETER_SEPARATOR)[1]
                change_type = message.split(PARAMETER_SEPARATOR)[2]
                change = message.split(PARAMETER_SEPARATOR)[3]
                print(change)
                if change_type == "settings":
                    change = json.loads(change)
                print(change)
                print(type(change))
                success = self.update_entry(ObjectId(item_id), collection, "replace", change, change_type)
                if success:
                    x = f"Successfully updated entry {item_id} in collection {collection} with {change} in field {change_type}"
                self.comtocol.send_sym(x)

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
        message = message.split(HEADER_SEPARATOR)[1]
        file_name = message.split(PARAMETER_SEPARATOR)[0]
        node_id = message.split(PARAMETER_SEPARATOR)[1]
        try:
            with open(f"{file_name}", "wb") as file:
                success, raw = self.comtocol.receive_raw_sym()
                if raw:
                    self.DB.new_file(ObjectId(node_id), [self.user_id], raw, {"Name": file_name})
                    file.write(raw)
                else:
                    write_to_log("[ClientHandle] file reception received no file")
                    return False
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
    
    def login(self, username, password):
        success, found_password, user_id = self.DB.fetch_user(username)
        if success:
            if password == found_password:
                self.user_id = username
                print(f"user_id is now {username}")
                return True
        return False


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

    def add_entry(self, entry_type: str, info: list):
        x = FAILURE_MESSAGE
        if entry_type == "user":
            x = self.DB.new_user(info[0], info[1])
        if entry_type == "vein":
            x = self.DB.new_vein(info[0], info[1], info[2], info[3])
        if entry_type == "node":
            x = self.DB.new_node(info[0], info[1], info[2], info[3])
        if entry_type == "project":
            x = self.DB.new_project(info[0], info[1], info[2], info[3])
        if entry_type == "file":
            x = self.DB.new_file(info[0], info[1], info[2], info[3])
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
        """
        inits comprotocol for later use
        :return:  none
        """
        self.comtocol = ComProtocol()

    def start_server(self, ip: str, port: int) -> bool:
        """
        starts the server with listen ip and port specified
        :param ip: listen ip of server
        :param port: port of server
        :return: True or false whether the server managed to start
        """
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
            while self.flags["running"] == True:
                cl_socket, cl_addr = self.comtocol.accept_handler(5)
                if cl_socket:
                    new_client = ClientHandle(cl_addr[0], cl_addr[1], cl_socket)
                    thread = threading.Thread(target=new_client.handle_client)
                    write_to_log(f"[ServerBL] Active connections: {threading.active_count() - 2}")
                    thread.start()
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
