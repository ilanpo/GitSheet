from Protocol.CommProtocol import *

if __name__ == "__main__":
    comtocol = ComProtocol()
    comtocol.connect("127.0.0.1", 6969, CLIENT_CONNECTION_TYPE)
    comtocol.send("Hello!!!!")
    comtocol.send_raw("LUPOV".encode())
    comtocol.send(DISCONNECT_MESSAGE)