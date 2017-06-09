import socket,select

UDP_port = 8587 #Port for fast pase data transfer, e.g. moving objects
TCP_port = 8588 #Port for serious data transfer, e.g. chat messages

class Server: #Class for a server
    def __init__(self,ip=socket.gethostbyname(socket.gethostname()),Uport = UDP_port, Tport = TCP_port):
        self.ip = ip
        self.uport = Uport
        self.tport = Tport
        self.usock = socket.socket()