#Main screen for drones
import pygame, time, pickle, sys, socket

import math #tempory

VERSION = 0.1

SCROLL_SPEED = 4 #Scematic scroll speed
CONSOLE_SIZE = [440,205] #Size of the console
DRONE_VIEW_SCALE = 3 #Drone view zoom in
DEF_RES = [1000,700] #Default reslution, this will be used to scale up the screen if required
MESH_BLOCK_SIZE = 125 #Size of a single mesh block
DEFAULT_COMMANDS = ["navigate","open","close","say","name","dock","swap","pickup"] #Default commands other than upgrade ones

def getMapMash(MAP): #Gets the map hash for the specific map
    file = open("maps/"+MAP,"rb")
    MLEN = len(file.read())
    file.close()
    MLEN = MLEN % 65535
    return MLEN
def nameIP(IP): #Turns an IP into hexadecimal charicters
    res = ""
    spl = IP.split(".")
    for a in spl:
        if int(a)<16:
            res+="0"
        res+=hex(int(a))[2:]
    return res
class GameEventHandle: #Used to simulate and handle the events of the game world (NOT VISUAL)
    def __init__(self, LINK):
        self.__LINK = LINK
        self.Map = [] #Stores ALL entities. Order does not matter
        self.Ref = {} #Reference, used to access specific types of entities
        self.IDLINK = {} #A dictionary of IDs for each entitiy loaded
        self.__lastTime = time.time() #Used to tackle lag
        self.drones = LINK["drones"] #All the drones used
        self.ship = LINK["shipEnt"] #The main ship of the map
        self.Mesh = {} #Used to speed up entitiy discovery, this is a 2D dictionary
        self.__IDMAX = -1
        LINK["mesh"] = self.Mesh #Set the global MESH to this classes one.
        LINK["create"] = self.createEnt #Create a new entity
        LINK["IDref"] = self.Ref
    def createEnt(self,name,pos,*args): #Creates a new entity
        if name in self.__LINK["ents"]:
            if self.__LINK["multi"]==1: #Is a client
                self.Map.append(self.__LINK["ents"][name].Main(pos[0],pos[1],self.__LINK,args[0],*tuple(args[1:])))
                ID = args[0]+0
            else:
                self.Map.append(self.__LINK["ents"][name].Main(pos[0],pos[1],self.__LINK,self.__IDMAX+0,*tuple(args)))
                ID = self.__IDMAX+0
            self.IDLINK[ID] = self.Map[-1]
            self.addToMesh(self.Map[-1])
            self.Map[-1].afterLoad()
            if not name in self.Ref:
                self.Ref[name] = []
            self.Ref[name].append(self.Map[-1])
            if self.__LINK["multi"]==2: #Is a server
                for a in self.__LINK["serv"].users:
                    self.__LINK["serv"].users[a].sendTrigger("mke",name,pos,self.__IDMAX+0,*tuple(args))
            self.__IDMAX += 1
            return self.Map[-1]
        else:
            self.__LINK["errorDisplay"]("Couln't create entity '"+name+"' because it doesen't exist!")
    def scanMESH(self): #Will scan the whole mesh for entities that shouldn't exist!
        for a in self.Mesh:
            for b in self.Mesh[a]:
                rem = []
                for c in self.Mesh[a][b]:
                    if c.REQUEST_DELETE:
                        rem.append(c)
                for c in rem:
                    self.Mesh[a][b].remove(c)
    def loop(self): # Called continuesly as an event loop for all entities in the map
        lag = (time.time()-self.__lastTime)*30 # Used to vary lag
        if lag>6: #Limit to how much the game can jump
            lag = 6
        self.__lastTime = time.time()
        rem = []
        for a in self.Map: # Loop through all objects and call their event loop
            a.loop(lag)
            if a.REQUEST_DELETE: #Entity is requesting to be deleted
                rem.append(a)
        for a in rem: #Remove entities requesting to be deleted
            a.deleteMesh() #Remove them from the MESH
            self.IDLINK.pop(a.ID) #Remove their easy access ID dictionary
            if self.__LINK["multi"]==2: #Is server
                self.__LINK["Broadcast"]("del",a.ID)
            if a in self.drones:
                self.drones.remove(a)
            self.Map.remove(a) #Finaly remove them from the map
            NAM = a.SaveFile()[0] #Get the name of the entity
            if NAM in self.Ref:
                if a in self.Ref[NAM]:
                    self.Ref[NAM].remove(a)
        if len(rem)!=0:
            self.scanMESH()
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def __addRawToMesh(self,x,y,Value):#Add the entity raw to the mesh (needs specific x and y values relative to the mesh size)
        if not x in self.Mesh: #The X dictionary doesen't exist
            self.Mesh[x] = {} #Create a new X column
        if not y in self.Mesh[x]: #The Y dictionary doesen't exist in this X plane
            self.Mesh[x][y] = [] #Create a new Y column
        self.Mesh[x][y].append(Value) #Add the entitiy to the mesh
    def addToMesh(self,ENT): #Adds an entity to the mesh
        for x in range(round(ENT.pos[0]/MESH_BLOCK_SIZE)-1,round(ENT.pos[0]/MESH_BLOCK_SIZE)+round(ENT.size[0]/MESH_BLOCK_SIZE)+1): #Add the entitiy to a 3x3 cube in the MESH
            for y in range(round(ENT.pos[1]/MESH_BLOCK_SIZE)-1,round(ENT.pos[1]/MESH_BLOCK_SIZE)+round(ENT.size[1]/MESH_BLOCK_SIZE)+1):
                self.__addRawToMesh(x,y,ENT)
    def open(self,name): #Opens a map
        try: #Attempt to open a file
            file = open("maps/"+name,"rb")
        except:
            self.__LINK["errorDisplay"]("Failed to open file!",sys.exc_info())
            return 0
        try: #Attempt to read a files data
            data = pickle.loads(file.read())
        except:
            self.__LINK["errorDisplay"]("Failed to pickle load file")
            file.close()
            return 0
        self.Map = [] #Stores ALL entities
        self.Ref = {}
        self.Mesh = {} #Stores the MESH
        self.IDLINK = {} #Used to initaly link entities up together
        self.__LINK["IDs"] = self.IDLINK
        doorCount = 1 #Counting doors
        airCount = 1 #Counting airlocks
        roomCount = 2 #Counting rooms
        self.__IDMAX = data[0]+0
        for a in data[1:]:
            if a[0]=="door": #Entity is a door
                self.Map.append(self.getEnt(a[0])(a[2][0],a[2][1],self.__LINK,a[1]+0,doorCount+0))
                self.Ref["d"+str(doorCount)] = self.Map[-1] #Add the door to the known list of doors
                doorCount += 1
            elif a[0]=="airlock": #Entitiy is an airlock
                self.Map.append(self.getEnt(a[0])(a[2][0],a[2][1],self.__LINK,a[1]+0,airCount+0))
                self.Ref["a"+str(airCount)] = self.Map[-1] #Add the airlock to the known list of airlocks
                airCount += 1
            elif a[0]=="room": #Entitiy is a room
                self.Map.append(self.getEnt(a[0])(a[2][0],a[2][1],self.__LINK,a[1]+0,roomCount+0))
                self.Ref["r"+str(roomCount)] = self.Map[-1] #Add the airlock to the known list of rooms
                roomCount += 1
            else: #Add the entitiy normaly.
                self.Map.append(self.getEnt(a[0])(a[2][0],a[2][1],self.__LINK,a[1]+0))
            self.IDLINK[a[1]+0] = self.Map[-1]
            if not a[0] in self.Ref: #Entity doesen't have its own directory, create one
                self.Ref[a[0]] = []
            self.Ref[a[0]].append(self.Map[-1]) #Add the entitiy to a list of ones its same type.
        defaultAir = None #The default airlock found.
        self.__LINK["IDref"] = self.Ref
        for i,a in enumerate(data[1:]): #Load all the etities settings
            try:
                self.Map[i].LoadFile(a,self.IDLINK)
                if type(self.Map[i]) == self.getEnt("airlock"): #Entity is an airlock
                    if self.Map[i].settings["default"]: #Is the default airlock
                        defaultAir = self.Map[i]
            except:
                self.__LINK["errorDisplay"]("Error when loading entity ",a,sys.exc_info())
            self.addToMesh(self.Map[i]) #Add the entitiy to the MESH
        self.__LINK["mesh"] = self.Mesh #Link the new MESH to the global one
        for a in self.Map: #Used to load content after the map has loaded sucsessfuly (e.g. special connections)
            a.afterLoad()
        self.__LINK["scrapCollected"] = 0 #Amount of scrap colected
        self.__LINK["fuelCollected"] = 0 #Amount of fuel colected
        if self.__LINK["multi"] != 1: #Is not a client
            if defaultAir is None:
                self.__LINK["log"]("There is no default airlock, finding one...")
                if "a1" in self.Ref:
                    defaultAir = self.Ref["a1"]
                else:
                    self.__LINK["log"]("There are no airlocks on this map, an exception is about to raise")
            self.Map.append(self.ship) #Add the main ship to the map
            self.ship.dockTo(defaultAir,True) #Dock the ship to an airlock
            self.ship.dockTime = 0 #Don't wait for docking
            self.Map.append(self.ship.room) #Add the ships room to the map
            self.Ref["r1"] = self.ship.room
            self.IDLINK[-6] = self.ship.room
            self.addToMesh(self.ship) #Add the ship to the MESH
            self.addToMesh(self.ship.room) #Add the ship's room to the MESH
            for i,a in enumerate(self.drones): #Add all the users drones to the map
                self.Map.append(a)
                if self.ship.LR: #Is the ship left to right
                    a.pos = [self.ship.room.pos[0]+(i*60)+40,self.ship.room.pos[1]+40]
                else:
                    a.pos = [self.ship.room.pos[0]+40,self.ship.room.pos[1]+(i*60)+40]
                self.addToMesh(a) #Add the drone to the MESH
                self.IDLINK[a.ID] = a
                if self.__LINK["multi"] == 2: #Is server
                    self.__LINK["serv"].SYNC["e"+str(a.ID)] = a.GiveSync()
        else: #Is a client
            self.drones = [] #Servers drones
            for i in range(2,6):
                if 0-i in self.IDLINK:
                    self.drones.append(self.IDLINK[0-i])
                else:
                    break
            self.ship = self.IDLINK[-1] #Servers ship
            self.ship.room = self.IDLINK[-6] #Set the ships room to the servers one
        file.close()
        self.__LINK["shipEnt"] = self.ship
        self.__LINK["mesh"] = self.Mesh #Link the new MESH to the global one
        self.__LINK["log"]("Opened file sucsessfuly!")
    def doCommand(self,text,drone,usrObj=None): #Will execute a command and return the text the command outputs
        out = "Unknown command '"+text+"'"
        col = (255,255,0)
        spl = text.split(" ")
        if len(text)==0:
            return out,col
        if text[0]=="d" and (text[1:].isnumeric() or len(text)==1): #Open/close a door
            gt = text[1:]
            if len(gt)==0:
                out = "No door number entered"
            elif not text in self.Ref:
                out = "No such door"
            else:
                out = self.Ref[text].toggle()
        elif text[0]=="a" and (text[1:].isnumeric() or len(text)==1): #Open/close an airlock
            gt = text[1:]
            if len(gt)==0:
                out = "No airlock number entered"
            elif not text in self.Ref:
                out = "No such airlock"
            else:
                out = self.Ref[text].toggle()
        elif spl[0]=="open": #Open a door/airlock
            if len(spl)==1:
                out = "No airlock/door specified"
            elif not spl[1] in self.Ref and spl[1]!="all":
                out = "No such airlock/door"
            elif spl[1]=="all":
                i = 1
                while "d"+str(i) in self.Ref:
                    self.Ref["d"+str(i)].OPEN()
                    i+=1
                out = "Opened all doors"
                col = (0,255,0)
            else:
                out = self.Ref[spl[1]].OPEN()
        elif spl[0]=="close": #Close a door/airlock
            if len(spl)==1:
                out = "No airlock/door specified"
            elif not spl[1] in self.Ref and spl[1]!="all":
                out = "No such airlock/door"
            elif spl[1]=="all":
                i = 1
                while "d"+str(i) in self.Ref:
                    self.Ref["d"+str(i)].CLOSE()
                    i+=1
                out = "Closed all doors"
                col = (0,255,0)
            else:
                out = self.Ref[spl[1]].CLOSE()
        elif spl[0]=="say": #Broadcast a message to all connected users (if in multiplayer)
            if self.__LINK["multi"]==0:
                out = "This command only works in multiplayer"
            elif len(spl)==1: #No content in the message
                out = "No text given to say"
            else: #Must be the server, broadcast to all users
                for a in self.__LINK["serv"].users:
                    self.__LINK["serv"].users[a].sendTrigger("com",usrObj.name+": "+text[4:],-2,(255,153,0))
                out = "NOMES" #Do not print the command out
        elif spl[0]=="name": #Change name for the current client
            if self.__LINK["multi"]==0:
                out = "This command only works in multiplayer"
            else: #Must be the server, broadcast to all users
                if len(spl)>1:
                    self.__LINK["serv"].SYNC[usrObj.ip2]["N"] = spl[1]
                    usrObj.sendTrigger("setn",spl[1])
                    out = "NOMES"
                else:
                    out = "No name supplied"
        elif spl[0]=="navigate": #Auto pilot a drone to a specific room
            if len(spl[0])<2:
                out = "Incorrect number of paramiters"
            else:
                if not spl[-1] in self.Ref: #Room exists
                    out = "No such room"
                elif len(spl)==2 and drone==-1: #If using quick navigating, there is an active drone feed
                    out = "Not on an active drone"
                else:
                    if len(spl)==2: #Move a drone to a place
                        if drone<0 or drone>=len(self.drones): #Drone doesen't exist
                            out = "No such drone"
                        else:
                            if self.drones[drone].alive:
                                if self.drones[drone].pathTo(self.Ref[spl[-1]]): #Move a drone to the room
                                    out = "Navigating drone "+str(drone+1)+" to "+spl[-1]
                                    col = (0,255,0)
                                else:
                                    out = "Room obstructed"
                            else:
                                out = "Drone is disabled"
                    elif spl[1]=="all": #Navigate all drones to a room
                        fail = False
                        for a in self.drones:
                            if a.alive:
                                fail = fail or not a.pathTo(self.Ref[spl[-1]])
                        if fail:
                            out = "Navigating all drones to "+spl[-1]+", although some are obstructed"
                        else:
                            out = "Navigating all drones to "+spl[-1]
                            col = (0,255,0)
                    else: #Navigate multiple drones but not all to a room
                        for a in spl[1:-1]:
                            if a!="":
                                if not a.isnumeric(): #Drone number invalid
                                    out = "Expected a drone NUMBER"
                                    break
                                elif int(a)<1 or int(a)>len(self.drones): #Drone does not exist
                                    out = "No such drone"
                                    break
                        else:
                            fail = False
                            drs = ""
                            for a in spl[1:-1]:
                                if a!="":
                                    if self.drones[int(a)-1].alive:
                                        fail = fail or not self.drones[int(a)-1].pathTo(self.Ref[spl[-1]])
                                        drs+=a+" "
                            if fail:
                                out = "Navigating drones "+drs+"to "+spl[-1]+" although some are obstructed"
                            else:
                                out = "Navigating drones "+drs+"to "+spl[-1]
                                col = (0,255,0)
        elif spl[0]=="dock": #Dock to a specific airlock
            if len(spl)==1:
                out = "Expected an airlock"
            elif not spl[1] in self.Ref:
                out = "No such airlock"
            elif spl[1][0]!="a":
                out = "Can only dock to an airlock"
            elif self.Ref[spl[1]]==self.ship.airlock:
                out = "Allredey docket to airlock"
            else:
                out,col = self.ship.dockTo(self.Ref[spl[1]])
                if self.__LINK["multi"]==2: #Is server
                    for a in self.__LINK["serv"].users:
                        self.__LINK["serv"].users[a].sendTrigger("dock",spl[1])
        elif len(spl)!=0: #Process the command as an upgrade
            if drone<0 or drone>=len(self.drones): #In scematic view
                for drone in self.drones+[self.ship]:
                    reason = None
                    if drone.alive:
                        for upgrade in drone.upgrades+drone.PERM_UPG:
                            if spl[0] in upgrade.caller: #Command belongs to upgrade
                                reason = upgrade.commandAllowed(text) #Is command valid or not according to the upgrade?
                                if reason==True: #Execute the upgrade command
                                    out = upgrade.doCommand(text,usrObj)
                                    if type(out)!=str:
                                        out = "NOMES"
                                    col = (0,255,0)
                                    break
                                elif type(reason)==str:
                                    out = reason+""
                    if reason == True:
                        break
            else:
                if self.drones[drone].alive:
                    for upgrade in self.drones[drone].upgrades+self.drones[drone].PERM_UPG:
                        if spl[0] in upgrade.caller: #Command belongs to upgrade
                            reason = upgrade.commandAllowed(text) #Is command valid or not according to the upgrade?
                            if reason==True: #Execute the upgrade command
                                out = upgrade.doCommand(text,usrObj)
                                if type(out)!=str:
                                    out = "NOMES"
                                col = (0,255,0)
                                break
                            elif type(reason)==str:
                                out = reason+""
                    if out=="NOMES" and usrObj is None:
                        out = ""
                else:
                    out = "Drone is disabled"
        return out,col

