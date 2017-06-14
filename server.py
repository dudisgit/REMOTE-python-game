import socket,select,pickle,time

UDP_port = 3745 #Port for fast pase data transfer, e.g. moving objects
TCP_port = 3746 #Port for serious data transfer, e.g. chat messages
TCP_BUF_SIZE = 4046
UDP_BUF_SIZE = 512
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

def copyIter(lis): #Copies a list so the items are not pointers
    res = {}
    for a in lis:
        if type(lis[a])==dict: #If anoutehr list of dictionary is detected then use rescusion and copy the contents inside
            res[a] = copyIter(lis[a])
        elif type(lis[a])==str: #Copy string
            res[a] = lis[a]+""
        elif type(lis[a])==float or type(lis[a])==int: #Copy number
            res[a] = lis[a]+0
        elif type(lis[a])==bool:
            res[a] = lis[a] == True
    return res
def varInitial(var): #Puts the variable into an intermediate form for detecting varaible changes
    if type(var)==str: #Copy string
        return var+""
    elif type(var)==int or type(var)==float: #Copy number
        return var+0
    elif type(var)==bool:
        return var==True
    elif type(var)==dict: #Copy dictionary
        return copyIter(var)
    else: #Raise an error because the type of variable isn't supported
        print("Error in varInitial, unsupported variable type",type(var))
def detectChanges(before,after): #Detects all the changes between one variable and anouther
    #The following is what this will return in a list
    #[index, "type change"] = The varible at "index" has changed its type
    #[index, "value change"] = The variable at "index" has changes its value
    #[index, "delete"] = The variable has been deleted at "index"
    #[index, value, "new"] = A new varible has been created and set to "value" with index "index"
    #This might be in a larger list if there are lists in lists, e.g.
    #[index_1,index_2,_index_3,index_4,"value change"]
    if type(before)==dict: #Depth searching
        changes = []
        if type(before)!=type(after): #The variable types have changes completely
            return "type change"
        inter = list(after) #A list of keys
        for a in before: #Loop through each item of the list
            if a in inter: #Does the variable exist inside the dictionary?
                if type(before[a])!=type(after[a]): #Varible type has changed
                    changes.append([a+"","type change"])
                elif type(before[a])==dict: #Iteration loop to detect changes in both dictionaries
                    changes2 = detectChanges(before[a],after[a]) #Find changes in the list
                    for b in changes2: #Put all the changes inside "change" but add its index at the start so it has a path!
                        changes.append([a+""]+b)
                elif before[a]!=after[a]:
                    changes.append([a+"","value change"])
                inter.remove(a) #Remove the variable so duplicate variables are encountered as well.
            else: #Items have been deleted from "after"
                changes.append([a+"","delete"])
        for a in inter: #Should be empty but if not then there are new varibles that have been added
            changes.append([a, after[a], "new"])
        return changes
    elif type(before)!=type(after): #Variable type has completely changed
        return "type change"
    elif before!=after: #Varibles are not equal
        return "value change"
    return None #No changes atall


class Server: #Class for a server
    def __init__(self,LINK,ip=socket.gethostbyname(socket.gethostname())):
        self.LINK = LINK
        self.__ip = ip
        self.SYNC = {} #This contains a list of all the variables to synk with clients
        self.__SYNCBefore = {} #To detect changes in "SYNC"
        self.users = {} #A list of users connected
        #UDP socket
        self.__usock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #Set up a UDP socket
        self.__usock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
        self.__usock.bind((self.__ip,UDP_port)) #Bind the UDP socket to an IP and port
        #TCP socket
        self.__tsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #Set up a TCP socket
        self.__tsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
        self.__tsock.bind((self.__ip,TCP_port)) #Bind the TCP socket to an IP and port
        self.__tsock.listen(MAX_PLAYER)
        self.__tlist = [self.__tsock] #Socket list for the TCP socket

        print("Binded to "+self.__ip+" on port "+str(TCP_port)+" and "+str(UDP_port))
        self.sensify([["p1","p1.5","p2","p3","new"]])
    def __clientDisconnect(self,sock): #A client disconnected
        self.users.pop(sock.getpeername()[0])
        self.__tlist.remove(sock)
        print("Disconnect ",sock.getpeername())
    def sensify(self,changeData,changeBy=False): #Turns results that come back from "detectChanges" in a sendable format.
        res = []
        for a in changeData:
            path = [] #Path towards the varible through dictionaries
            tcp = False #If it should send the message over TCP
            for i,c in enumerate(a):
                path.append(c)
                tcp = c[0].upper()==c[0]
                if i>=len(a)-2 or (a[-1]=="new" and i>=len(a)-4):
                    if a[-1]=="new" and i>=len(a)-4 and i==0:
                        path = []
                        tcp = a[0][0].lower()!=a[0][0]
                    break
            print(path)
            if a[-1]=="new": #New item has been added to the dictionary
                res.append(["n"+a[-3],a[-2]]+path)
            elif a[-1]=="delete":
                res.append(["d"]+path)
            elif a[-1]=="value change":
                if changeBy:
                    pass #Send what it has changed by
                else:
                    res.append(["s"]) #I left off here... ________________________________________________________________________________________________
            if tcp:
                res[-1][0][0] = res[-1][0][0].upper()
        return res
    def detectAndApplySYNC(self): #Checks if "SYNC" has changes and then applies it to send changes to all users
        change = detectChanges(self.__SYNCBefore,self.SYNC)
        #self.sensify(change)
        self.__SYNCBefore = varInitial(self.SYNC)
    def close(self): #Closes all sockets
        self.__usock.close()
        self.__tsock.close()
    def loop(self): #Must be called continualy
        self.loopUDP()
        self.loopTCP()
        self.detectAndApplySYNC()
        for a in self.users:
            self.users[a].loop()
    def loopUDP(self): #This function must be called continuesly in order to update the UDP server
        read,write,err = select.select([self.__usock],[],[],0) #Get all events to do with the socket
        for sock in read:
            dataRaw,con = sock.recvfrom(UDP_BUF_SIZE)
            if dataRaw and con[0] in self.users: #Succsessfuly received and is a valid user
                try: #Try to read data received from UDP connection
                    data = pickle.loads(dataRaw) #Load the data received
                except: #Do nothing if the data is corrupted
                    pass
                else:
                    #Code to react to UDP receiving data will be here
                    pass
    def loopTCP(self): #This function must be called continuesly in order to update the TCP server
        read,write,err = select.select(self.__tlist,[],[],0) #Get all events to do with the socket
        for sock in read:
            if sock==self.__tsock: #A new connection has came in
                con,addr = self.__tsock.accept()
                self.__tlist.append(con)
                print("New connection (TCP)",addr) #Will be removed
                self.users[addr[0]] = Player(addr[0],con,self.usock)
            else: #A message was received
                try:
                    dataRaw = sock.recv(TCP_BUF_SIZE)
                except socket.error: #Error receiving, client must have disconnected!!
                    self.__clientDisconnect(sock)
                    dataRaw = False
                if dataRaw: #Succsessfuly received (should)
                    try: #Attempt to read the data being received
                        data = pickle.loads(dataRaw) #Load the data received
                    except: #Data is currupted, do nothing
                        pass
                    else: #Received sucsessfuly
                        if data=="p": #A ping was received
                            self.users[sock.getpeername()[0]].receivedPing()
                        else:
                            #Code for receiving TCP data will be here
                            pass

