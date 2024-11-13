from Protocol.CommProtocol import *

if __name__ == "__main__":
    comtocol = ComProtocol("127.0.0.1", 4565, CLIENT_CONNECTION_TYPE)
    comtocol.connect()
    comtocol.send("Hello!!!!")
    comtocol.send_raw("LUPOV".encode())