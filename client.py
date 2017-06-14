import socket,select,pickle

selfIp = socket.gethostbyname(socket.gethostname())
TCP_BUF_SIZE = 4046
UDP_BUF_SIZE = 512

class Client:
    def __init__(self,serverIp,tcpPort=3746,udpPort=3745):
        self.SYNC = {} #A list of variables that gets synced with the server
        self.TRIGGER = {} #A list containing pointers to functions if the server calls them
        self.serverIp = serverIp #IP of the server
        self.tsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #Setup TCP socket
        self.tsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
        self.tsock.settimeout(5)
        self.usock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.usock.bind((selfIp,udpPort))
        try: #Attempt to connect to the server
            self.tsock.connect((serverIp,tcpPort))
        except: #An error occured while connecting...
            self.failConnect = True
            raise
        else:
            self.failConnect = False
    def loop(self):
        self.udpLoop()
        self.tcpLoop()
    def serverShutdown(self): #The server has shutdown!
        print("Lost connection to server!")
    def udpLoop(self): #Loop for udp connection
        read,write,err = select.select([self.usock],[],[],0)
        for sock in read:
            if sock.getpeername()[0]==self.serverIp:
                dataRaw,con = sock.recvfrom(UDP_BUF_SIZE)
                try: #Try to read data coming through
                    data = pickle.loads(dataRaw)
                except: #Break out the loop of the data is corrupted
                    break
    def tcpLoop(self): #Loop for tcp connection
        read,write,err = select.select([self.tsock],[],[],0)
        for sock in read:
            if sock == self.tsock:
                try:
                    dataRaw = sock.recv(TCP_BUF_SIZE)
                except socket.error:
                    self.serverShutdown()
                try:
                    data = pickle.loads(dataRaw)
                except:
                    break
                if data=="p": #Was pinged
                    self.tsock.sendall(pickle.dumps("p"))
                else:
                    pass

test = Client("169.254.63.227")
if test.failConnect:
    print("Failed to connect!")
else:
    print("Conntected!")
    while True:
        test.loop()
