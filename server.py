import socket,select,pickle,time,render, os, importlib, sys
import entities.base as base


TCP_port = 3746 #Port for serious data transfer, e.g. chat messages
TCP_BUF_SIZE = 4046 #Receiving buffer size
MAX_PLAYER = 60
PING_INTERVAL = 5 #Seconds to send a ping interval again
SLOW_UPDATE_SPEED = 0.15 #Seconds between sending a slow update packet, (initaly syncing variables when joining a server or changing map) TCP connection.
MAX_FREQUENT = 5 #Max number of variables allowed in the frequently changed list, increasing may resolve sync issues but would also slow network down
FREQUENT_TIME = 5 #Seconds to update all users with frequently changed variables
ERROR = None #Function to call when an error happens
MAX_KEEP = 60 # Maximum packets to keep for users to access if missed, the higher this the more memory used and possibly a user could request a packet from a while ago.
MAX_PACKET = 200 #Maximum size of one packet sent to a user

class Player: #Class used to store a player
    def __init__(self,ip,sock):
        self.ip = ip #IP of the player
        self.tsock = sock #Socket for the player/client
        self.tick = 22 #Default
        self.sender = False #Is the source of a changed variable
        self.updateSlow = [] #Packets to send slowly to the user (This will be populated when the user first joins or the map is changed)
        self.updateSlowTimer = time.time() #Used for sending SYNC completely
        self.minTick = 10 #Minimum tick that tick can be lowered too
        self.maxTick = 25 #Maximum tick that tick can be highered too
        self.__tickSend = time.time()+(1/self.tick) #Tick rate, used to determine how fast packets should be sent to a user
        self.__pingTime = time.time()+PING_INTERVAL #When should ping next
        self.__buffer = [] #Data to send to the user over TCP
        self.__buffer2 = [] #Data to send to the user over UDP
        self.__pingBefore = -1 #Time the ping was sent at
        self.__IDSend = 0 #ID of a sending packets
        self.IDRec = 0 #ID of receiving messages
        self.ReceiveBuffer = [] #Used for tracking missing packets and ensuring packet order
        self.SendingBuffer = [] #Used to store previous packets for clients to access if requested
        self.resent = [] #Packets that where resent by the client, this list will be releatively small but fixes a problem
        self.ignorePackets = {} #Packet ID's to ignore (ID will be removed if message is different)
        for i in range(MAX_KEEP): #Fill the receive and sending buffer with empty variables
            self.ReceiveBuffer.append(None)
            self.SendingBuffer.append(None)
        self.ping = 0 #The current ping for the user
    def sendTrigger(self,funcName,*args): #Call a function on the client
        self.__buffer.append([["t"+funcName]+list(args)])
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
    def countTCPPackets(self): #Counts how many TCP packets there are
        num = 0
        for a in self.ReceiveBuffer:
            num += int(not a is None) #Count the packet if it contains a value and is not empty
        return num
    def receivedResend(self,ID): #Sends a specific packet back to the client
        if ID < len(self.SendingBuffer) and ID>=0: #This does not sync with tickrate
            if type(self.SendingBuffer[ID])==list: #Send the packet as a full list with the first index being the ID
                self.tsock.send(pickle.dumps([ID]+self.SendingBuffer[ID])) #Send missing packet
            else: #Send as a list containing the ID and the packet infomation
                self.tsock.send(pickle.dumps([ID,self.SendingBuffer[ID]])) #Send missing packet
    def requestResend(self,ID): #Request a client to resend a message
        self.tsock.send(pickle.dumps(["r",ID])) #Sends a message to the client to request a missed packet
        if not ID in self.resent: #Mark allredey exists
            self.resent.append(ID) #Mark packet ID as an expected receive ID
    def sendUDP(self,mes): #Add a UDP message to the buffer
        self.__buffer2.append(mes)
    def sendTCP(self,mes): #Add a TCP message to the buffer
        self.__buffer.append(mes)
    def loop(self): #Called continuesly
        if time.time()>self.__tickSend and len(self.updateSlow)==0: #Send the buffer to the user because its the users tick
            self.__tickSend = time.time()+(1/self.tick) #Reset the tick to next time
            if len(self.__buffer)!=0: #TCP messages
                sending = [self.__IDSend] #Packet to send to the client
                rem = [] #Data to remove from the buffer
                for a in self.__buffer: #Loop through the buffer and send only what we should fit in a packet.
                    if len(pickle.dumps(sending+[a]))<MAX_PACKET or len(sending)==0: #Can add the data without the packet going over a limit
                        rem.append(a) #Mark the data to be removed from the buffe
                        sending.append(a) #Add the a list, ready to be sent to the client
                    else: #Data limit has been hit
                        break
                for a in rem: #Removed the ones sending from the buffer, ready to be sent
                    self.__buffer.remove(a)
                self.tsock.send(pickle.dumps(sending)) #Send the packet
                self.SendingBuffer[self.__IDSend] = sending[1:] #Add the a buffer so the user can request this packet if it doesen't arrive
                self.__IDSend = (self.__IDSend + 1) % MAX_KEEP #Increase the ID for the next packet
            if len(self.__buffer2)!=0: #UDP messages
                sending = [] #Packet to send to client
                rem = [] #Data to remove from the buffer
                for a in self.__buffer2: #Loop through the buffer and send only what we should fit in a packet.
                    if len(pickle.dumps(sending+[a]))<MAX_PACKET or len(sending)==0: #Can add the data without the packet going over a limit
                        rem.append(a) #Mark the data to be removed from the buffe
                        sending.append(a) #Add the a list, ready to be sent to the client
                    else: #Data limit has been reached
                        break
                for a in rem: #Removed the ones sending from the buffer, ready to be sent
                    self.__buffer2.remove(a)
                self.tsock.send(pickle.dumps(sending)) #Send the packet
        elif len(self.updateSlow)!=0 and time.time()>self.updateSlowTimer: #This will be ran initialy to send the SYNC dictionary to the user
            self.updateSlowTimer = time.time()+SLOW_UPDATE_SPEED
            if type(self.updateSlow[0])==list: #Send the message as a list
                self.tsock.send(pickle.dumps([self.__IDSend]+self.updateSlow[0])) #Send the packet to the client
                self.SendingBuffer[self.__IDSend] = self.updateSlow.pop(0) #Add the a buffer so the user can request this packet if it doesen't arrive
                self.__IDSend = (self.__IDSend + 1) % MAX_KEEP #Increment the ID for the next message
            else:
                self.tsock.send(pickle.dumps([self.__IDSend, self.updateSlow[0]])) #Send the packet as a list
                self.SendingBuffer[self.__IDSend] = self.updateSlow.pop(0) #Add the a buffer so the user can request this packet if it doesen't arrive
                self.__IDSend = (self.__IDSend + 1) % MAX_KEEP #Increment the ID for the next message
            if len(self.updateSlow)==0: #End of updating SYNC
                self.__tickSend = time.time()+(1/self.tick)
                self.sendTCP("L") #Send a packet to tell the user the SYNC has ended
        if time.time()>self.__pingTime: #Ping the client
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
    def __init__(self,ip=socket.gethostbyname(socket.gethostname())):
        self.__ip = ip
        self.SYNC = {} #This contains a list of all the variables to synk with clients
        self.TRIGGER = {} #A dictionary of functions to be called by clients
        self.__SYNCBefore = {} #To detect changes in "SYNC"
        self.__frequent = [] #A list of frequently changes variables, use MAX_FREQUENT to increase size
        self.__UpdateFrequent = time.time()+FREQUENT_TIME #Time given to update all clients with frequently changed variables
        self.users = {} #A list of users connected
        #TCP socket
        self.__tsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #Set up a TCP socket
        self.__tsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
        self.__tsock.bind((self.__ip,TCP_port)) #Bind the TCP socket to an IP and port
        self.__tsock.listen(MAX_PLAYER)
        self.__tlist = [self.__tsock] #Socket list for the TCP socket

        print("Binded to "+self.__ip+" on port "+str(TCP_port))
    def __clientDisconnect(self,sock): #A client disconnected
        self.users.pop(sock.getpeername()[0])
        self.__tlist.remove(sock)
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
                if not path in self.__frequent and len(path)!=0 and not tcp: #Add the variable to a frequency list
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
        self.__tsock.close()
    def setVariable(self,lis,path,value): #Set a varable using a path list
        if len(path)==0:
            return None
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
    def doCommand(self,data,sock,tcpSent=False): #Called either from UDP or TCP connections. Their transmission data is the same format!
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
            elif data[0][0]=="t": #A trigger was sent to call a function
                if data[0][1:] in self.TRIGGER:
                    self.TRIGGER[data[0][1:]](*tuple([sock]+data[1:]))
    def receive(self,data,sock,tcpSent=False): #Processes a packet sent by a user
        if len(data)==0: #No data
            return False
        if data[0]=="r": #Resend a packet
            pname = sock.getpeername()[0] #Get the name for the client
            self.users[pname].receivedResend(data[1]) #Resend the packet to the user (without using tick-rate)
        else:
            for a in data:
                self.doCommand(a,sock,tcpSent)
    def loop(self): #Must be called continualy
        self.loopTCP() #Process all incoming packets
        self.detectAndApplySYNC() #Process all outgoing packets (due to variable changes)
        self.uploadFrequent() #Send frequently changed variables to all users over TCP
        for a in self.users: #Loop to process all user packet interaction (sending)
            self.users[a].loop()
            self.users[a].sender = False #User is no longer a sender (used to detect if the user was the one who changed a variable)
    def loopTCP(self): #This function must be called continuesly in order to update the TCP server
        read,write,err = select.select(self.__tlist,[],[],0) #Get all events to do with the socket
        for sock in read:
            if sock==self.__tsock: #A new connection has came in
                con,addr = self.__tsock.accept()
                self.__tlist.append(con)
                self.users[addr[0]] = Player(addr[0],con) #Add new player
                if len(self.SYNC)!=0: #Sent the SYNC list to the user
                    self.users[addr[0]].updateSlow = ["l"]+self.sensify(detectChanges({},self.SYNC),False) #Send the whole SYNC list to the user
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
                        else: #Is a normal message
                            pname = sock.getpeername()[0] #Sockets name
                            if type(data[0]) == int: #Message is linked with an ID (TCP)
                                if data[0]<MAX_KEEP and data[0]>=0: #Message is in bounds of the KEEP list
                                    shouldReceive = True #Is the packet valid and correct
                                    if data[0] in self.users[pname].resent: #Was the packet expected to be received
                                        self.users[pname].resent.remove(data[0]) #Don't expect any more
                                        self.users[pname].ignorePackets[data[0]] = data[1:] #Ingore duplicates of this packet with the ID
                                    elif data[0] in self.users[pname].ignorePackets: #Packet might be a duplicate
                                        if self.users[pname].ignorePackets[data[0]] != data[1:]: #Packet is different and valid, processing...
                                            self.users[pname].ignorePackets.pop(data[0]) #Remove from the ignore list
                                        else:
                                            shouldReceive = False #Packet is a duplicate, ignore!
                                    if shouldReceive:
                                        self.users[pname].ReceiveBuffer[data[0]] = data[1:] #Add to the users processing list
                                tCount = self.users[pname].countTCPPackets() #Count how many packets need processing
                                while not self.users[pname].ReceiveBuffer[self.users[pname].IDRec] is None: #Loop until the list gets to a null point
                                    self.receive(self.users[pname].ReceiveBuffer[self.users[pname].IDRec],sock,True)
                                    self.users[pname].ReceiveBuffer[self.users[pname].IDRec] = None
                                    self.users[pname].IDRec = (self.users[pname].IDRec + 1) % MAX_KEEP
                                if self.users[pname].countTCPPackets()!=0: #Is there packets still awaiting to be sent
                                    self.users[pname].requestResend(self.users[pname].IDRec) #Request the client to send the packet again
                            else: #Message is UDP
                                self.users[pname].sender = True
                                self.receive(data,sock) #Receive normal

