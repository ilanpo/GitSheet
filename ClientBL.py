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
        This function starts the communications protocol
        """
        self.comtocol = ComProtocol()

    def start_client(self, ip: str, port: int) -> bool:
        """
        Receives public key then generates and sends symmetric key
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

    def console_handle(self):
        """
        function for testing client bl using console
        :return:
        """
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
        """
        function to request projects from server
        :return:the found data
        """
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

    def request_data(self, data_type: str, parent_id):
        """
        requests dara such as veins nodes or files belonging to a project / node from the server
        :param data_type: valid types are: veins nodes files (when requesting files note that you're requesting the file INFO not the file itself)
        :param project_id: id of project also for files you need to input node_id not project id
        :return:bool whether operation was successful and the found data
        """
        try:
            self.comtocol.send_sym(f"FTCH<{data_type}>{parent_id}".encode())
            success, x = self.comtocol.receive_sym()
            x = x.decode()
            x = x.split(HEADER_SEPARATOR)[1]
            if x == FAILURE_MESSAGE:
                raise Exception(f"Server failed to find requested data {data_type} {parent_id}")
            else:
                x = json.loads(x)
                fetch = x
            return True, fetch

        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request data {e}")
            self.last_error = f"Exception in [ClientBL] request data: {e}"
            return False, None

    def request_file(self, node_id, file_id, file_name):
        """
        requests a specific file
        :param node_id: id of the node the file belongs to
        :param file_id: id of the file
        :param file_name: the name of the file
        :return: bool whether the request was successful
        """
        try:
            file_dir = os.path.dirname(os.path.realpath('__file__'))
            if not os.path.exists(f"{file_dir}\\Files"):
                os.mkdir(f"{file_dir}\\Files")
            file_name = os.path.join(file_dir, f'Files\\{file_name}')
            self.comtocol.send_sym(f"FLFT<{node_id}>{file_id}".encode())
            success, file = self.comtocol.receive_raw_sym()
            with open(f'{file_name}', "wb") as new_file:
                new_file.write(file)
            return success
        except Exception as e:
            write_to_log(f"[ClientBL] Exception on request file {e}")
            self.last_error = f"Exception in [ClientBL] request file: {e}"
            return False

    def login(self, username, password):
        """
        sends login request to server
        :param username: username of account
        :param password: password of account
        :return: returns the servers response to the login request and the user_id which could be FAILURE_MESSAGE if it failed the login
        """
        self.comtocol.send_sym(f"LGIN<{username}>{password}".encode())
        success, x = self.comtocol.receive_sym()
        x = x.decode()
        success, user_id = self.comtocol.receive_sym()
        user_id = user_id.decode()
        return x, user_id

    def register(self, username, password):
        """
        sends register request to server
        :param username: username of account
        :param password: password of account
        :return:
        """
        self.comtocol.send_sym(f"CRET<user>{username}>{password}".encode())
        success, x = self.comtocol.receive_sym()
        x = x.decode()
        return x

    def upload_file(self, file_name, node_id):
        """
        uploads a file to a node in the server
        :param file_name: name of the file
        :param node_id: id of the destination node
        :return:
        """
        self.comtocol.send_sym(f"FILE<{file_name}>{node_id}".encode())
        self.file_send(file_name)

    def file_send(self, file_name):
        """
        sends a file to the server
        :param file_name: name of the file
        :return:
        """
        with open(f'Files/{file_name}', "rb") as file:
            self.comtocol.send_raw_sym(file.read())

    def update_position(self, collection: str, item_id: str, settings: dict) -> str:
        """
        sends a request to the server to update the position of a node according to the clients positions
        :param collection: id of updated collection (nodes)
        :param item_id: id of updated item
        :param settings: a new settings dict that has the updated positions
        :return: the servers response or a failure message defined in the protocol
        """
        settings = json.dumps(settings)
        self.comtocol.send_sym(f"UPDT<{item_id}>{collection}>settings>{settings}".encode())
        success, x = self.comtocol.receive_sym()
        x = x.decode()
        if not success:
            return FAILURE_MESSAGE
        else:
            return x

    def update_vein_text(self, collection: str, item_id: str, vein_data: str):
        """
        sends a request to the server to update the data of a vein according to the clients positions
        :param collection: id of updated collection (veins)
        :param item_id: id of updated item
        :param vein_data: the new vein data
        :return: failure message or received response from server
        """
        self.comtocol.send_sym(f"UPDT<{item_id}>{collection}>vein_data>{vein_data}".encode())
        success, x = self.comtocol.receive_sym()
        x = x.decode()
        if not success:
            return FAILURE_MESSAGE
        else:
            return x

    def delete_node(self, item_id, project_id):
        """
        sends a request to delete a node to the server
        :param item_id: id of the node
        :param project_id: id of the project the node belongs to
        :return: failure message or received response from server
        """
        self.comtocol.send_sym(f"DELT<nodes>{item_id}>{project_id}".encode())
        success, x = self.comtocol.receive_sym()
        if not success:
            return FAILURE_MESSAGE
        else:
            return x

    def delete_vein(self, item_id, project_id):
        """
        sends a request to delete a vein to the server
        :param item_id: id of the vein
        :param project_id: id of the project the vein belongs to
        :return: failure message or received response from server
        """
        self.comtocol.send_sym(f"DELT<veins>{item_id}>{project_id}".encode())
        success, x = self.comtocol.receive_sym()
        if not success:
            return FAILURE_MESSAGE
        else:
            return x

    def create_node(self, project_id: str, permissions: list, item_data: list, settings: dict):
        """
        sends a request to create a node to the server
        :param project_id: id of the project the new node belongs to
        :param permissions: permissions list of the people allowed to access the node
        :param item_data: the node_data of the node
        :param settings: the settings dict of the node
        :return: failure message or received response from server
        """
        permissions = json.dumps(permissions)
        item_data = json.dumps(item_data)
        settings = json.dumps(settings)
        self.comtocol.send_sym(f"CRET<node>{project_id}>{permissions}>{item_data}>{settings}".encode())
        success, x = self.comtocol.receive_sym()
        x = x.decode()
        if not success:
            return FAILURE_MESSAGE
        else:
            return x

    def create_vein(self, project_id: str, permissions: list, item_data: str, settings: dict):
        """
        sends a request to create a vein to the server
        :param project_id: id of the project the new vein belongs to
        :param permissions: permissions list of the people allowed to access the vein
        :param item_data: the vein_data of the vein
        :param settings: the settings dict of the vein
        :return: failure message or received response from server
        """
        permissions = json.dumps(permissions)
        settings = json.dumps(settings)
        self.comtocol.send_sym(f"CRET<vein>{project_id}>{permissions}>{item_data}>{settings}".encode())
        success, x = self.comtocol.receive_sym()
        x = x.decode()
        if not success:
            return FAILURE_MESSAGE
        else:
            return x

    def disconnect(self):
        """
        sends a disconnect msg as defined in the protocol to the server
        :return:
        """
        msg = DISCONNECT_MESSAGE
        self.comtocol.send_sym(msg.encode())
        self.flags["running"] = False

    def get_error(self):
        return self.last_error


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