class Main: #Used as the screen object for rendering and interaction
    def __init__(self,LINK):
        self.__LINK = LINK
        self.Map = [] #Used to store the map inside
        self.Ref = {} #Used as a reference for other objects to find a selection of objects faster.
        self.mapLoaded = False #Is the map loaded or not
        self.mapLoading = False #Is the map loading
        self.__renderFunc = LINK["render"].Scematic(LINK,False) #Class to render entities
        self.__droneFeed = LINK["render"].DroneFeed(LINK) #Class to render entities in 3D as in drone feed
        self.__command = LINK["render"].CommandLine(LINK,3) #Class to render command line
        self.__reslution = LINK["reslution"] #Reslution of the game
        self.__Event = GameEventHandle(LINK) # Stores the class "GameEventHandle" to handle events for entities
        self.__renderFunc.ents = self.Map #Make sure the rendering class gets updates from this one through a pointer
        self.__droneFeed.ents = self.Map
        self.scematic = True #If viewing in scematic view
        self.__scemPos = [0,0] #Scematic position
        self.__HoldKeys = {} #Keys being held down
        self.__DOWNLOAD = [] #Used to store downloads (map)
        self.__typing = "" #The current typing text
        self.__typingOut = "" #The displayed output text for the typing text (used for hinting)
        self.__backPress = -1 # The time to press the backspace button again
        self.force = [] #A list of functions to call so the user has no controll until the functions say so, if empty then normal user controll is enabled
        self.__fChange = 0 #Used to detect changes in size inside the "force" list
        self.__LINK["force"] = self.force #Make it so everything can access this
        self.currentDrone = None #A reference to the currently selected drone
        if LINK["multi"] == 1: #Client to server
            self.__LINK["cli"].TRIGGER["dsnd"] = self.downLoadingMap #Downloading map function
            self.__LINK["cli"].finishLoading = self.finishSYNC #SYNC has finished downloading
            self.__LINK["cli"].TRIGGER["com"] = self.addCommands #Write text to the command line
            self.__LINK["cli"].TRIGGER["setn"] = self.changeName #Change our name
            self.__LINK["cli"].TRIGGER["dock"] = self.__clientDock #Ship has docked to an airlock
            self.__LINK["cli"].TRIGGER["del"] = self.__rmEnt #Remove entity
            self.__LINK["cli"].TRIGGER["rbub"] = self.__mkBubble #Create a visual bubble in a room
            self.__LINK["cli"].TRIGGER["rrub"] = self.__mkRad #Create a visual radiation bubble in a room
            self.__LINK["cli"].TRIGGER["rbud"] = self.__dlBubble #Remove all visual bubbles in a room
            self.__LINK["cli"].TRIGGER["cupg"] = self.__callUpgrade #Call an upgrade on a drone to work client-side (not recomended but used for menu's)
            self.__LINK["cli"].TRIGGER["mke"] = self.__Event.createEnt #Create a new entity in the map
            self.__LINK["cli"].TRIGGER["duc"] = self.__airTarget #Make a drone being sucked by an airlock
            self.name = socket.gethostbyname(socket.gethostname())
            self.IP = nameIP(self.name)
            mapLoading = True
        else:
            self.name = ""
        self.__LINK["outputCommand"] = self.putLine #So other entiteis can output to their tab
    def changeName(self,nam):
        self.name=nam
    def __callUpgrade(self,droneID,upgradeName,*args): #This is used to call functions on specific upgrades on drones (client-side)
        for a in self.__Event.IDLINK[droneID].upgrades+self.__Event.IDLINK[droneID].PERM_UPG:
            if a.name==upgradeName: #Found the upgrade
                a.clientCall(*tuple(args))
                break
    def __airTarget(self,ID,airID): #An airlock is targeting a drone
        if airID==False and type(airID)==bool: #Drone has stopped being sucked out an airlock
            self.__Event.IDLINK[ID].beingSucked = False
        elif self.__Event.IDLINK[ID].pathTo(self.__Event.IDLINK[airID]): #Drone is being sucked out an airlock
            self.__Event.IDLINK[ID].paths[-1][0] = 1
            self.__Event.IDLINK[ID].beingSucked = True
    def __mkBubble(self,ID,pos): #Creates a vacuum bubble in a room requested by the server
        self.__Event.IDLINK[ID].airBurst(pos,"",-1)
    def __mkRad(self,ID,pos): #Creates a radiation bubble in the room requested by the server
        self.__Event.IDLINK[ID].radBurst(pos)
    def __dlBubble(self,ID): #Remove all vacuum bubbles in a room requested by the server
        self.__Event.IDLINK[ID].fillAir()
    def __rmEnt(self,ID): #Removes an entitiy requested by the server
        self.__Event.IDLINK[ID].REQUEST_DELETE = True
    def __clientDock(self,TO): #Called by the server to dock to an airlock
        self.__Event.ship.dockTo(self.__Event.Ref[TO],True)
    def addCommands(self,tex,drone,extr=-1): #Called by the server to add text to a command line
        if drone==-1: #Scematic view
            dr = len(self.__command.tabs)-1
        elif drone==-2: #All views
            for i in range(0,len(self.__Event.drones)+1):
                if tex!="":
                    self.putLine(tex,extr,i)
                else:
                    self.putLine(extr[0],extr[1],i)
            dr = -2
        else: #A drone command line
            dr = drone
        if dr!=-2:
            if tex!="":
                self.putLine(tex,(255,255,255),dr)
            if extr!=-1:
                self.putLine(extr[0],extr[1],dr)
    def __isKeyDown(self,key): #Returns true if the key is being held down
        if key in self.__HoldKeys: #Has the key been pressed before?
            return self.__HoldKeys[key]
        return False
    def goToDrone(self,number): #Goto a specific drone number view
        droneNums = {}
        for a in self.__Event.drones:
            droneNums[a.number] = a
        if not number in droneNums: #Drone doesen't exist
            self.putLine("No such drone "+str(number),(255,255,0))
        else: #Drone exists
            self.currentDrone = droneNums[number] #Set the current drone object to the one specified
            self.scematic = False #Is not viewing in scematic view
            self.__command.activeTab = number-1 #Switch to the specific tab of the drone
            self.__UpdateRender = 0
    def putLine(self,tex,col,Tab=None): #Adds a line to the current command line
        if Tab is None:
            TB = None
        elif type(Tab) != int:
            TB = Tab.number-1
        else:
            TB = Tab
        self.__command.replaceLast(tex,col,TB)
        if TB is None:
            self.__command.addLine(self.name+">"+self.__typing,(255,255,255))
        else:
            self.__command.addLine(self.name+">"+self.__typing,(255,255,255),TB)
    def doCommand(self,command): #Does a command to the currently selected drone/ship
        if command=="":
            return 0
        if self.__LINK["multi"]==1: #Send the command to the server to process
            if len(command)>175: #Max text limit for text
                self.putLine("Gone over max text limit",(255,255,255))
            else:
                if not self.currentDrone in self.__Event.drones:
                    self.currentDrone = None
                if self.currentDrone is None:
                    self.__LINK["cli"].sendTrigger("com",command,-1)
                else:
                    self.__LINK["cli"].sendTrigger("com",command,self.__Event.drones.index(self.currentDrone))
        else:
            self.__command.replaceLast(">"+self.__typing)  
            if self.currentDrone is None:
                tex,col = self.__Event.doCommand(command,-1)
            else:
                tex,col = self.__Event.doCommand(command,self.__Event.drones.index(self.currentDrone))
            if tex!="" and tex!="NOMES":
                self.__command.addLine(tex,col)
            self.__command.addLine(">",(255,255,255))
    def __isAtStart(self,str1,str2): #Returns true/false if the string is at the start of the other string
        if len(str1)>len(str2):
            return False
        for i,a in enumerate(str1): #Find charicters that are the same
            if a!=str2[i]:
                return False
        return True
    def __hintTyping(self): #Hints what the user is typing
        if len(self.__typing)==0:
            self.__typingOut = ""
            return 0
        for a in DEFAULT_COMMANDS: #Find a command that matches the typing string
            if self.__isAtStart(self.__typing,a):
                self.__typingOut = self.__typing+a[len(self.__typing):].upper()
                break
        else: #No matching default command found
            self.__typingOut = ""
            if self.currentDrone is None: #Search all drones and ship upgrades
                for d in self.__Event.drones+[self.__Event.ship]: #Go through every drone and the ship
                    for a in d.upgrades: #Go through all upgrades on the entity
                        for b in a.caller: #Loop through all the names it the upgrade can be called by
                            if self.__isAtStart(self.__typing,b): #Should show a hint?
                                self.__typingOut = self.__typing+b[len(self.__typing):].upper()
                                break
                        if self.__typingOut!="":
                            break
                    if self.__typingOut!="":
                        break
            else: #Search active drone for hints
                for a in self.currentDrone.upgrades: #Loop through all the drones upgades
                    for b in a.caller: #Loop throguh all the commands that can be called for this upgade
                        if self.__isAtStart(self.__typing,b): #Should show a hint?
                            self.__typingOut = self.__typing+b[len(self.__typing):].upper()
                            break
                    if self.__typingOut!="":
                        break
            if self.__typingOut == "":
                self.__typingOut = self.__typing+""
    def loop(self,mouse,kBuf,lag): #Constant loop
        global start
        if len(self.force)!=0: #A force function has taken over (e.g. swap menu)
            if len(self.force)!=self.__fChange: #Force has just started
                self.__fChange = len(self.force)
                for a in self.__HoldKeys: #Stop all holding keys
                    self.__HoldKeys[a] = False
            for a in self.force:
                a[1](mouse,kBuf,lag)
        else: #Run normaly
            self.__fChange = 0
            for event in kBuf: #Loop through keyboard event loops
                if event.type == pygame.KEYDOWN:
                    self.__HoldKeys[event.key] = True
                    if event.key >= 48 and event.key <=57 and len(self.__typing)==0: #Key is a number
                        self.goToDrone(int(chr(event.key)))
                    elif event.key == pygame.K_SPACE and len(self.__typing)==0: #Exit out of scematic view
                        self.scematic = True
                        self.currentDrone = None
                        self.__command.activeTab = len(self.__command.tabs)-1 #Goto the ships command line
                    elif event.key >= 32 and event.key <= 126: #A key was pressed down for typing
                        self.__typing += chr(event.key)
                        self.__hintTyping()
                    elif event.key == pygame.K_BACKSPACE: #Backspace
                        self.__typing = self.__typing[:-1]
                        self.__backPress = time.time()+0.4
                        self.__hintTyping()
                    elif event.key == pygame.K_TAB: #Tab key, auto fill hint
                        if len(self.__typingOut)!=len(self.__typing):
                            self.__typing = self.__typingOut.lower()+" "
                            self.__typingOut = self.__typingOut.lower()+" "
                    elif event.key == pygame.K_RETURN: #Enter button was pressed
                        self.doCommand(self.__typing)
                        self.__typing = ""
                        self.__typingOut = ""
                elif event.type == pygame.KEYUP:
                    self.__HoldKeys[event.key] = False
        if self.mapLoaded:
            self.reloadCommandline()
        if (time.time()-int(time.time()))*2%1<0.5 or len(self.__typing)!=len(self.__typingOut):
            self.__command.replaceLast(self.name+">"+self.__typingOut)
        else:
            self.__command.replaceLast(self.name+">"+self.__typingOut+"_")
        if self.__isKeyDown(pygame.K_BACKSPACE) and time.time()>self.__backPress:
            self.__backPress = time.time()+0.05
            self.__typing = self.__typing[:-1]
            self.__hintTyping()
        if self.scematic: #Is currently in the scematic view
            #Move the scematic view if the arrow keys are being held or pressed.
            if self.__isKeyDown(self.__LINK["controll"]["up"]):
                self.__scemPos[1] -= SCROLL_SPEED*lag
            if self.__isKeyDown(self.__LINK["controll"]["down"]):
                self.__scemPos[1] += SCROLL_SPEED*lag
            if self.__isKeyDown(self.__LINK["controll"]["left"]):
                self.__scemPos[0] -= SCROLL_SPEED*lag
            if self.__isKeyDown(self.__LINK["controll"]["right"]):
                self.__scemPos[0] += SCROLL_SPEED*lag
        elif not self.currentDrone is None: #Move a drone the player is controlling
            if self.currentDrone.REQUEST_DELETE:
                if self.currentDrone in self.__Event.drones:
                    self.__Event.drones.remove(self.currentDrone)
                self.currentDrone = None
                self.scematic = True
                self.__command.activeTab = len(self.__command.tabs)-1
                self.reloadCommandline()
            else:
                if self.__isKeyDown(self.__LINK["controll"]["up"]):
                    self.currentDrone.go(lag)
                if self.__isKeyDown(self.__LINK["controll"]["down"]):
                    self.currentDrone.go(-1*lag)
                if self.__isKeyDown(self.__LINK["controll"]["left"]):
                    self.currentDrone.turn(lag*4)
                if self.__isKeyDown(self.__LINK["controll"]["right"]):
                    self.currentDrone.turn(-4*lag)
        if not self.__Event is None:
            self.__Event.loop()
    def reloadCommandline(self): #Reloads all the drone/ship upgrades and infomation to the command line
        droneNums = []
        for a in self.__Event.drones:
            droneNums.append(a.number)
        i2 = 0
        for i in range(0,len(self.__command.tabs)-1):
            if i+1 in droneNums:
                a = self.__Event.drones[i2]
                i2+=1
                if a.settings["health"]<=0 or not a.alive:
                    self.__command.settings(i,1,a.beingAttacked,a.upgrades)
                else:
                    self.__command.settings(i,0,a.beingAttacked,a.upgrades)
            else:
                self.__command.settings(i,2)
        self.__command.settings(len(self.__command.tabs)-1,0,False,self.__LINK["shipEnt"].upgrades)
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def downLoadingMap(self,LN): #Function called to save a peaice of the map
        print("GOT,",LN) #TEMPORY
        self.__DOWNLOAD.append(LN) #Add the downloading map to the buffer
    def finishSYNC(self): #Finished downloading SYNC and possibly the map
        if len(self.__DOWNLOAD)!=0:
            print("Finished loading")
            file = open("maps/SERVER_MAP.map","wb")
            file.write(pickle.dumps(self.__DOWNLOAD))
            file.close()
            self.__DOWNLOAD = []
            self.open("SERVER_MAP.map")
            if self.__LINK["cli"].SYNC["V"]!=VERSION:
                if self.__LINK["cli"].SYNC["V"]>VERSION:
                    self.__LINK["errorDisplay"]("Server has a more updated version than you ("+str(self.__LINK["cli"].SYNC["V"]))
                else:
                    self.__LINK["errorDisplay"]("You have a more updated version than the server ("+str(self.__LINK["cli"].SYNC["V"]))
    def open(self,name): #Opens a map
        self.__Event.open(name)
        self.__renderFunc.ents = self.__Event.Map
        self.__droneFeed.ents = self.__Event.Map
        self.__scemPos = [self.__Event.ship.pos[0]-(self.__LINK["reslution"][0]/2),self.__Event.ship.pos[1]-(self.__LINK["reslution"][1]/2)] #Start the scematic position at the ships position
        self.__command.activeTab = len(self.__Event.drones)
        for i,a in enumerate(self.__Event.drones):
            self.__command.tabs.insert(i,["DRONE-"+str(i+1),[[">",[255,255,255]]],0,[],False,a])
        self.reloadCommandline()
        self.mapLoaded = True
        self.mapLoading = False
    def render(self,surf=None): #Render everything.
        if surf is None:
            surf = self.__LINK["main"]
        scale = ((self.__LINK["reslution"][0]/DEF_RES[0])+(self.__LINK["reslution"][1]/DEF_RES[1]))/2
        if self.scematic: #Is inside the scematic view
            if self.__LINK["DEVDIS"]:
                self.__LINK["render"].drawDevMesh(self.__scemPos[0],self.__scemPos[1],0.8,surf,self.__LINK) #DEVELOPMENT
            self.__renderFunc.render(self.__scemPos[0],self.__scemPos[1],0.8,surf) #Render the map.
        elif not self.currentDrone is None:
            drpos = [self.currentDrone.pos[0]*DRONE_VIEW_SCALE*scale,self.currentDrone.pos[1]*DRONE_VIEW_SCALE*scale] #Find the drones position in screen coordinates
            if self.__LINK["DEVDIS"]:
                self.__LINK["render"].drawDevMesh(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,surf,self.__LINK) #DEVELOPMENT
            self.__renderFunc.render(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,surf,True) #Render the map through drone view.
            self.__droneFeed.render(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,self.currentDrone.angle+90,self.currentDrone.findPosition(),self.currentDrone,surf) #Render map in 3D
        if self.__LINK["DEVDIS"]:
            self.__LINK["render"].drawConnection(10,10,surf,self.__LINK)
        self.__command.render(self.__reslution[0]-CONSOLE_SIZE[0]-20,self.__reslution[1]-CONSOLE_SIZE[1]-20,CONSOLE_SIZE[0],CONSOLE_SIZE[1],surf) #Render command line
        for a in self.force:
            a[2](surf,list(surf.get_size()))


