import socket,select,pickle,time,render, os, importlib, sys, traceback,mapGenerator
import entities.base as base

VERSION = 0.3 #Version number, used so clients with incorrect versions cannot connect

TCP_port = 3746 #Port for serious data transfer, e.g. chat messages
TCP_BUF_SIZE = 4046 #Receiving buffer size
MAX_PLAYER = 60
PING_INTERVAL = 5 #Seconds to send a ping interval again
SLOW_UPDATE_SPEED = 0.1 #0.25 #Seconds between sending a slow update packet, (initaly syncing variables when joining a server or changing map) TCP connection.
MAX_FREQUENT = 12 #Max number of variables allowed in the frequently changed list, increasing may resolve sync issues but would also slow network down
FREQUENT_TIME = 4 #Seconds to update all users with frequently changed variables
ERROR = None #Function to call when an error happens
MAX_KEEP = 60 # Maximum packets to keep for users to access if missed, the higher this the more memory used and possibly a user could request a packet from a while ago.
MAX_PACKET = 200 #Maximum size of one packet sent to a user
WORLD_UPDATE_TICK = 0.05 #Time to wait until updating the world again

def nameIP(IP): #Turns an IP into hexadecimal charicters
    res = ""
    spl = IP.split(".")
    for a in spl:
        if int(a)<16:
            res+="0"
        res+=hex(int(a))[2:]
    return res

