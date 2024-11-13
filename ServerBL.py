from Protocol.CommProtocol import *

if __name__ == "__main__":
    comtocol = ComProtocol("0.0.0.0", 4565, SERVER_CONNECTION_TYPE)
    comtocol.connect()
    c_socket, c_addr = comtocol.accept_handler()
    client = ComProtocol(c_addr[0], c_addr[1], CLIENT_CONNECTION_TYPE, c_socket)
    print(client.receive())
    print(client.receive())