def enError(err):
    print("Error, ",err)

def ERROR(*info): #This function is called whenever an unexspected error occures. It is mainly so it can be displayed on the screen without the game crashing
    print("Err: ",info) #Tempory
    if LINK["DEV"]: #If in development mode then exit the game
        pygame.quit()
        sys.exit(1)
def ADDLOG(mes): #Used to show logs (used for console)
    print(mes)
class NULLENT(base.Main): #Null entity for keeping the game running when an entity doesen't exist
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK)
        self.ID = ID
        self.settings = {}
        self.pos = [x,y]
        self.size = [50,50]
        self.LINK = LINK
        self.HINT = True
    def editMove(*args):
        pass
    def SaveFile(self):
        return []
    def loop(self,lag):
        pass
    def rightInit(self,surf):
        self.__surface = pygame.Surface((50,50))
        self.__lastRenderPos = [0,0]
    def rightLoop(self,mouse,kBuf):
        pass
    def rightUnload(self):
        self.__surface = None
        self.__lastRenderPos = None
    def rightRender(self):
        pass
    def sRender(self,x,y,scale,surf=None,edit=False):
        self.renderHint(surf,"Null entity, please remove.",[x,y])
def loadLINK(): #Loads all content
    LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
    LINK["errorDisplay"] = ERROR #Used to show errors
    LINK["reslution"] = [1000,700] #Reslution of the game
    LINK["DEV"] = True #Development mode, this will stop the game when errors occur.
    LINK["render"] = render #Used so other scripts can use its tools for rendering
    LINK["log"] = ADDLOG #Used to log infomation (not seen in game unless developer console is turned on)
    LINK["mesh"] = {} #Used for fast entity discovery
    #Screens
    files = os.listdir("screens")
    LINK["screens"] = {}
    for a in files:
        if a[-3:]==".py":
            LINK["screens"][a[:-3]] = importlib.import_module("screens."+a[:-3])
    #Entities
    files = os.listdir("entities")
    LINK["ents"] = {}
    for a in files:
        if a[-3:]==".py":
            LINK["ents"][a[:-3]] = importlib.import_module("entities."+a[:-3])
    #Upgrades
    files = os.listdir("upgrades")
    LINK["upgrade"] = {} #Drone upgrades
    LINK["shipUp"] = {} #Ship upgrades
    for a in files:
        if a[-3:]==".py":
            itm = importlib.import_module("upgrades."+a[:-3])
            if a=="base.py":
                LINK["upgrade"][a[:-3]] = itm
            elif itm.Main(LINK).droneUpgrade:
                LINK["upgrade"][a[:-3]] = itm
            else:
                LINK["shipUp"][a[:-3]] = itm
    LINK["null"] = NULLENT
    LINK["drones"] = [] #Drone list of the players drones
    for i in range(0,3):
        LINK["drones"].append(LINK["ents"]["drone"].Main(i*60,0,LINK,-2-i))
    LINK["shipEnt"] = LINK["ents"]["ship"].Main(0,0,LINK,-1)
    LINK["multi"] = 2 #Running as server
    return LINK