class Player: #Class used to store a player
    def __init__(self,ip,sock):
        self.ip = ip #IP of the player
        self.ip2 = nameIP(ip)
        self.tsock = sock #Socket for the player/client
        self.tick = 22 #Default
        self.name = ip+"" #Name of the player
        self.sender = False #Is the source of a changed variable
        self.updateSlow = [] #Packets to send slowly to the user (This will be populated when the user first joins or the map is changed)
        self.updateSlowTimer = time.time() #Used for sending SYNC completely
        self.minTick = 10 #Minimum tick that tick can be lowered too
        self.maxTick = 25 #Maximum tick that tick can be highered too
        self.tempIgnore = [] #Used by other entities to ignore one change in a variable (probebly because it synced it over TCP)
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
    def getIDSend(self): #Returns the value of IDSend, used for debugging
        return self.__IDSend +0
    def getBufs(self): #Returns the value of the lengths of both buffers for debugging
        return len(self.__buffer),len(self.__buffer2)
    def sendTrigger(self,funcName,*args): #Call a function on the client
        self.__buffer.append([["t"+funcName]+list(args)])
    def receivedPing(self): #Called when the user sent a message back because of a ping
        if self.__pingBefore!=-1:
            SEND = (time.time()-self.__pingBefore)/2
            if not SEND==0:
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
        Fail = False
        if time.time()>self.__tickSend and len(self.updateSlow)==0: #Send the buffer to the user because its the users tick
            self.__tickSend = time.time()+(1/self.tick) #Reset the tick to next time
            if len(self.__buffer)!=0: #TCP messages
                sending = [self.__IDSend] #Packet to send to the client
                rem = [] #Data to remove from the buffer
                for a in self.__buffer: #Loop through the buffer and send only what we should fit in a packet.
                    if len(pickle.dumps(sending+[a]))<MAX_PACKET or len(sending)==1: #Can add the data without the packet going over a limit
                        rem.append(a) #Mark the data to be removed from the buffe
                        sending.append(a) #Add the a list, ready to be sent to the client
                        if type(a)==str:
                            break
                    else: #Data limit has been hit
                        break
                for a in rem: #Removed the ones sending from the buffer, ready to be sent
                    self.__buffer.remove(a)
                try:
                    self.tsock.send(pickle.dumps(sending)) #Send the packet
                except:
                    Fail = True
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
                try:
                    self.tsock.send(pickle.dumps(sending)) #Send the packet
                except:
                    Fail = True
        elif len(self.updateSlow)!=0 and time.time()>self.updateSlowTimer: #This will be ran initialy to send the SYNC dictionary to the user
            self.updateSlowTimer = time.time()+SLOW_UPDATE_SPEED
            if type(self.updateSlow[0])==list: #Send the message as a list
                try:
                    self.tsock.send(pickle.dumps([self.__IDSend]+self.updateSlow[0])) #Send the packet to the client
                except:
                    Fail = True
                self.SendingBuffer[self.__IDSend] = self.updateSlow.pop(0) #Add the a buffer so the user can request this packet if it doesen't arrive
                self.__IDSend = (self.__IDSend + 1) % MAX_KEEP #Increment the ID for the next message
            else:
                try:
                    self.tsock.send(pickle.dumps([self.__IDSend, self.updateSlow[0]])) #Send the packet as a list
                except:
                    Fail = True
                self.SendingBuffer[self.__IDSend] = self.updateSlow.pop(0) #Add the a buffer so the user can request this packet if it doesen't arrive
                self.__IDSend = (self.__IDSend + 1) % MAX_KEEP #Increment the ID for the next message
            if len(self.updateSlow)==0: #End of updating SYNC
                self.__tickSend = time.time()+(1/self.tick)
                self.__buffer.insert(0,"L") #Send a packet to tell the user the SYNC has ended
        if time.time()>self.__pingTime: #Ping the client
            self.__pingTime = time.time()+PING_INTERVAL
            self.__pingBefore = time.time()
            try:
                self.tsock.send(pickle.dumps("p"))
            except:
                Fail = True
        return Fail

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
        self.newUser = None #Function to call if a new user joins the server
        self.closeUser = None #Function to call if a user disconnects

        print("Binded to "+self.__ip+" on port "+str(TCP_port))
    def __clientDisconnect(self,sock): #A client disconnected
        try: #Try to get the users address so that we can remove them from the player list
            sIP = sock.getpeername()[0]
        except OSError: #Try to find their address by finding their socket in the player list using brute force
            sIP = None
            for a in self.users:
                if self.users[a].tsock == sock:
                    sIP = self.users[a].ip
                    break
        if not sIP is None: #Disconnecting user
            self.closeUser(sIP) #Call the function to deal with user disconnects
            self.users[sIP].tsock.close()
            self.users.pop(sIP)
            self.__tlist.remove(sock)
    def reset(self): #Reset sync variables
        self.__SYNCBefore = {}
        self.SYNC = {}
        for a in self.users:
            self.SYNC[self.users[a].ip2] = {"N":self.users[a].name}
            self.__SYNCBefore[self.users[a].ip2] = {"N":self.users[a].name}
    def getValue(self,path,currentList): #Returns the value at the specified path (path is a list)
        if type(currentList[path[0]])==dict and len(path)!=1:
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
                if tcp: #Is a TCP variable
                    for c in self.users: #Send the TCP data to every player in the game
                        if not self.users[c].sender:
                            self.users[c].sendTCP(a)
                else: #Is a UDP variable
                    for c in self.users: #Send the UDP data to every player in the game
                        if not self.users[c].sender and not path in self.users[c].tempIgnore: #Is not the sender and variable shouln't be ignored
                            self.users[c].sendUDP(a)
            for a in self.users: #Reset variable ignores
                self.users[a].tempIgnore = []
            self.__SYNCBefore = varInitial(self.SYNC) #Apply the changes so further changes in SYNC can be detected.
    def uploadFrequent(self): #Sends frequently changed variables full value to all players if timer has expired
        if time.time()>self.__UpdateFrequent:
            self.__UpdateFrequent = time.time()+FREQUENT_TIME
            msg = []
            rem = [] #Remove invalid variables
            for a in self.__frequent:
                try:
                    msg.append(["s",self.getValue(a,self.SYNC)]+a)
                except KeyError: #Variable probebly doesen't exist anymore
                    rem.append(a)
                except:
                    ERROR("Error occured when getting value in LINK, variable info:",a,"error:",traceback.format_exc())
                    rem.append(a)
            for a in rem:
                self.__frequent.remove(a)
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
        if type(lis[path[0]])==dict and len(path)!=1:
            self.setVariable(lis[path[0]],path[1:],value)
        else:
            lis[path[0]] = value
    def deleteVariable(self,lis,path): #Delete a variable using a path list
        if not path[0] in lis:
            if len(path)!=1:
                lis[path[0]] = {}
        if type(lis[path[0]])==dict and len(path)!=1:
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
                try:
                    self.doCommand(a,sock,tcpSent)
                except:
                    print("FAIL PACKET ",a,"info:")
                    traceback.print_exc()
                    print("################ END ################")
    def loop(self): #Must be called continualy
        self.loopTCP() #Process all incoming packets
        self.detectAndApplySYNC() #Process all outgoing packets (due to variable changes)
        self.uploadFrequent() #Send frequently changed variables to all users over TCP
        rem = []
        for a in self.users: #Loop to process all user packet interaction (sending)
            try: #Try to do an event loop on the user
                if self.users[a].loop():
                    self.users[a].tsock.close()
                    rem.append(a)
            except BrokenPipeError: #Socket must be broken, disconect user
                self.users[a].tsock.close()
                rem.append(a)
            self.users[a].sender = False #User is no longer a sender (used to detect if the user was the one who changed a variable)
            if self.users[a].ip2 in self.SYNC:
                self.users[a].name = self.SYNC[self.users[a].ip2]["N"]
        for a in rem: #Users to remove since they had broken sockets
            self.closeUser(self.users[a].ip) #Call the function to deal with user disconnects
            self.__tlist.remove(self.users[a].tsock)
            self.users.pop(a)
    def loopTCP(self): #This function must be called continuesly in order to update the TCP server
        read,write,err = select.select(self.__tlist,[],[],0) #Get all events to do with the socket
        for sock in read:
            if sock==self.__tsock: #A new connection has came in
                con,addr = self.__tsock.accept()
                self.__tlist.append(con)
                self.users[addr[0]] = Player(addr[0],con) #Add new player
                self.SYNC[nameIP(addr[0])]={"N": addr[0]}
                if len(self.SYNC)!=0: #Sent the SYNC list to the user
                    self.users[addr[0]].updateSlow = ["l"]+self.sensify(detectChanges({},self.SYNC),False) #Send the whole SYNC list to the user
                    self.users[addr[0]].updateSlow[0] = "l"+str(len(self.users[addr[0]].updateSlow)-1) #For loading bar on users
                if not self.newUser is None:
                    self.newUser(addr[0])
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

