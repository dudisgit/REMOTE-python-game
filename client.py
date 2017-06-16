import socket,select,pickle
from tkinter import * #TEMPORY

selfIp = "169.254.178.71"
TCP_BUF_SIZE = 4046
UDP_BUF_SIZE = 512

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
    def __init__(self,serverIp,tcpPort=3746,udpPort=3745):
        self.SYNC = {} #A list of variables that gets synced with the server
        self.__SYNCBefore = {} #A list to detect changes in SYNC
        self.TRIGGER = {} #A list containing pointers to functions if the server calls them
        self.__serverIp = serverIp #IP of the server
        self.__tcpPort = tcpPort
        self.__udpPort = udpPort
        self.__tsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #Setup TCP socket
        self.__tsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1) #Change settings to work with the "select" library
        self.__tsock.settimeout(5)
        self.__usock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.__usock.bind((selfIp,udpPort))
        try: #Attempt to connect to the server
            self.__tsock.connect((serverIp,tcpPort))
        except: #An error occured while connecting...
            self.failConnect = True
            raise
        else:
            self.failConnect = False
    def loop(self):
        self.udpLoop()
        self.tcpLoop()
        self.detectAndApplySYNC()
    def serverShutdown(self): #The server has shutdown!
        print("Lost connection to server!")
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
    def getVariable(self,lis,path): #Get the value of a variable using a path list
        if not path[0] in lis:
            if len(path)==1:
                return 0
            else:
                lis[path[0]] = {}
        if type(lis[path[0]])==dict:
            return self.getVariable(lis[path[0]],path[1:])
        else:
            return lis[path[0]]
    def deleteVariable(self,lis,path): #Delete a variable using a path list
        if not path[0] in lis:
            if len(path)!=1:
                lis[path[0]] = {}
        if type(lis[path[0]])==dict:
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
                self.__tsock.sendall(pickle.dumps(sendTCP))
            if len(sendUDP)!=0:
                self.__usock.sendto(pickle.dumps(sendUDP),(self.__serverIp,self.__udpPort))
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
                self.deleteVariable(self.SYNC,data[1:])
                self.deleteVariable(self.__SYNCBefore,data[1:])
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
    def receive(self,data,tcpSent=False):
        if len(data)==0:
            return False
        if type(data[0])==list:
            for a in data[0]:
                self.doCommand(a,tcpSent)
        else:
            self.doCommand(data,tcpSent)
        print(self.SYNC)
    def udpLoop(self): #Loop for udp connection
        read,write,err = select.select([self.__usock],[],[],0)
        for sock in read:
            dataRaw,addr = sock.recvfrom(UDP_BUF_SIZE)
            if addr[0]==self.__serverIp: #Validate that this is the server
                try: #Try to read data coming through
                    data = pickle.loads(dataRaw)
                except: #Break out the loop of the data is corrupted
                    break
                self.receive(data)
    def tcpLoop(self): #Loop for tcp connection
        read,write,err = select.select([self.__tsock],[],[],0)
        for sock in read:
            if sock == self.__tsock:
                try:
                    dataRaw = sock.recv(TCP_BUF_SIZE)
                except socket.error:
                    self.serverShutdown()
                try:
                    data = pickle.loads(dataRaw)
                except:
                    break
                if data=="p": #Was pinged
                    self.__tsock.sendall(pickle.dumps("p"))
                else:
                    self.receive(data,True)

def tmpU():
    test.SYNC["Test"]+=1
def tmpD():
    test.SYNC["Test"]-=1

main = Tk()
but1 = Button(main,text="Up",command=tmpU)
but1.pack()
but2 = Button(main,text="Down",command=tmpD)
but2.pack()
val = Label(main,text="SYNC")
val.pack()
main.update()

test = Client("169.254.21.86")
if test.failConnect:
    print("Failed to connect!")
else:
    print("Conntected!")
    while True:
        test.loop()
        main.update()
        val.config(text=str(test.SYNC))
