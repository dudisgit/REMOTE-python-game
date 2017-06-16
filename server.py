import socket,select,pickle,time

UDP_port = 3745 #Port for fast pase data transfer, e.g. moving objects
TCP_port = 3746 #Port for serious data transfer, e.g. chat messages
TCP_BUF_SIZE = 4046
UDP_BUF_SIZE = 512
MAX_PLAYER = 60
PING_INTERVAL = 5 #Seconds to send a ping interval again
SLOW_UPDATE_SPEED = 0.3 #Seconds between sending a slow update packet, (initaly syncing variables when joining a server or changing map) TCP connection.
MAX_FREQUENT = 12 #Max number of variables allowed in the frequently changed list, increasing may resolve sync issues but would also slow network down
FREQUENT_TIME = 5 #Seconds to update all users with frequently changed variables
ERROR = None #Function to call when an error happens

class Player: #Class used to store a player
    def __init__(self,ip,sock,usock):
        self.ip = ip
        self.tsock = sock
        self.usock = usock
        self.tick = 22 #Default
        self.sender = False
        self.updateSlow = [] #Packets to send slowly to the user (This will be populated when the user first joins or the map is changed)
        self.updateSlowTimer = time.time()
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
        if time.time()>self.__tickSend and len(self.updateSlow)==0: #Send the buffer to the user because its the users tick
            self.__tickSend = time.time()+(1/self.tick) #Reset the tick to next time
            if len(self.__buffer)!=0: #TCP messages
                self.tsock.send(pickle.dumps(self.__buffer))
                self.__buffer = []
            if len(self.__buffer2)!=0: #UDP messages
                self.usock.sendto(pickle.dumps(self.__buffer2),(self.ip,UDP_port))
                self.__buffer2 = []
        elif len(self.updateSlow)!=0 and time.time()>self.updateSlowTimer:
            self.updateSlowTimer = time.time()+SLOW_UPDATE_SPEED
            self.tsock.send(pickle.dumps(self.updateSlow.pop(0)))
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
        else:
            ERROR("copyIter, unsupported variable type",type(lis[a]))
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
        ERROR("varInitial, unsupported variable type",type(var))
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
        self.__frequent = [] #A list of frequently changes variables, use MAX_FREQUENT to increase size
        self.__UpdateFrequent = time.time()+FREQUENT_TIME #Time given to update all clients with frequently changed variables
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
    def __clientDisconnect(self,sock): #A client disconnected
        self.users.pop(sock.getpeername()[0])
        self.__tlist.remove(sock)
        print("Disconnect ",sock.getpeername())
    def getValue(self,path,currentList): #Returns the value at the specified path (path is a list)
        if type(currentList[path[0]])==dict:
            return self.getValue(path[1:],currentList[path[0]])
        return currentList[path[0]]
    def detectChanges(self,val1,val2): #Returns the changes in the variable
        if type(val1)==int or type(val1)==float:
            return val2-val1
        if type(val1)==bool:
            return int(val2)
        return val2
    def sensify(self,changeData,changeBy=True): #Turns results that come back from "detectChanges" in a sendable format.
        res = []
        for a in changeData: #Loop through all the items that "detectChanges" has given
            path = [] #Path towards the varible through dictionaries
            tcp = False #Used to detect if the variable is a TCP connection (if it should be sent over TCP, its path or name must begin with a capital letter)
            for i,c in enumerate(a): #Construct a path for the variable changing/deleting/creation
                path.append(c)
                if c[0].upper()==c[0]:
                    tcp = True
                if i>=len(a)-2 or (a[-1]=="new" and i>=len(a)-4):
                    if a[-1]=="new" and i>=len(a)-4 and i==0:
                        path = []
                        tcp = a[-3][0].upper()==a[-3][0]
                    break
            if a[-1]=="new": #New item has been added to the dictionary or the variables type has changed
                res.append(["n"+a[-3],a[-2]]+path) #["nVariable_name",VALUE,Path]
            elif a[-1]=="delete": #An item has been deleted from the dictionary
                res.append(["d"]+path) #["d",Path]
            elif a[-1]=="value change" or a[-1]=="type change": #A variable has changed its value
                valueBefore = self.getValue(path,self.__SYNCBefore) #Get the variable as it was before the change
                value = self.getValue(path,self.SYNC) #Get the variables new value
                if changeBy and not tcp and a[-1]!="type change": #Should be sent over UDP connection (sends changes in variable rather then its new value)
                    res.append(["s",self.detectChanges(valueBefore,value)]+path) #Send what it has changed by
                else: #Send the whole value of the variable
                    res.append(["s",value]+path) #Send the whole value
                #["s",VALUE/CHANGE,Path]
        return res
    def detectAndApplySYNC(self): #Checks if "SYNC" has changes and then applies it to send changes to all users
        change = detectChanges(self.__SYNCBefore,self.SYNC)
        if len(change)!=0:
            sendChange = self.sensify(change)
            sendUDP = [] #A list containing all the UDP data to send
            sendTCP = [] #A list containing all the TCP data to send
            for a in sendChange: #Loop through the changes and detect if a message is TCP or UDP
                tcp = False
                path = [] #Path to the variable being edited/deleted
                for i,b in enumerate(a):
                    if ((a[0][0]=="n" or a[0][0]=="s") and i>1) or a[0][0]=="d":
                        path.append(b)
                        if b[0].upper()==b[0]: #Is TCP
                            tcp = True
                            break
                if not path in self.__frequent and len(path)!=0: #Add the variable to a frequency list
                    #If the variable is placed in here it will be updated fully in a given time slice
                    self.__frequent.append(path)
                    if len(self.__frequent)>MAX_FREQUENT:
                        self.__frequent.pop(0)
                if tcp:
                    sendTCP.append(a)
                else:
                    sendUDP.append(a)
            for a in self.users: #Send the UDP and TCP data to every player in the game
                if not self.users[a].sender:
                    if len(sendTCP)!=0:
                        self.users[a].sendTCP(sendTCP)
                    if len(sendUDP)!=0:
                        self.users[a].sendUDP(sendUDP)
            self.__SYNCBefore = varInitial(self.SYNC) #Apply the changes so further changes in SYNC can be detected.
    def uploadFrequent(self): #Sends frequently changed variables full value to all players if timer has expired
        if time.time()>self.__UpdateFrequent:
            self.__UpdateFrequent = time.time()+FREQUENT_TIME
            msg = []
            for a in self.__frequent:
                msg.append(["s",self.getValue(a,self.SYNC)]+a)
            for a in self.users:
                self.users[a].sendTCP(msg)
    def close(self): #Closes all sockets
        self.__usock.close()
        self.__tsock.close()
    def setVariable(self,lis,path,value): #Set a varable using a path list
        if not path[0] in lis:
            if len(path)==1:
                lis[path[0]] = value
                return None
            else:
                lis[path[0]] = {}
        if type(lis[path[0]])==dict:
            self.setVariable(lis[path[0]],path[1:],value)
        else:
            lis[path[0]] = value
    def deleteVariable(self,lis,path): #Delete a variable using a path list
        if not path[0] in lis:
            if len(path)!=1:
                lis[path[0]] = {}
        if type(lis[path[0]])==dict:
            self.deleteVariable(lis[path[0]],path[1:])
        else:
            if path[0] in lis:
                lis.pop(path[0])
    def doCommand(self,data,tcpSent=False): #Called either from UDP or TCP connections. Their transmission data is the same format!
        if type(data)!=list:
            return False
        if type(data[0])==str: #A trigger or update communication
            if len(data[0])==0:
                return False
            if data[0][0]=="n": #New variable / Variable type changed
                if len(data[0])==1:
                    return False
                self.setVariable(self.SYNC,data[2:]+[data[0][1:]],data[1])
            elif data[0][0]=="d": #Delete a variable
                if len(data)==1:
                    return False
                self.deleteVariable(self.SYNC,data[1:])
            elif data[0][0]=="s": #Change a variable
                if len(data)<2:
                    return False
                tcp = False
                for b in data[2:]:
                    if b[0].upper()==b[0]:
                        tcp = True
                        break
                if tcpSent or tcp:
                    self.setVariable(self.SYNC,data[2:],data[1])
                else:
                    change = self.getValue(data[2:],self.SYNC)
                    if type(change)==int or type(change)==float:
                        self.setVariable(self.SYNC,data[2:],change+data[1])
                    elif type(change)==bool:
                        self.setVariable(self.SYNC,data[2:],data[1]==1)
                    else:
                        self.setVariable(self.SYNC,data[2:],data[1])
    def receive(self,data,tcpSent=False):
        if len(data)==0:
            return False
        for a in data:
            self.doCommand(a,tcpSent)
        print(self.SYNC)
    def loop(self): #Must be called continualy
        self.loopUDP()
        self.loopTCP()
        self.detectAndApplySYNC()
        self.uploadFrequent()
        for a in self.users:
            self.users[a].loop()
            self.users[a].sender = False
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
                    self.users[con[0]].sender = True
                    self.receive(data)
    def loopTCP(self): #This function must be called continuesly in order to update the TCP server
        read,write,err = select.select(self.__tlist,[],[],0) #Get all events to do with the socket
        for sock in read:
            if sock==self.__tsock: #A new connection has came in
                con,addr = self.__tsock.accept()
                self.__tlist.append(con)
                print("New connection (TCP)",addr) #Will be removed
                self.users[addr[0]] = Player(addr[0],con,self.__usock)
                self.users[addr[0]].updateSlow = self.sensify(detectChanges({},self.SYNC),False) #Send the whole SYNC list to the user
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
                            self.users[sock.getpeername()[0]].sender = True
                            self.receive(data,True)

