import logging
import socket
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import secrets

HEADER_SIZE = 4
CHUNK_SIZE = 1024

LOG_FILE_PATH = 'Log_Global.txt'
CLIENT_CONNECTION_TYPE = 'ClientConnectionType'
SERVER_CONNECTION_TYPE = 'ServerConnectionType'
DISCONNECT_MESSAGE = 'D1SC0NNECT'
HEADER_SEPARATOR = '<'
PARAMETER_SEPARATOR = '>'
HEADERS = {
    "file": "FILE",
    "fetch": "FTCH",
    "keygen": "KYGN"
}
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def write_to_log(msg):
    logging.info(msg)
    print(msg)


class EncryptProtocol:
    def __init__(self):
        self.last_error = None
        self.public_key = None
        self.private_key = None
        self.symmetric_key = None
        self.init_vector = None

    def encrypt_asymmetric(self, content: bytes) -> tuple:
        try:
            result = self.public_key.encrypt(
                content,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return True, result

        except Exception as e:
            write_to_log(f"[EncryptProtocol] Exception on Asymmetric encrypt {e}")
            self.last_error = f"Exception in EncryptProtocol Asymmetric encrypt: {e}"
            return False, ""

    def decrypt_asymmetric(self, cryptid: bytes) -> tuple:
        try:
            content = self.private_key.decrypt(
                cryptid,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return True, content

        except Exception as e:
            write_to_log(f"[EncryptProtocol] Exception on Asymmetric decrypt {e}")
            self.last_error = f"Exception in EncryptProtocol Asymmetric decrypt: {e}"
            return False, ""

    def encrypt_symmetric(self, content: bytes) -> tuple:
        try:
            algorithm = algorithms.AES(self.symmetric_key)
            mode = modes.CTR(self.init_vector)
            cipher = Cipher(algorithm, mode)
            encryptor = cipher.encryptor()

            message_encrypted = encryptor.update(content) + encryptor.finalize()

            return True, message_encrypted

        except Exception as e:
            write_to_log(f"[EncryptProtocol] Exception on Symmetric encrypt {e}")
            self.last_error = f"Exception in EncryptProtocol Symmetric encrypt: {e}"
            return False, ""

    def decrypt_symmetric(self, cryptid: bytes) -> tuple:
        try:
            algorithm = algorithms.AES(self.symmetric_key)
            mode = modes.CTR(self.init_vector)

            cipher = Cipher(algorithm, mode)

            decryptor = cipher.decryptor()
            message_decrypted = decryptor.update(cryptid) + decryptor.finalize()

            return True, message_decrypted

        except Exception as e:
            write_to_log(f"[EncryptProtocol] Exception on Symmetric decrypt {e}")
            self.last_error = f"Exception in EncryptProtocol Symmetric decrypt: {e}"
            return False, ""

    def generate_asymmetric_key(self) -> bool:
        key_size = 2048
        try:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
            )

            self.public_key = self.private_key.public_key()
            return True

        except Exception as e:
            write_to_log(f"[EncryptProtocol] Exception on Asymmetric keygen {e}")
            self.last_error = f"Exception in EncryptProtocol Asymmetric keygen: {e}"
            return False

    def gen_padding(self):
        return padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )

    def generate_symmetric_key(self) -> bool:
        try:
            self.symmetric_key = secrets.token_bytes(32)
            self.init_vector = secrets.token_bytes(16)
            return True

        except Exception as e:
            write_to_log(f"[EncryptProtocol] Exception on Symmetric keygen {e}")
            self.last_error = f"Exception in EncryptProtocol Symmetric keygen: {e}"
            return False

    def set_symmetric_key(self, sym_key):
        self.symmetric_key = sym_key


class ComProtocol:
    ip: str
    port: int
    connection_type: str
    socket: socket

    def __init__(self):
        self.last_error = None
        self.cryptocol = EncryptProtocol()

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

    def gen_symmetric_key(self):
        return self.cryptocol.generate_symmetric_key()

    def set_symmetric_key(self, sym_key):
        self.cryptocol.set_symmetric_key(sym_key)

    def format_value(self, value: str, is_raw: bool):
        success, value = self.cryptocol.encrypt_symmetric(value.encode())
        if success:
            value = str(value)
            value_len = str(len(value)).zfill(HEADER_SIZE)
            return f"{ value_len }{ is_raw and 1 or 0 }{ value }"
        else:
            return None

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

    def decrypt_data(self, data):
        return self.cryptocol.decrypt_symmetric(data)

    def receive(self):
        try:
            length = int(self.socket.recv(HEADER_SIZE).decode())
            is_raw = self.socket.recv(1).decode()
            if is_raw == "1":
                length_raw = self.socket.recv(length).decode()
                return self.raw_receive(int(length_raw))

            data = self.socket.recv(length)
            data = self.decrypt_data(data)
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
    comtocol = ComProtocol()
    comtocol2 = ComProtocol()

    comtocol.gen_symmetric_key()
    comtocol2.gen_symmetric_key()

    comtocol.connect("0.0.0.0", 36969, SERVER_CONNECTION_TYPE)
    comtocol2.connect("127.0.0.1", 36969, CLIENT_CONNECTION_TYPE)

    comtocol2.send("123")
    print(comtocol.receive())
