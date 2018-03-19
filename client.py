import socket,select,pickle,time,os,traceback
import multiprocessing as mp

selfIp = socket.gethostbyname(socket.gethostname()) #"169.254.178.71"
TCP_BUF_SIZE = 4046
MAX_KEEP = 60 # Maximum number of packets kept by the server when a packet was missed.
UPDATE_RATE = 0.075 #Rate at which the client should sent updates to the server (UDP/TCP)

def bufferThread(servIP,port,active,sendQueue,ReceiveQueue): #Is used for in threading to seperate the game and socket sending/receiving
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
    sock.settimeout(5)
    failed = False
    print("Thread started and binded, process ID = ",os.getpid())
    try: #Attempt to connect to the server
        sock.connect((servIP,port))
    except socket.timeout: #Timeout error
        active.value = -3
        traceback.print_exc()
        failed = True
    except socket.error: #Connection error
        active.value = -1
        traceback.print_exc()
        failed = True
    except: #Unknown error
        active.value = -2
        failed = True
        traceback.print_exc()
    print("Connected")
    while active.value>time.time() and not failed: #Loop until the program is closed
        read,write,err = select.select([sock],[],[],0)
        for Sock in read: #Go through all packets being received
            if Sock == sock:
                try: #Attempt to receive packet
                    data = sock.recv(TCP_BUF_SIZE)
                except socket.error: #Socket was disconnected
                    print("Connection failure, attempting to connect again")
                    try: #Attempt to connect again
                        sock.connect((servIP,port))
                    except: #Failed
                        print("Failed to connect")
                        sock.close()
                        active.value = -1
                        traceback.print_exc()
                        failed = True
                    else:
                        print("Connected")
                except: #Unknown error
                    active.value = -2
                    traceback.print_exc()
                    failed = True
                try: #Attempt to read packet
                    qr = pickle.loads(data)
                except: #Error when reading
                    pass
                else: #Sucsessful
                    if qr=="p": #Message is a ping
                        sock.sendall(pickle.dumps("p"))
                    else: #Normal message
                        ReceiveQueue.put(data)
        while not sendQueue.empty(): #Send all awaiting packets
            try:
                sock.sendall(sendQueue.get())
            except BrokenPipeError:
                active.value = -1
                traceback.print_exc()
                failed = True
    print("Closesd thread")
    sock.close()

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

