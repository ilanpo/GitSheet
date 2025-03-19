import base64
import logging
import socket
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import cryptography.hazmat.primitives.serialization as serialization
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

    def set_symmetric_key(self, sym_key, init_vector):
        self.symmetric_key = sym_key
        self.init_vector = init_vector

    def get_symmetric_key(self):
        return self.symmetric_key, self.init_vector

    def set_public_key(self, public_key):
        self.public_key = serialization.load_pem_public_key(public_key)

    def get_public_key(self):
        return self.public_key.public_bytes(encoding=serialization.Encoding.PEM,
                                            format=serialization.PublicFormat.SubjectPublicKeyInfo)


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

    def send_public_key(self):
        try:
            self.cryptocol.generate_asymmetric_key()
            value = self.cryptocol.get_public_key()
            value_len = str(len(value)).zfill(HEADER_SIZE)
            msg = f"{value_len}0{value.decode()}"
            self.socket.send(msg.encode())
            return True
        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on send public key: {e}")
            self.last_error = f"Exception in ComProtocol send public key: {e}"
            return False

    def send_asym(self, value: bytes):
        try:
            success, value = self.cryptocol.encrypt_asymmetric(value)
            value_len = str(len(value)).zfill(HEADER_SIZE)
            msg_len = str(len(value_len)).zfill(HEADER_SIZE)
            msg = f"{msg_len}0{value_len}"
            self.socket.send(msg.encode())
            self.socket.send(value)
            return True
        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on send asymmetric: {e}")
            self.last_error = f"Exception in ComProtocol send asymmetric: {e}"
            return False

    def send_sym(self, value: bytes):
        try:
            success, value = self.cryptocol.encrypt_symmetric(value)
            value_len = str(len(value)).zfill(HEADER_SIZE)
            msg_len = str(len(value_len)).zfill(HEADER_SIZE)
            msg = f"{msg_len}0{value_len}"
            self.socket.send(msg.encode())
            self.socket.send(value)
            return True
        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on send symmetric: {e}")
            self.last_error = f"Exception in ComProtocol send symmetric: {e}"
            return False

    def send_raw_sym(self, value: bytes):
        try:
            success, value = self.cryptocol.encrypt_symmetric(value)
            value_len = str(len(value)).zfill(HEADER_SIZE)
            msg_len = str(len(value_len)).zfill(HEADER_SIZE)
            msg = f"{msg_len}0{value_len}"
            self.socket.send(msg.encode())
            len_sent = 0
            while len_sent < len(value):
                remaining = value[len_sent:]
                length_to_send = min(len(remaining), CHUNK_SIZE)
                self.socket.send(remaining[:length_to_send])
                len_sent += length_to_send

            return True
        except Exception as e:
            write_to_log(f"[ComProtocol] Exception on send raw symmetric: {e}")
            self.last_error = f"Exception in ComProtocol send raw symmetric: {e}"
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
        self.cryptocol.generate_symmetric_key()
        return self.cryptocol.get_symmetric_key()

    def set_symmetric_key(self, sym_key, init_vector):
        self.cryptocol.set_symmetric_key(sym_key, init_vector)

    def format_value(self, value: str, is_raw: bool):
        success, value = self.cryptocol.encrypt_symmetric(value.encode())
        if success:
            #value = value.decode()
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
        _, value = self.cryptocol.decrypt_symmetric(data)
        return _, value

    def decrypt_data_asym(self, data):
        return self.cryptocol.decrypt_asymmetric(data)

    def receive_public_key(self):
        try:
            length = int(self.socket.recv(HEADER_SIZE).decode())
            is_raw = self.socket.recv(1).decode()
            if is_raw == "1":
                length_raw = self.socket.recv(length).decode()
                return self.raw_receive(int(length_raw))

            data = self.socket.recv(length)
            self.cryptocol.set_public_key(data)
            return data

        except Exception as e:
            """write_to_log(f"[ComProtocol] Exception on receive public key: {e}")
            self.last_error = f"Exception in ComProtocol receive public key: {e}")"""
            return None

    def receive_asym(self):
        try:
            length = int(self.socket.recv(HEADER_SIZE).decode())
            is_raw = self.socket.recv(1).decode()

            bytes_len = self.socket.recv(length).decode()
            data = self.socket.recv(int(bytes_len))
            success, data = self.cryptocol.decrypt_asymmetric(data)
            return success, data

        except Exception as e:
            """write_to_log(f"[ComProtocol] Exception on receive asymmetric: {e}")
            self.last_error = f"Exception in ComProtocol receive asymmetric: {e}")"""
            return False, None

    def receive_sym(self):
        try:
            length = int(self.socket.recv(HEADER_SIZE).decode())
            is_raw = self.socket.recv(1).decode()

            bytes_len = self.socket.recv(length).decode()
            data = self.socket.recv(int(bytes_len))
            success, data = self.cryptocol.decrypt_symmetric(data)
            return success, data

        except Exception as e:
            """write_to_log(f"[ComProtocol] Exception on receive asymmetric: {e}")
            self.last_error = f"Exception in ComProtocol receive asymmetric: {e}")"""
            return False, None

    def receive_raw_sym(self):
        try:
            length = int(self.socket.recv(HEADER_SIZE).decode())
            is_raw = self.socket.recv(1).decode()
            file_length = int(self.socket.recv(length).decode())
            raw_data: bytes = b""
            while len(raw_data) < file_length:
                chunk_size = min(CHUNK_SIZE, file_length-len(raw_data))
                chunk = self.socket.recv(chunk_size)
                raw_data += chunk

            success, raw_data = self.decrypt_data(raw_data)
            return True, raw_data

        except Exception as e:
            """write_to_log(f"[ComProtocol] Exception on receive asymmetric: {e}")
            self.last_error = f"Exception in ComProtocol receive asymmetric: {e}")"""
            return False, None

    def receive(self):
        try:
            length = int(self.socket.recv(HEADER_SIZE).decode())
            is_raw = self.socket.recv(1).decode()
            if is_raw == "1":
                length_raw = self.socket.recv(length).decode()
                return self.raw_receive(int(length_raw))

            data = self.socket.recv(length)
            print(data)
            return data

        except Exception as e:
            """write_to_log(f"[ComProtocol] Exception on receive: {e}")
            self.last_error = f"Exception in ComProtocol receive: {e}")"""
            return None

    def is_valid(self) -> bool:
        return self.socket is not None

    def whos_there(self):
        return self.ip, self.port

    def give_me_keys(self):
        return self.cryptocol.get_symmetric_key()


if __name__ == "__main__":
    pass