def enError(*err):
    print("Error:")
    for a in err:
        print("\t",a)
    print()

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
def loadLINK(serv): #Loads all content
    LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
    LINK["errorDisplay"] = ERROR #Used to show errors
    LINK["serv"] = serv
    LINK["reslution"] = [1000,700] #Reslution of the game
    LINK["DEV"] = False #Development mode, this will stop the game when errors occur.
    LINK["allPower"] = False #Cheat to enable power to all doors, used for development
    LINK["render"] = render #Used so other scripts can use its tools for rendering
    LINK["log"] = ADDLOG #Used to log infomation (not seen in game unless developer console is turned on)
    LINK["mesh"] = {} #Used for fast entity discovery
    LINK["hints"] = False
    LINK["hintDone"] = []
    LINK["upgradeIDCount"] = 0 #Upgrade ID Count
    LINK["scrapCollected"] = 0 #Amount of scrap colected
    LINK["fuelCollected"] = 0 #Amount of fuel colected
    LINK["NPCignorePlayer"] = False #Used for development
    LINK["floorScrap"] = False #Enable/disable floor scrap
    LINK["absoluteDoorSync"] = False #Send packets randomly to make doors in SYNC perfectly (bigger the map the more packets)
    LINK["particles"] = False #Disable particle effects on server
    LINK["simpleModels"] = True #Simple models
    LINK["showRooms"] = False
    LINK["backgroundStatic"] = False #Enable/disable background static
    LINK["viewDistort"] = False #Drone view distortion
    LINK["names"] = ["Jeff","Tom","Nathon","Harry","Ben","Fred","Timmy","Potter","Stranger"] #Drone names
    LINK["shipNames"] = ["Franks","Daron","Hassle","SETT","BENZYA"] #Ship names
    LINK["shipData"] = {"fuel":5,"scrap":5,"shipUpgs":[],"maxShipUpgs":2,"reserveUpgs":[],"reserveMax":8,"invent":[],
        "beforeMap":-1,"mapSaves":[],"maxScore":0,"reserve":[],"maxDrones":4,"maxReserve":2,"maxInvent":70} #Data about the players ship
    LINK["multi"] = 2 #Running as server
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
            elif itm.Main(LINK,-1).droneUpgrade:
                LINK["upgrade"][a[:-3]] = itm
            else:
                LINK["shipUp"][a[:-3]] = itm
    LINK["null"] = NULLENT
    LINK["drones"] = [] #Drone list of the players drones
    for i in range(0,4):
        LINK["drones"].append(LINK["ents"]["drone"].Main(i*60,0,LINK,-2-i,i+1))
    LINK["drones"][0].settings["upgrades"][0] = ["gather",0,-1]
    LINK["drones"][0].settings["upgrades"][1] = ["motion",0,-1]
    LINK["drones"][1].settings["upgrades"][0] = ["generator",0,-1]
    LINK["drones"][2].settings["upgrades"][0] = ["interface",0,-1]
    LINK["drones"][2].settings["upgrades"][1] = ["tow",0,-1]
    LINK["drones"][0].loadUpgrades() #Tempory
    LINK["drones"][1].loadUpgrades() #Tempory
    LINK["drones"][2].loadUpgrades() #Tempory
    
    LINK["shipEnt"] = LINK["ents"]["ship"].Main(0,0,LINK,-1)
    LINK["shipEnt"].settings["upgrades"][0] = ["remote power",0,-1]
    
    #LINK["shipEnt"].settings["upgrades"][1] = ["surveyor",1,-1]
    LINK["shipEnt"].loadUpgrades()
    return LINK