class GameServer:
    def __init__(self,IP):
        print("Loading...")
        self.serv = Server(IP) #Make the server
        self.LINK = loadLINK() #Initialize LINK
        self.LINK["serv"] = self.serv
        DEFMAP = "Testing map.map" #Map to load (tempory)
        self.mapName = DEFMAP
        self.world = self.LINK["screens"]["game"].GameEventHandle(self.LINK) #The game world to simulate
        self.world.open(DEFMAP) #Open the map in the world
        self.serv.SYNC["P"] = {} #Players
        self.serv.SYNC["M"] = {} #Map
        self.serv.SYNC["M"]["h"] = self.LINK["screens"]["game"].getMapMash(DEFMAP) #Map hash
        self.serv.SYNC["M"]["n"] = DEFMAP #Map name
        self.RAW_MAP = [] #Raw map file lines (used for user downloading)
        with open("maps/"+DEFMAP,"rb") as file: #Open the map for sending to users
            self.RAW_MAP = pickle.loads(file.read())
        self.serv.TRIGGER["dwnl"] = self.downloadMap #Function to call when a user requests to download a map
        self.__MAP_DOWNLOAD = {} #Users who are downloading the map
        self.__DOWNLOAD_TICK = time.time()+SLOW_UPDATE_SPEED #Used to track how fast to call the event loop on map downloading
        print("Done, entering event loop, map mash is "+str(self.serv.SYNC["M"]["h"]))
    def getAllMapEnts(self): #Retruns all map entities (used for late downloading)
        res = [self.RAW_MAP[0]+0]
        for a in self.world.Map:
            res.append(a.SaveFile())
        return res
    def loop(self): #Game loop
        self.world.loop() #Simulate world events
        self.serv.loop() #Deal with server events and variable changes in SYNC
        if time.time()>self.__DOWNLOAD_TICK: #Should run the donwloading loop
            self.__DOWNLOAD_TICK = time.time()+SLOW_UPDATE_SPEED
            self.__downloadMapLoop()
    def __downloadMapLoop(self): #Used for sending maps to clients
        rem = [] #User downloads that have finished
        for i in self.__MAP_DOWNLOAD: #Go through every user downloading a map
            a = self.__MAP_DOWNLOAD[i]
            if a>=len(self.RAW_MAP): #Has the map finished downloading for the specific client
                self.serv.users[i].sendTrigger("dsnd",self.mapName) #Send the maps name to save
                rem.append(i) #Add to the removing list
            else: #Continue sending parts of the map
                self.serv.users[i].sendTrigger("dsnd",self.RAW_MAP[a]) #Sent a single entity
                self.__MAP_DOWNLOAD[i] = a+1 #Increase variable for next entity
        for a in rem: #Remove finished clients
            self.__MAP_DOWNLOAD.pop(a)
    def downloadMap(self,UserSock): #Sends the current map to the specific user
        if not UserSock.getpeername()[0] in self.__MAP_DOWNLOAD: #Checking if the user isn't trying to request the map more than once
            self.__MAP_DOWNLOAD[UserSock.getpeername()[0]] = 0 #Begin sending the map

if __name__=="__main__": #If not imported the run as a server without a game running in the background.
    ERROR = enError
    IP = socket.gethostbyname(socket.gethostname())
    #IP = "169.254.178.71"
    Game = GameServer(IP)
    while True:
        Game.loop()
