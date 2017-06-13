import socket,select,pickle,time

UDP_port = 3745 #Port for fast pase data transfer, e.g. moving objects
TCP_port = 3746 #Port for serious data transfer, e.g. chat messages
BUF_SIZE = 4046
MAX_PLAYER = 60
PING_INTERVAL = 5 #Seconds to send a ping interval again

class Player: #Class used to store a player
    def __init__(self,ip,sock,usock):
        self.ip = ip
        self.tsock = sock
        self.usock = usock
        self.tick = 22 #Default
        self.minTick = 10 #Minimum tick that tick can be lowered too
        self.maxTick = 25 #Maximum tick that tick can be highered too
        self.__tickSend = time.time()+(1/self.tick)
        self.__pingTime = time.time()+PING_INTERVAL
        self.__buffer = [] #Data to send to the user over TCP
        self.__buffer2 = [] #Data to send to the user over UDP
        self.__pingBefore = -1 #Time the ping was sent at
        self.ping = 0 #The current ping for the user
    def receivedPing(self): #Called when the user sent a message back because of a ping
        if self.__pingBefore!=-1:
            SEND = (time.time()-self.__pingBefore)/2
            self.ping = SEND*1000
            self.tick = 1/SEND
            if self.tick<self.minTick:
                self.tick = self.minTick+0
            elif self.tick>self.maxTick:
                self.tick = self.maxTick+0
            self.__pingBefore = -1
    def sendUDP(self,mes): #Add a UDP message to the buffer
        self.__buffer2.append(mes)
    def sendTCP(self,mes): #Add a TCP message to the buffer
        self.__buffer.append(mes)
    def loop(self): #Called continuesly
        if time.time()>self.__tickSend: #Send the buffer to the user because its the users tick
            self.__tickSend = time.time()+(1/self.tick) #Reset the tick to next time
            if len(self.__buffer)!=0: #TCP messages
                self.tsock.send(pickle.dumps(self.__buffer))
                self.__buffer = []
            if len(self.__buffer2)!=0: #UDP messages
                self.usock.sendto(pickle.dumps(self.__buffer2),(self.ip,UDP_port))
                self.__buffer2 = []
        if time.time()>self.__pingTime:
            self.__pingTime = time.time()+PING_INTERVAL
            self.__pingBefore = time.time()
            self.tsock.send(pickle.dumps("p"))

class Server: #Class for a server
    def __init__(self,ip=socket.gethostbyname(socket.gethostname())):
        self.ip = ip
        self.SYNC = {} #This contains a list of all the variables to synk with clients
        self.users = {} #A list of users connected
        #UDP socket
        self.usock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #Set up a UDP socket
        self.usock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
        self.usock.bind((self.ip,UDP_port)) #Bind the UDP socket to an IP and port
        #TCP socket
        self.tsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #Set up a TCP socket
        self.tsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
        self.tsock.bind((self.ip,TCP_port)) #Bind the TCP socket to an IP and port
        self.tsock.listen(MAX_PLAYER)
        self.tlist = [self.tsock] #Socket list for the TCP socket

        print("Binded to "+self.ip+" on port "+str(TCP_port)+" and "+str(UDP_port))
    def close(self): #Closes all sockets
        self.usock.close()
        self.tsock.close()
    def loop(self): #Must be called continualy
        self.loopUDP()
        self.loopTCP()
        for a in self.users:
            self.users[a].loop()
    def loopUDP(self): #This function must be called continuesly in order to update the UDP server
        read,write,err = select.select([self.usock],[],[],0) #Get all events to do with the socket
        for sock in read:
            dataRaw,con = sock.recvfrom(BUF_SIZE)
            if dataRaw and con[0] in self.users: #Succsessfuly received and is a valid user
                data = pickle.loads(dataRaw) #Load the data received
                #Code to react to UDP receiving data will be here
    def loopTCP(self): #This function must be called continuesly in order to update the TCP server
        read,write,err = select.select(self.tlist,[],[],0) #Get all events to do with the socket
        for sock in read:
            if sock==self.tsock: #A new connection has came in
                con,addr = self.tsock.accept()
                self.tlist.append(con)
                print("New connection (TCP)",addr)
                self.users[addr[0]] = Player(addr[0],con,self.usock)
            else: #A message was received
                dataRaw = sock.recv(BUF_SIZE)
                if dataRaw: #Succsessfuly received
                    data = pickle.loads(dataRaw) #Load the data received
                    #print("Got data (TCP)",data)
                    if data=="p": #A ping was received
                        self.users[sock.getpeername()[0]].receivedPing()
                    else:
                        #Code for receiving TCP data will be here
                        pass