class Client:
    def __init__(self,serverIp,tcpPort=3746,thread=False):
        self.SYNC = {} #A list of variables that gets synced with the server
        self.__SYNCBefore = {} #A list to detect changes in SYNC
        self.TRIGGER = {} #A list containing pointers to functions if the server calls them
        self.loading = True #Game is loading
        self.__thread = thread
        self.finishLoading = None #Function to call when the main content from the server has finished downloading
        self.__loadCur = 0 #Current packet loading
        self.__loadingMax = 0 #Max loading packets (used to calculate percentage)
        self.__serverIp = serverIp #IP of the server
        self.__tcpPort = tcpPort
        self.errorReason = "Unknown" #Reason for the error in connection
        if thread: #Threading enabled
            self.__queue = mp.Queue() #Sending queue
            self.__recQueue = mp.Queue() #Receiving queue
            self.__active = mp.Value("i",int(time.time()+5)) #Active queue
            self.__proc = mp.Process(target=bufferThread,args=(serverIp,tcpPort,self.__active,self.__queue,self.__recQueue,))
            self.__proc.start() #Start the thread
            self.__tsock = None
        else: #Normal mode
            self.__tsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #Setup TCP socket
            self.__tsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
            self.__tsock.settimeout(5) #Disconnect after 5 seconds
        self.__IDSend = 0 #Used to tell the position in the sending list
        self.__IDRec = 0 #Used to tell the position in the receiving list
        self.__ReceiveBuffer = [] #Used to track missing packets and ensure order of packets
        self.__SendingBuffer = [] #Used to store packets incase the server didon't receive one properly
        self.__resent = [] #Packets that where resent by the server, this list will be releatively small but fixes a problem
        self.__ignorePackets = {} #Packet ID's to ignore (ID will be removed if message is different)
        self.__UpdateTime = time.time()+UPDATE_RATE # Rate at which this client should send data to the server
        for i in range(MAX_KEEP): #Fill with buffers with empty items
            self.__ReceiveBuffer.append(None)
            self.__SendingBuffer.append(None)
        if not thread:
            try: #Attempt to connect to the server
                self.__tsock.connect((serverIp,tcpPort))
            except ConnectionRefusedError: #An error occured while connecting...
                self.failConnect = True
                traceback.print_exc()
                self.errorReason = "Connection refused"
            except ConnectionResetError:
                self.failConnect = True
                traceback.print_exc()
                self.errorReason = "Connection reset"
            except socket.timeout:
                self.failConnect = True
                traceback.print_exc()
                self.errorReason = "Timed out"
            except: #Unknown error
                self.failConnect = True
                traceback.print_exc()
                self.errorReason = "Other error, check console"
            else:
                self.failConnect = False
        else:
            self.failConnect = False
    def getInfo(self): #Returns info about the receiving buffer
        res = []
        for a in self.__ReceiveBuffer:
            if a is None:
                res.append(False)
            else:
                res.append(len(a))
        return self.__IDRec,res
    def loop(self):
        if self.failConnect:
            return 0
        if self.__thread:
            if self.__active.value>0: #Working correctly
                self.__active.value = int(time.time()+5) #Update thread
            elif self.__active.value==-1: #Thread had a connection failure
                self.errorReason = "Connection lost"
                self.failConnect = True
            elif self.__active.value==-2: #Thread had an unknown error
                self.errorReason = "Other error, check console"
                self.failConnect = True
            elif self.__active.value==-3: #Thread timed out
                self.errorReason = "Timed out"
                self.failConnect = True
            if not self.__proc.is_alive() and not self.failConnect: #Thread closed without communication of failure
                self.failConnect = True
                self.errorReason = "Connection thread closed, check console"
        self.tcpLoop() #Process all receiving packets
        if time.time()>self.__UpdateTime:
            self.__UpdateTime = time.time()+UPDATE_RATE
            self.detectAndApplySYNC() #Process all outgoing packets
    def __sendUDP(self,mes): #Sends a message over UDP
        if self.__thread:
            self.__queue.put(pickle.dumps(mes))
        else:
            try:
                self.__tsock.sendall(pickle.dumps(mes))
            except BrokenPipeError:
                self.serverShutdown()
    def __sendTCP(self,mes): #Sends a message over TCP
        if type(mes)==list: #Message is a list, allowed to send over UDP
            if self.__thread:
                self.__queue.put(pickle.dumps([self.__IDSend]+mes))
            else:
                try:
                    self.__tsock.sendall(pickle.dumps([self.__IDSend]+mes))
                except BrokenPipeError:
                    self.serverShutdown()
            self.__SendingBuffer[self.__IDSend] = [self.__IDSend]+mes
            self.__IDSend = (self.__IDSend + 1) % MAX_KEEP
        else: #Send it as UDP
            if self.__thread:
                self.__queue.put(pickle.dumps(mes))
            else:
                try:
                    self.__tsock.sendall(pickle.dumps(mes))
                except BrokenPipeError:
                    self.serverShutdown()
    def serverShutdown(self): #The server has shutdown!
        print("Lost connection to server!")
        print("Attempting to connect...")
        self.failConnect = True
        try:
            self.__tsock.connect((self.__serverIp,self.__tcpPort))
        except ConnectionAbortedError:
            traceback.print_exc()
            self.errorReason = "Connectino aborted"
        except ConnectionRefusedError:
            traceback.print_exc()
            self.errorReason = "Connection reset"
        except socket.timeout:
            traceback.print_exc()
            self.errorReason = "Timed out"
        except: #Unknwon error
            traceback.print_exc()
            self.errorReason = "Other, check console"
        else:
            self.failConnect = False
            print("Connected!")
    def close(self): #Closes the client socket
        self.failConnect = True
        self.errorReason = "Client closed"
        if not self.__thread:
            self.__tsock.close()
    def setVariable(self,lis,path,value): #Set a varable using a path list
        if not path[0] in lis: #Create new variable
            if len(path)==1: #Create the new variable as a normal
                lis[path[0]] = value
                return None
            else: #Create the new variable as a dictionary
                lis[path[0]] = {}
        if type(lis[path[0]])==dict and len(path)!=1: #Set a variable inside the keys dictionary
            self.setVariable(lis[path[0]],path[1:],value)
        else:
            lis[path[0]] = value
    def getVariable(self,lis,path): #Get the value of a variable using a path list
        if not path[0] in lis:
            if len(path)==1:
                return 0
            else:
                lis[path[0]] = {}
        if type(lis[path[0]])==dict and len(path)!=1:
            return self.getVariable(lis[path[0]],path[1:])
        else:
            return lis[path[0]]
    def deleteVariable(self,lis,path): #Delete a variable using a path list
        if not path[0] in lis:
            if len(path)!=1:
                lis[path[0]] = {}
        if type(lis[path[0]])==dict and len(path)!=1:
            self.deleteVariable(lis[path[0]],path[1:])
        else:
            if path[0] in lis:
                lis.pop(path[0])
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
                valueBefore = self.getVariable(self.__SYNCBefore,path) #Get the variable as it was before the change
                value = self.getVariable(self.SYNC,path) #Get the variables new value
                if changeBy and not tcp and a[-1]!="type change": #Should be sent over UDP connection (sends changes in variable rather then its new value)
                    res.append(["s",self.detectChanges(valueBefore,value)]+path) #Send what it has changed by
                else: #Send the whole value of the variable
                    res.append(["s",value]+path) #Send the whole value
                #["s",VALUE/CHANGE,Path]
        return res
    def detectAndApplySYNC(self): #Checks if "SYNC" has changes and then applies it to send changes to the server
        change = detectChanges(self.__SYNCBefore,self.SYNC)
        if len(change)!=0:
            sendChange = self.sensify(change)
            sendUDP = [] #A list containing all the UDP data to send
            sendTCP = [] #A list containing all the TCP data to send
            for a in sendChange: #Loop through the changes and detect if a message is TCP or UDP
                tcp = False
                for i,b in enumerate(a):
                    if ((a[0][0]=="n" or a[0][0]=="s") and i>1) or a[0][0]=="d":
                        if b[0].upper()==b[0]: #Is TCP
                            tcp = True
                            break
                if tcp:
                    sendTCP.append(a)
                else:
                    sendUDP.append(a)
            if len(sendTCP)!=0:
                self.__sendTCP(sendTCP)
            if len(sendUDP)!=0:
                self.__sendUDP(sendUDP)
            self.__SYNCBefore = varInitial(self.SYNC) #Apply the changes so further changes in SYNC can be detected.
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
                self.setVariable(self.__SYNCBefore,data[2:]+[data[0][1:]],data[1])
            elif data[0][0]=="d": #Delete a variable
                if len(data)==1:
                    return False
                try:
                    self.deleteVariable(self.SYNC,data[1:])
                    self.deleteVariable(self.__SYNCBefore,data[1:])
                except:
                    print("Failed to delete variable path ",data[1:])
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
                    self.setVariable(self.__SYNCBefore,data[2:],data[1])
                else:
                    change = self.getVariable(self.SYNC,data[2:])
                    if type(change)==int or type(change)==float:
                        self.setVariable(self.SYNC,data[2:],change+data[1])
                        self.setVariable(self.__SYNCBefore,data[2:],change+data[1])
                    elif type(change)==bool:
                        self.setVariable(self.SYNC,data[2:],data[1]==1)
                        self.setVariable(self.__SYNCBefore,data[2:],data[1]==1)
                    else:
                        self.setVariable(self.SYNC,data[2:],data[1])
                        self.setVariable(self.__SYNCBefore,data[2:],data[1])
            elif data[0][0]=="t": #A trigger was sent to call a function
                if data[0][1:] in self.TRIGGER:
                    self.TRIGGER[data[0][1:]](*tuple(data[1:]))
            elif data[0][0]=="L": #Stop loading the game
                self.loading = False
                if not self.finishLoading is None:
                    self.finishLoading()
                print("Loading END")
    def sendTrigger(self,funcName,*args):
        self.__sendTCP([["t"+funcName]+list(args)])
    def getPercent(self): #Returns the loading percentage
        if self.__loadingMax==0:
            return 0
        else:
            return self.__loadCur/self.__loadingMax
    def receive(self,data,tcpSent=False): #Received a packet
        if len(data)==0: #No data, exiting
            return False
        if self.loading:
            self.__loadCur += 1
        #print(data)
        if type(data[0])==list: #Is a bundle of commands
            for a in data:
                if type(a) == list:
                    if len(a)!=0:
                        if type(a[0]) == list:
                            if len(a[0])!=0: #If for some odd reason the message had anouther bundle inside this bundle
                                for b in a:
                                    self.doCommand(b,tcpSent)
                        else: #Process normaly
                            self.doCommand(a,tcpSent)
                else: #Process the single charicter as a list
                    self.doCommand([a],tcpSent)
        elif data[0]=="r": #Resend a message if the server missed it.
            if data[1]<len(self.__SendingBuffer) and data[1]>=0: #Check if the packet is out of range
                self.__sendUDP(self.__SendingBuffer[data[1]]) #Resend missing packet to server
        elif data[0][0]=="l": #Loading a map
            self.loading = True
            self.__loadingMax = int(data[0][1:])
            self.__loadCur = 0
            print("Loading START",data[0])
        else: #Is a single command
            self.doCommand(data,tcpSent)
    def countTCPPackets(self): #Counts how many TCP packets there are
        num = 0
        for a in self.__ReceiveBuffer:
            num += int(not a is None) #Add if the item in the list is not empty
        return num
    def tcpLoop(self): #Loop for tcp connection
        if self.__thread:
            read = []
            while not self.__recQueue.empty():
                read.append(self.__recQueue.get())
        else:
            read,write,err = select.select([self.__tsock],[],[],0)
        for sock in read:
            if sock == self.__tsock or self.__thread:
                if self.__thread:
                    try:
                        data = pickle.loads(sock)
                    except:
                        break
                else:
                    try:
                        dataRaw = sock.recv(TCP_BUF_SIZE)
                    except socket.error:
                        self.serverShutdown()
                    try:
                        data = pickle.loads(dataRaw)
                    except:
                        break
                if data!="p": #Is not a ping message
                    if type(data[0]) == int: #Message linked with an ID
                        if data[0]<len(self.__ReceiveBuffer) and data[0]>=0: #ID is in range with KEEP
                            shouldReceive = True #Is the packet not a duplicate
                            if data[0] in self.__resent: #ID was expected to be received
                                self.__resent.remove(data[0]) #Do not include this ID as an expected one in the future
                                self.__ignorePackets[data[0]] = data[1:] #Mark this ID as a duplicate for future packets if they are detected
                            elif data[0] in self.__ignorePackets: #Packet might be a duplicate
                                if self.__ignorePackets[data[0]]!=data[1:]: #Packet is different, remove mark as duplicate
                                    self.__ignorePackets.pop(data[0])
                                else: #Packet is a duplicate, ignore!
                                    shouldReceive = False
                            if shouldReceive:
                                self.__ReceiveBuffer[data[0]] = data[1:]
                    else:
                        self.receive(data) #Receive the data as UDP
                    tCount = self.countTCPPackets()
                    if tCount>=1:
                        START = self.__IDRec + 0
                        while not self.__ReceiveBuffer[self.__IDRec] is None: #Go through pending packets and process them all
                            self.receive(self.__ReceiveBuffer[self.__IDRec],True)
                            self.__ReceiveBuffer[self.__IDRec] = None
                            self.__IDRec = (self.__IDRec+1) % MAX_KEEP
                        if self.countTCPPackets()!=0: #Packets are missing, request them.
                            if not self.__IDRec in self.__resent:
                                self.__resent.append(self.__IDRec+0)
                            if self.__thread:
                                self.__queue.put(pickle.dumps(["r",self.__IDRec]))
                            else:
                                self.__tsock.send(pickle.dumps(["r",self.__IDRec]))
                else: #Was pinged
                    self.__sendTCP("p")
