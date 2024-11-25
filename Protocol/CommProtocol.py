import logging
import socket
from select import select

HEADER_SIZE = 4
CHUNK_SIZE = 1024

LOG_FILE_PATH = 'Log_Global.txt'
CLIENT_CONNECTION_TYPE = 'ClientConnectionType'
SERVER_CONNECTION_TYPE = 'ServerConnectionType'
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def write_to_log(msg):
    logging.info(msg)
    print(msg)


class ComProtocol:
    ip: str
    port: int
    connection_type: str
    socket: socket

    def __init__(self):
        self.last_error = None

    def attach(self, ip: str, port: int, c_socket: socket):
        self.ip = ip
        self.port = port
        self.connection_type = CLIENT_CONNECTION_TYPE
        self.socket = c_socket

    def connect(self, ip: str, port: int, connection_type: str) -> bool:
        self.ip = ip
        self.port = port
        self.connection_type = connection_type

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.connection_type == CLIENT_CONNECTION_TYPE:
                self.socket.connect((self.ip, self.port))
            if self.connection_type == SERVER_CONNECTION_TYPE:
                self.socket.bind((self.ip, self.port))
                self.socket.listen()
            write_to_log(f"[ComProtocol] {self.socket.getsockname()} connected")
            return True

        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on connect {e}")
            self.last_error = f"Exception in ComProtocol connect: {e}"
            return False

    def accept_handler(self, timer_len: int):
        try:
            self.socket.settimeout(timer_len)
            return self.socket.accept()

        except Exception as e:
            #write_to_log(f"[ComProtocol] Exception on accept handler {e}")
            #self.last_error = f"Exception in ComProtocol accept handler: {e}"
            return None, None

    def send(self, msg: str) -> bool:
        try:
            msg = self.format_value(msg, False)
            self.socket.send(msg.encode())
            return True
        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on send: {e}")
            self.last_error = f"Exception in ComProtocol send: {e}"
            return False

    def return_error(self):
        return self.last_error

    def send_raw(self, raw: bytes):
        try:
            raw_len = len(raw)
            msg = self.format_value(str(raw_len), True)
            self.socket.send(msg.encode())
            len_sent = 0
            while len_sent < raw_len:
                remaining = raw[len_sent:]
                length_to_send = min(len(remaining), CHUNK_SIZE)
                self.socket.send(remaining[:length_to_send])
                len_sent += length_to_send
            return True
        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on send_raw: {e}")
            self.last_error = f"Exception in ComProtocol send_raw: {e}"
            return False

    def format_value(self, value: str, is_raw: bool):
        value_len = str(len(value)).zfill(HEADER_SIZE)
        return f"{ value_len }{ is_raw and 1 or 0 }{ value }"

    def raw_receive(self, length):
        try:
            raw_data: bytes = b""

            while len(raw_data) < length:
                size = min(CHUNK_SIZE, length-len(raw_data))
                chunk_data = self.socket.recv(size)
                raw_data += chunk_data
            return raw_data
        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on receive_raw: {e}")
            self.last_error = f"Exception in ComProtocol receive_raw: {e}"
            return None

    def receive(self):
        try:
            length = int(self.socket.recv(HEADER_SIZE).decode())
            is_raw = self.socket.recv(1).decode()
            if is_raw == "1":
                length_raw = self.socket.recv(length).decode()
                return self.raw_receive(int(length_raw))

            data = self.socket.recv(length).decode()
            return data

        except Exception as e:

            """write_to_log(f"[ComProtocol] Exception on receive: {e}")
            self.last_error = f"Exception in ComProtocol receive: {e}")"""
            return None

    def is_valid(self) -> bool:
        return self.socket is not None

    def whos_there(self):
        return self.ip, self.port


if __name__ == "__main__":
    pass