class GameServer:
    def __init__(self,IP):
        print("Loading...")
        self.serv = Server(IP) #Make the server
        self.LINK = loadLINK(self.serv) #Initialize LINK
        self.LINK["serv"] = self.serv
        self.LINK["serv"].newUser = self.userJoin
        self.LINK["serv"].closeUser = self.userLeave
        self.LINK["serv"].TRIGGER["com"] = self.doCommand #Execute a command
        self.LINK["serv"].TRIGGER["mvu"] = self.__moveUpgrade #Move an upgade from one drone to anouther
        self.LINK["serv"].TRIGGER["sup"] = self.__swapUpgrade #Swap two upgrades in a drone, (used instead of two "self.__moveUpgrade" calls)
        self.LINK["serv"].TRIGGER["sls"] = self.__selectShip #Select a ship to dock to
        #DEFMAP = "ServGen.map" #Map to load (tempory)
        #mapGenerator.MapGenerator(self.LINK,7,"ServGen.map")
        self.mapName = ""
        if self.LINK["DEV"]:
            self.__rend = render.DebugServer(self.LINK)
        self.shipSelect = True #Is the server inside a ship selecting screen
        self.gameOver = False #Is the game over?
        self.world = None
        #self.world = self.LINK["screens"]["game"].GameEventHandle(self.LINK) #The game world to simulate
        #self.world.open(DEFMAP) #Open the map in the world
        self.LINK["world"] = self.world
        self.serv.SYNC["V"] = VERSION #Server version
        self.serv.SYNC["P"] = {} #Players
        #self.serv.SYNC["M"] = {} #Map
        self.serv.SYNC["SS"] = True #Inside ship selecting screen
        #self.serv.SYNC["M"]["h"] = self.LINK["screens"]["game"].getMapMash(DEFMAP) #Map hash
        #self.serv.SYNC["M"]["n"] = DEFMAP #Map name
        self.LINK["outputCommand"] = self.putLine
        self.LINK["Broadcast"] = self.broadCast
        self.__updateTime = time.time()
        self.startShipSelectingScreen()
        print("Done, entering event loop")
    def __selectShip(self,sock,ship): #Select a ship in the ship selecting screen
        if self.shipSelect:
            self.world.selectShip(ship)
            self.resetSync()
            self.startNewGame("ShipSelect"+str(ship))
    def __moveUpgrade(self,sock,drone1ID,drone2ID,index):
        #Index 0 should allways be a "swap.py" upgrade
        #Move the upgrade server-side
        DRONE = self.LINK["IDs"][drone1ID]
        DRONE.PERM_UPG[0].moveTo(DRONE.upgrades.pop(index),self.LINK["IDs"][drone2ID])
        self.broadCast("cupg",drone1ID,"swap",drone2ID,index) #Send a trigger to all players that a drone upgrade has moved
    def __swapUpgrade(self,sock,drone1ID,drone2ID,leftIndex,rightIndex):
        #Swap the upgrades server-side
        DRONE_1 = self.LINK["IDs"][drone1ID]
        DRONE_2 = self.LINK["IDs"][drone2ID]
        upg = DRONE_1.upgrades.pop(leftIndex)
        DRONE_2.PERM_UPG[0].moveTo(DRONE_2.upgrades.pop(rightIndex),DRONE_1,leftIndex)
        DRONE_1.PERM_UPG[0].moveTo(upg,DRONE_2,rightIndex)
        self.broadCast("cupg",drone1ID,"swap",drone2ID,leftIndex,rightIndex) #Send a trigger to all players that two drone upgrades where swapped
    def broadCast(self,fname,*args): #Broadcasts a message to all clients connected
        for a in self.LINK["serv"].users:
            self.LINK["serv"].users[a].sendTrigger(fname,*args)
    def putLine(self,tex,col,flash,Tab=None): #Add a line to the command line from an entity
        if Tab is None: #Global
            TB = -2
        elif type(Tab) != int: #A specific drone tab
            TB = self.world.drones.index(Tab)
        else:
            TB = Tab
        self.broadCast("com","",TB,flash,[tex,col])
    def resetSync(self): #Resets the syncing variables
        self.serv.reset()
        self.serv.SYNC["V"] = VERSION
        self.serv.SYNC["SS"] = self.shipSelect
        self.LINK["mesh"] = {}
        #rem = []
        #for a in self.serv.SYNC:
        #    if a[0]=="e" and not "-" in a:
        #        rem.append(a)
        #for a in rem:
        #    self.serv.SYNC.pop(a)
    def startNewGame(self,mapName): #Load the game into a world
        #mapGenerator.MapGenerator(self.LINK,7,"ServGen.map")
        #self.LINK = None
        #self.serv.reset()
        #self.LINK = loadLINK(self.serv)
        #self.LINK["serv"] = self.serv
        #self.LINK["serv"].newUser = self.userJoin
        #self.LINK["serv"].closeUser = self.userLeave
        #self.LINK["serv"].TRIGGER["com"] = self.doCommand #Execute a command
        #self.LINK["serv"].TRIGGER["mvu"] = self.__moveUpgrade #Move an upgade from one drone to anouther
        #self.LINK["serv"].TRIGGER["sup"] = self.__swapUpgrade #Swap two upgrades in a drone, (used instead of two "self.__moveUpgrade" calls)
        #self.serv.SYNC["V"] = VERSION #Server version
        self.resetSync()
        self.serv.SYNC["M"] = {} #Map
        self.serv.SYNC["SS"] = False
        self.shipSelect = False
        #self.serv.SYNC["M"]["h"] = self.LINK["screens"]["game"].getMapMash("ServGen.map") #Map hash
        #self.serv.SYNC["M"]["n"] = "ServGen.map" #Map name
        self.world = self.LINK["screens"]["game"].GameEventHandle(self.LINK) #The game world to simulate
        self.world.open(mapName) #Open the map in the world
        self.world.loop()
        self.LINK["world"] = self.world
        #self.broadCast("lda","game")
        self.__causeLoadingToAll()
        for a in self.serv.users:
            self.serv.users[a].updateSlow.insert(1,["tlda","game"])
        mapEnts = self.getAllMapEnts()
        for usr in self.LINK["serv"].users:
            for a in mapEnts:
                self.LINK["serv"].users[usr].updateSlow.append(["tdsnd",a])
            self.serv.users[usr].updateSlow[0] = "l"+str(len(self.serv.users[usr].updateSlow)-1) #For loading bar on users
            self.LINK["serv"].users[usr].updateSlow.append(["tsetn",self.LINK["serv"].users[usr].name])
    def startShipSelectingScreen(self):
        self.shipSelect = True
        self.resetSync()
        self.world = self.LINK["screens"]["shipSelect"].Main(self.LINK)
        self.LINK["world"] = self.world
        if self.world.failed[0]: #Game is over
            self.gameOver = True
            return None
        for i,a in enumerate(self.world.maps):
            self.serv.SYNC["S"+str(i)] = {}
            self.serv.SYNC["S"+str(i)]["N"] = a[3] #Ship name
            self.serv.SYNC["S"+str(i)]["S"] = a[1] #Scrap capasity
            self.serv.SYNC["S"+str(i)]["T"] = a[4] #Threat types
            self.serv.SYNC["S"+str(i)]["D"] = a[5] #Distance/fuel
            self.serv.SYNC["S"+str(i)]["A"] = a[2] #Age
        self.serv.SYNC["MD"] = self.LINK["shipData"]["maxDrones"]+0 #Max drones
        self.serv.SYNC["MR"] = self.LINK["shipData"]["maxReserve"]+0 #Max reserved drones
        self.serv.SYNC["MS"] = self.LINK["shipData"]["maxShipUpgs"]+0 #Maximum ship upgrades
        self.serv.SYNC["MSS"] = self.LINK["shipData"]["reserveMax"]+0 #Maximum reserved ship upgrades
        self.serv.SYNC["MI"] = self.LINK["shipData"]["maxInvent"]+0 #Max inventory size
        self.serv.SYNC["DC"] = len(self.LINK["drones"])
        self.serv.SYNC["UC"] = len(self.LINK["shipData"]["shipUpgs"])
        for i in range(0,self.LINK["shipData"]["maxDrones"]+self.LINK["shipData"]["maxReserve"]):
            self.serv.SYNC["D"+str(i)] = {}
            a = None
            if i<self.LINK["shipData"]["maxDrones"] and i<len(self.LINK["drones"]):
                a = self.LINK["drones"][i]
                self.LINK["drones"][i].GID = i+0 #Give this drone a reference back to its SYNCs
            elif i-self.LINK["shipData"]["maxDrones"]<len(self.LINK["shipData"]["reserve"]) and i-self.LINK["shipData"]["maxDrones"]>=0:
                a = self.LINK["shipData"]["reserve"][i-self.LINK["shipData"]["maxDrones"]]
                self.LINK["shipData"]["reserve"][i-self.LINK["shipData"]["maxDrones"]].GID = i+0 #Give this drone a reference back to its SYNCs
            if a is None: #Drone doesen't exist
                self.serv.SYNC["D"+str(i)]["E"] = False
            else: #Drone exists
                self.serv.SYNC["D"+str(i)]["E"] = True
                self.serv.SYNC["D"+str(i)]["N"] = a.settings["name"]
                self.serv.SYNC["D"+str(i)]["H"] = a.health
                self.serv.SYNC["D"+str(i)]["HM"] = a.settings["maxHealth"]
                self.serv.SYNC["D"+str(i)]["A"] = a.alive
                self.serv.SYNC["D"+str(i)]["O"] = i+0 #Drone order
                self.serv.SYNC["D"+str(i)]["US"] = len(a.settings["upgrades"]) #Drone upgrade amount
                for i2,b in enumerate(a.settings["upgrades"]): #Sync all the drones upgrades
                    if b[0]=="":
                        self.serv.SYNC["D"+str(i)]["U"+str(i2)] = ""
                    else:
                        if len(b)==5:
                            if len(b[4])!=0:
                                self.serv.SYNC["D"+str(i)]["U"+str(i2)] = b[0]+","+str(b[1])+","+str(b[4][0])
                            else:
                                self.serv.SYNC["D"+str(i)]["U"+str(i2)] = b[0]+","+str(b[1])
                        else:
                            self.serv.SYNC["D"+str(i)]["U"+str(i2)] = b[0]+","+str(b[1])
        for i in range(0,self.LINK["shipData"]["maxInvent"]): #Sync all inventory upgrades
            self.serv.SYNC["U"+str(i)] = {}
            if i<len(self.LINK["shipData"]["invent"]): #Upgrade exists
                self.serv.SYNC["U"+str(i)]["E"] = True
                A = self.LINK["shipData"]["invent"][i]
                self.serv.SYNC["U"+str(i)]["N"] = A[0]
                self.serv.SYNC["U"+str(i)]["D"] = A[1]
                if i+1<len(self.LINK["shipData"]["invent"]):
                    self.serv.SYNC["U"+str(i)]["P"] = i+1 #Point to the next upgrade
                else:
                    self.serv.SYNC["U"+str(i)]["P"] = -1 #Set pointer as end
            else:
                self.serv.SYNC["U"+str(i)]["E"] = False
                self.serv.SYNC["U"+str(i)]["N"] = "Empty"
                self.serv.SYNC["U"+str(i)]["D"] = 0
                self.serv.SYNC["U"+str(i)]["P"] = -1 #Doesen't point to anything
        for i in range(0,self.LINK["shipData"]["maxShipUpgs"]+self.LINK["shipData"]["reserveMax"]):
            self.serv.SYNC["G"+str(i)] = {}
            self.serv.SYNC["G"+str(i)]["E"] = False
            self.serv.SYNC["G"+str(i)]["P"] = i+0
            UPG = None
            if i>=self.LINK["shipData"]["maxShipUpgs"]: #Reserved ship upgrade
                if i-self.LINK["shipData"]["maxShipUpgs"]<len(self.LINK["shipData"]["reserveUpgs"]):
                    self.serv.SYNC["G"+str(i)]["E"] = True
                    self.serv.SYNC["G"+str(i)]["N"] = self.LINK["shipData"]["reserveUpgs"][i-self.LINK["shipData"]["maxShipUpgs"]][0]
                    self.serv.SYNC["G"+str(i)]["D"] = self.LINK["shipData"]["reserveUpgs"][i-self.LINK["shipData"]["maxShipUpgs"]][1]+0
                    self.serv.SYNC["G"+str(i)]["I"] = self.LINK["shipData"]["reserveUpgs"][i-self.LINK["shipData"]["maxShipUpgs"]][2]+0
            else: #Ship upgrade
                if i<len(self.LINK["shipData"]["shipUpgs"]):
                    self.serv.SYNC["G"+str(i)]["E"] = True
                    self.serv.SYNC["G"+str(i)]["N"] = self.LINK["shipData"]["shipUpgs"][i][0]
                    self.serv.SYNC["G"+str(i)]["D"] = self.LINK["shipData"]["shipUpgs"][i][1]+0
                    self.serv.SYNC["G"+str(i)]["I"] = self.LINK["shipData"]["shipUpgs"][i][2]+0
        self.__causeLoadingToAll()
    def __causeLoadingToAll(self): #Loads varaibles into all clients
        for a in self.serv.users:
            self.serv.users[a].updateSlow = ["l"]+self.serv.sensify(detectChanges({},self.serv.SYNC),False) #Send the whole SYNC list to the user
            self.serv.users[a].updateSlow[0] = "l"+str(len(self.serv.users[a].updateSlow)-1) #For loading bar on users
    def doCommand(self,sock,command,drone): #Called when a user enteres a command into their command line
        pName = sock.getpeername()[0]
        usr = self.LINK["serv"].users[pName]
        tex,col = self.world.doCommand(command,drone,usr) #Process the command
        if tex=="": #Broadcast what the user typed
            self.broadCast("com",usr.name+">"+command,drone,False)
        elif tex!="NOMES": #Broadcast what the user typed and what the outcome of the command was
            self.broadCast("com",usr.name+">"+command,drone,False,[tex,col])
    def userLeave(self,addr): #A user has left
        print("Connection closed ",addr)
        self.broadCast("com","User "+addr+" left",-2,False,(255,153,0)) #Broadcast that the user left
        file = open("LOG.txt","a")
        file.write("User left "+addr+"\n")
        file.close()
    def userJoin(self,addr): #A new user has joined
        if self.shipSelect:
            pass
        else:
            mapEnts = self.getAllMapEnts()
            for a in mapEnts:
                self.LINK["serv"].users[addr].updateSlow.append(["tdsnd",a])
            self.broadCast("com","User "+addr+" joined",-2,False,(255,153,0)) #Broadcast that the user joined
        self.LINK["serv"].users[addr].updateSlow[0] = "l"+str(len(self.LINK["serv"].users[addr].updateSlow)) #For loading bar on users
        self.LINK["serv"].users[addr].updateSlow.insert(0,["tpls",len(self.LINK["serv"].users)-1]) #Send player count
        FL = -1
        if self.shipSelect:
            if self.world.failed[0]:
                FL = self.world.failed[1]
        self.LINK["serv"].users[addr].updateSlow.insert(1,["tsss",self.shipSelect,FL]) #Send player count
        print("New connection "+addr)
        file = open("LOG.txt","a")
        file.write("New user connected "+addr+"\n")
        file.close()
    def getAllMapEnts(self): #Retruns all map entities (used for late downloading)
        res = [0]
        for a in self.world.Map:
            sD = a.SaveFile()
            if sD[1]>res[0]:
                res[0] = sD[1]+0
            res.append(sD)
        return res
    def loop(self): #Game loop
        if self.shipSelect: #In ship selecting screen
            pass
        else: #Inside game
            if time.time()>self.__updateTime: #Only update the world a certain amounts of times in a second
                self.__updateTime = time.time()+WORLD_UPDATE_TICK
                try:
                    self.world.loop() #Simulate world events
                except:
                    print("Failed to run world loop within server")
                    traceback.print_exc()
                try:
                    for a in self.world.drones:
                        a.discoverAround()
                except:
                    print("Discovering failed on drones")
                    traceback.print_exc()
            if self.world.exit:
                SCR = self.world.getScore()
                INF = self.world.safeExit()
                self.startShipSelectingScreen()
                if self.gameOver:
                    for a in self.LINK["serv"].users:
                        self.serv.users[a].updateSlow.insert(1,["tlda","death",self.world.failed[1]])
                else:
                    for a in self.LINK["serv"].users:
                        self.serv.users[a].updateSlow.insert(1,["tlda","shipSelect"])
                        self.serv.users[a].updateSlow.insert(2,["tdinf",INF,SCR])
        self.serv.loop() #Deal with server events and variable changes in SYNC
        if self.LINK["DEV"]:
            try:
                self.__rend.render(self.world.Map)
            except:
                print("Failed to render dev window")
                traceback.print_exc()
    def downloadMap(self,UserSock): #Sends the current map to the specific user
        if not UserSock.getpeername()[0] in self.__MAP_DOWNLOAD: #Checking if the user isn't trying to request the map more than once
            self.__MAP_DOWNLOAD[UserSock.getpeername()[0]] = 0 #Begin sending the map

if __name__=="__main__": #If not imported the run as a server without a game running in the background.
    ERROR = enError
    IP = socket.gethostbyname(socket.gethostname())
    IP = "127.0.1.1"
    Game = GameServer(IP)
    while True:
        Game.loop()
