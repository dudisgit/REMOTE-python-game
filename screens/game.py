#Main screen for drones
import pygame, time, pickle, sys, socket, random, traceback
import math #tempory

VERSION = 0.2

SCROLL_SPEED = 4 #Scematic scroll speed
CONSOLE_SIZE = [440,205] #Size of the console
DRONE_VIEW_SCALE = 3 #Drone view zoom in
DEF_RES = [1000,700] #Default reslution, this will be used to scale up the screen if required
MESH_BLOCK_SIZE = 125 #Size of a single mesh block
DEFAULT_COMMANDS = ["open","close","help","navigate","say","name","dock","swap","pickup","flag","info","exit"] #Default commands other than upgrade ones
HELP_COMS = {"navigate":"Navigate a drone to a room, \nUsage: navigate <DRONE NUMBER> <ROOM>",
            "open":"Open a door or airlock \nUsage: open <DOOR/AIRLOCK>",
            "close":"Close a door or airlock \nUsage: close <DOOR/AIRLOCK>",
            "say":"Broadcast a message to all command lines (multiplayer only) \nUsage: say <TEXT>",
            "name":"Change your name on the server \nUsage: name <TEXT>",
            "dock":"Dock to an airlock \nUsage dock <AIRLOCK>",
            "swap":"Swap upgrades with the closest drone \nUsage: swap",
            "pickup":"Pickup something a drone placed down \nUsage pickup",
            "flag":"Flag a room so you don't forget \nUsage flag <ROOM>",
            "info":"Gathers infomation about the room a drone is in \nUsage info",
            "gather":"Gathers scrap and fuel \nUsage: gather",
            "generator":"Powers a generator \nUsage: generator",
            "interface":"Connects to an interface \nUsage: interface",
            "lure":"Places a lure that can be picked up \nUsage: lure",
            "motion":"Scans nearby rooms for motion \nUsage: motion",
            "overload":"Surges a room and kills anything electronic \nUsage: overload <ROOM>",
            "stealth":"Makes drone invisible to threats \nUsage: stealth",
            "tow":"Tows nearby drones/upgrades \nUsage: tow"}
COMPARAMS = {"open":"e",
            "close":"e",
            "say":"T",
            "name":"T",
            "dock":"A",
            "swap":"",
            "pickup":"",
            "flag":"R",
            "info":"",
            "gather":"",
            "generator":"",
            "interface":"",
            "lure":"",
            "motion":"",
            "tow":"",
            "navigate":"R",
            "overload":"R",
            "stealth":"",
            "pry":"",
            "remote":"R",
            "sensor":"",
            "tow":"",
            "help":"T"} #Paramiters for commands, (used for controllers)
OVERLAY_OPASITY = 30 #Opasity of the overlay (0-255)
COMMAND_HISTORY_LENGTH = 30 #Length of the command history

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
        self.mapSize = [0,0,0,0] #Size of the map
        self.drones = LINK["drones"] #All the drones used
        self.__startDrones = len(self.drones)
        self.__quiting = False #Is the user attempting to quit
        self.exit = False #Should the game exit or not
        self.ship = LINK["shipEnt"] #The main ship of the map
        self.Mesh = {} #Used to speed up entitiy discovery, this is a 2D dictionary
        self.__IDMAX = -1
        LINK["mesh"] = self.Mesh #Set the global MESH to this classes one.
        LINK["create"] = self.createEnt #Create a new entity
        LINK["IDref"] = self.Ref
        self.__LINK["scrapCollected"] = 0
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
            try:
                a.loop(lag)
            except:
                print("Failed to run loop on entity ID ",a.ID,a)
                traceback.print_exc()
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
        self.mapSize = [0,0,0,0]
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
                if self.Map[i].pos[0]<self.mapSize[0]:
                    self.mapSize[0] = self.Map[i].pos[0]+0
                if self.Map[i].pos[1]<self.mapSize[1]:
                    self.mapSize[1] = self.Map[i].pos[1]+0
                if self.Map[i].pos[0]+self.Map[i].size[0]>self.mapSize[2]:
                    self.mapSize[2] = self.Map[i].pos[0]+self.Map[i].size[0]
                if self.Map[i].pos[1]+self.Map[i].size[1]>self.mapSize[3]:
                    self.mapSize[3] = self.Map[i].pos[1]+self.Map[i].size[1]
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
                a.stopNavigation()
        else: #Is a client
            self.drones = [] #Servers drones
            for i in range(2,6):
                if 0-i in self.IDLINK:
                    self.drones.append(self.IDLINK[0-i])
                else:
                    break
            self.__LINK["drones"] = self.drones
            self.ship = self.IDLINK[-1] #Servers ship
            self.ship.room = self.IDLINK[-6] #Set the ships room to the servers one
            self.ship.LR = self.ship.room.size[0]>self.ship.room.size[1]
        file.close()
        self.__LINK["shipEnt"] = self.ship
        self.__LINK["mesh"] = self.Mesh #Link the new MESH to the global one
        self.__LINK["log"]("Opened file sucsessfuly!")
    def clean(self): #Clears the map, unloads all entities and returns the entities inside the ship area
        shipEnts = self.Ref["r1"].EntitiesInside()
        self.__LINK["mesh"] = {}
        self.__LINK["IDref"] = {}
        self.Map = []
        self.Ref = {}
        self.IDLINK = {}
        self.Mesh = {}
        for a in shipEnts: #Go through all entities inside the ship room
            if type(a)==self.getEnt("drone"): #Entity is a drone
                for b in a.upgrades: #Go through all the drones upgrades
                    b.afterDamage()
        for a in self.__LINK["shipEnt"].upgrades:
            a.afterDamage()
        return shipEnts
    def doCommand(self,text,drone,usrObj=None): #Will execute a command and return the text the command outputs
        out = "Unknown command '"+text+"'"
        col = (255,255,0)
        spl = text.split(" ")
        if len(text)==0:
            return out,col
        if spl[0]!="exit":
            self.__quiting = False
        if text[0]=="d" and (text[1:].isnumeric() or len(text)==1): #Open/close a door
            gt = text[1:]
            if len(gt)==0:
                out = "No door number entered"
            elif not text in self.Ref:
                out = "No such door"
            elif not self.Ref[text].discovered:
                out = "No such door"
            else:
                out = self.Ref[text].toggle()
        elif text[0]=="a" and (text[1:].isnumeric() or len(text)==1): #Open/close an airlock
            gt = text[1:]
            if len(gt)==0:
                out = "No airlock number entered"
            elif not text in self.Ref:
                out = "No such airlock"
            elif not self.Ref[text].discovered:
                out = "No such airlock"
            else:
                out = self.Ref[text].toggle()
        elif spl[0]=="open": #Open a door/airlock
            if len(spl)==1:
                out = "No airlock/door specified"
            elif not spl[1] in self.Ref and spl[1]!="all":
                out = "No such airlock/door"
            elif spl[1][0]=="r":
                out = "Must be a door/airlock"
            elif spl[1]=="all":
                i = 1
                while "d"+str(i) in self.Ref:
                    self.Ref["d"+str(i)].OPEN()
                    i+=1
                out = "Opened all doors"
                col = (0,255,0)
            elif not self.Ref[spl[1]].discovered:
                out = "No such airlock/door"
            else:
                out = self.Ref[spl[1]].OPEN()
        elif spl[0]=="close": #Close a door/airlock
            if len(spl)==1:
                out = "No airlock/door specified"
            elif not spl[1] in self.Ref and spl[1]!="all":
                out = "No such airlock/door"
            elif spl[1][0]=="r":
                out = "Must be a door/airlock"
            elif spl[1]=="all":
                i = 1
                while "d"+str(i) in self.Ref:
                    self.Ref["d"+str(i)].CLOSE()
                    i+=1
                out = "Closed all doors"
                col = (0,255,0)
            elif not self.Ref[spl[1]].discovered:
                out = "No such airlock/door"
            else:
                out = self.Ref[spl[1]].CLOSE()
        elif spl[0]=="say": #Broadcast a message to all connected users (if in multiplayer)
            if self.__LINK["multi"]==0:
                out = "This command only works in multiplayer"
            elif len(spl)==1: #No content in the message
                out = "No text given to say"
            else: #Must be the server, broadcast to all users
                for a in self.__LINK["serv"].users:
                    self.__LINK["serv"].users[a].sendTrigger("com",usrObj.name+": "+text[4:],-2,False,(255,153,0))
                file = open("LOG.txt","a")
                file.write("New user message "+str(usrObj.ip2)+"("+str(usrObj.name)+") said "+text[4:]+"\n")
                file.close()
                out = "NOMES" #Do not print the command out
        elif spl[0]=="name": #Change name for the current client
            if self.__LINK["multi"]==0:
                out = "This command only works in multiplayer"
            elif len(spl[1])==0:
                out = "Nothing entered"
            elif "\\" in spl[1]:
                out = "Invalid charicter entered '\\'"
            else: #Must be the server, broadcast to all users
                if len(spl)>1:
                    for a in self.__LINK["serv"].users:
                        if self.__LINK["serv"].SYNC[self.__LINK["serv"].users[a].ip2]["N"]==spl[1]:
                            out = "User name has been taken"
                            break
                    else:
                        self.__LINK["serv"].SYNC[usrObj.ip2]["N"] = spl[1]
                        usrObj.sendTrigger("setn",spl[1])
                        out = "NOMES"
                        file = open("LOG.txt","a")
                        file.write("New user namechange "+str(usrObj.ip2)+" to "+str(spl[1])+"\n")
                        file.close()
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
                elif not self.Ref[spl[-1]].discovered:
                    out = "No such room"
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
            elif not self.Ref[spl[1]].discovered:
                out = "No such airlock"
            else:
                out,col = self.ship.dockTo(self.Ref[spl[1]])
                if self.__LINK["multi"]==2: #Is server
                    for a in self.__LINK["serv"].users:
                        self.__LINK["serv"].users[a].sendTrigger("dock",spl[1])
        elif spl[0]=="flag": #Flag a room
            if len(spl)==1:
                out = "Expected a room"
            elif not spl[1] in self.Ref:
                out = "No such room"
            elif not self.Ref[spl[1]].discovered:
                out = "No such room"
            elif spl[1][0]!="r":
                out = "Expected a room"
            else:
                col = (0,255,0)
                out = self.Ref[spl[1]].toggleFlag()
        elif spl[0]=="help":
            if len(spl)==1:
                out = "Expected a command"
            elif spl[1] in HELP_COMS:
                out = HELP_COMS[spl[1]]
            else:
                out = "No such command"
        elif spl[0]=="exit":
            if not self.__quiting:
                for a in self.drones:
                    if a.findPosition()!=self.Ref["r1"]:
                        out = "All drones are not in R1, are you sure you want to exit?"
                        self.__quiting = True
                        break
                else:
                    pass
            else:
                self.__quiting = False
            if not self.__quiting:
                self.exit = True
        elif len(spl)!=0: #Process the command as an upgrade
            if drone<0 or drone>=len(self.drones): #In scematic view
                for drone in self.drones+[self.ship]:
                    reason = None
                    if drone.alive:
                        for upgrade in drone.upgrades+drone.PERM_UPG:
                            if spl[0] in upgrade.caller and upgrade.damage!=2: #Command belongs to upgrade
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
                        if spl[0] in upgrade.caller and upgrade.damage!=2: #Command belongs to upgrade
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
    def getScore(self): #Returns the score for the player (usualy called when exiting)
        Ents = self.Ref["r1"].EntitiesInside()
        DroneReferenceObject = self.getEnt("drone")
        UpgradeReferenceObject = self.getEnt("ShipUpgrade")
        score = 0
        #20 = A new drone
        #15 = A ship upgrade
        #50 = Fuel collected
        for a in Ents:
            if type(a)==DroneReferenceObject:
                if a.ID>=0:
                    score+=20
            elif type(a)==UpgradeReferenceObject:
                score+=15
        score-=self.__startDrones-len(self.drones)
        for a in self.drones:
            if a.findPosition()!=self.Ref["r1"]:
                score-=20
        score+=self.__LINK["scrapCollected"]
        score+=self.__LINK["fuelCollected"]*50
        return score


class Main: #Used as the screen object for rendering and interaction
    def __init__(self,LINK,tutorial=False):
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
        self.__commands = [] #Command history
        self.__commandSelect = 0 #Selecting command
        self.__viewChangeEffect = 0
        self.__controllerMenu = [0,[]] #Controller menu
        self.__controllHold = -1 #Controller key hold
        self.__controllSelect = None #The entity the drone is facing (for easy controller interface)
        self.__controllerChange = {"x":False,"y":False,"b":False,"a":False,"sel":False,"start":False,"lt":False,"rt":False,"up":False,"down":False,"left":False,"right":False} #Used to detect changed in controller button sates
        #1 = Command selecting
        self.scematic = True #If viewing in scematic view
        self.tutorial = tutorial #Enable/disable tutorial mission
        if tutorial: #In a tutorial mission
            self.tpart = [0,False,False,0,[],[]] #Tutorial part, used to track progression in the tutorial.
            for a in LINK["drones"]+[LINK["shipEnt"]]:
                for b in range(0,len(a.settings["upgrades"])):
                    a.settings["upgrades"][b] = ["",0,-1]
            LINK["drones"][0].settings["upgrades"][0] = ["gather",0,-1]
            LINK["drones"][0].settings["upgrades"][1] = ["motion",0,-1]
            LINK["drones"][1].settings["upgrades"][0] = ["generator",0,-1]
            LINK["drones"][2].settings["upgrades"][0] = ["interface",0,-1]
            LINK["drones"][2].settings["upgrades"][1] = ["tow",0,-1]
            LINK["drones"][0].loadUpgrades()
            LINK["drones"][1].loadUpgrades()
            LINK["drones"][2].loadUpgrades()
            LINK["shipEnt"].settings["upgrades"][0] = ["overload",1,-1]
            LINK["shipEnt"].loadUpgrades()
        sx,sy = LINK["main"].get_size()
        #sx = 1000
        #sy = 700
        sx2 = sy*1.777
        self.__loading = [False,pygame.transform.scale(LINK["content"]["loading"],(int(sx2),int(sy))),(sx2-sx)/-2,0,"Downloading variables",[sx,sy]]
        self.__fail = [False,pygame.transform.scale(LINK["content"]["loading"],(int(sx2),int(sy))),(sx2-sx)/-2,[sx,sy],"Unknown error"]
        self.__extrInfo = [] #Extra info on a fail screen
        #syntax of loading = Active, pygame image, x offset, loading percentage, loading message, screen size
        self.__scemPos = [0,0] #Scematic position
        self.__HoldKeys = {} #Keys being held down
        self.__DOWNLOAD = [] #Used to store downloads (map)
        self.__typing = "" #The current typing text
        self.__cols = [] #Colour lists
        self.__changeEffect = [0,0.0]
        self.__typingOut = "" #The displayed output text for the typing text (used for hinting)
        self.__backPress = -1 # The time to press the backspace button again
        self.force = [] #A list of functions to call so the user has no controll until the functions say so, if empty then normal user controll is enabled
        self.__fChange = 0 #Used to detect changes in size inside the "force" list
        self.__LINK["force"] = self.force #Make it so everything can access this
        self.currentDrone = None #A reference to the currently selected drone
        if LINK["multi"] == 1: #Client to server
            self.__loading[0] = True
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
            self.__LINK["cli"].TRIGGER["disc"] = self.__disconnect #Server disconencted user
            self.name = socket.gethostbyname(socket.gethostname())
            self.IP = nameIP(self.name)
            mapLoading = True
            if self.__LINK["cli"].failConnect:
                self.__loading[0] = False
                self.__fail[0] = True
                self.__fail[4] = "Connection error: "+self.__LINK["cli"].errorReason
        else:
            self.name = ""
        self.__LINK["outputCommand"] = self.putLine #So other entiteis can output to their tab
        if LINK["backgroundStatic"]:
            print("Generating overlays")
            for a in range(3):
                self.__cols.append(pygame.Surface((sx,sy)))
                matr = pygame.PixelArray(self.__cols[-1])
                for x in range(int(sx/3)):
                    for y in range(int(sy/3)):
                        matr[x*3:(x*3)+3,y*3:(y*3)+3] = pygame.Color(random.randint(0,50),random.randint(0,50),random.randint(0,50))
                    if self.__LINK["multi"]==1:
                        self.__LINK["cli"].loop()
            print("Done")
    def __disconnect(self,reason):
        self.__fail[0] = True
        self.__fail[4] = "Disconnected: "+reason
        self.__LINK["cli"].close()
    def controller_key(self,typ): #Returns wether a button is pressed
        if self.__LINK["controller"] is None:
            return False
        if typ=="up": #Up button
            return self.__LINK["controller"].get_axis(1)<-0.5
        elif typ=="down": #Down button
            return self.__LINK["controller"].get_axis(1)>0.5
        elif typ=="left": #Left button
            return self.__LINK["controller"].get_axis(0)<-0.5
        elif typ=="right": #Right button
            return self.__LINK["controller"].get_axis(0)>0.5
        elif typ=="x": #X button
            return self.__LINK["controller"].get_button(0)
        elif typ=="y": #Y button
            return self.__LINK["controller"].get_button(3)
        elif typ=="b": #B button
            return self.__LINK["controller"].get_button(2)
        elif typ=="a": #A button
            return self.__LINK["controller"].get_button(1)
        elif typ=="lt": #Left trigger
            return self.__LINK["controller"].get_button(4)
        elif typ=="rt": #Right trigger
            return self.__LINK["controller"].get_button(5)
        elif typ=="sel": #Select button
            return self.__LINK["controller"].get_button(8)
        elif typ=="start": #Start button
            return self.__LINK["controller"].get_button(9)
        return False
    def __droneMove(self): #Highlights the closest door to the drones angle
        self.__controllSelect = None
        if self.__LINK["controller"] is None:
            return 0
        if not self.currentDrone is None: #A drone is acvtivly being controlled 
            rm = self.currentDrone.findPosition()
            AirlockReferenceObject = self.getEnt("airlock")
            if type(rm)==self.getEnt("room"): #Drone is in a room
                closest = [-1,None]
                for a in rm.doors: #Go through the rooms doors
                    if a.powered and not (type(a)==AirlockReferenceObject and a.room2 is None): #Door is powered and is not an un-docked airlock
                        #Get the angle of the drone towards the door and compare distances
                        angle = math.atan2(self.currentDrone.pos[0]-a.pos[0],self.currentDrone.pos[1]-a.pos[1])*180/math.pi
                        angle = int(angle) % 360 #Put into the range 0-360
                        dist2 = 360
                        if angle > self.currentDrone.angle:
                            if angle - self.currentDrone.angle > 180:
                                dist2 = 180 - (angle - 180 - self.currentDrone.angle)
                            else:
                                dist2 = angle - self.currentDrone.angle
                        else:
                            if self.currentDrone.angle - angle > 180:
                                dist2 = 180 - (self.currentDrone.angle - 180 - angle)
                            else:
                                dist2 = self.currentDrone.angle - angle
                        if abs(dist2)<closest[0] or closest[0]==-1: #Check if the door/airlock is closest to the centre of the room
                            closest[0] = abs(dist2)+0
                            closest[1] = a
                self.__controllSelect = closest[1]
    def changeName(self,nam):
        self.name=nam
    def renderHint(self,surf,message,pos,ctext="Press enter or space to continue"): #Render a hint box
        screenRes = self.__LINK["reslution"] #Screen reslution
        boxPos = [pos[0]+10,pos[1]+10] #Position of the box
        boxWidth = screenRes[0]/2 #Width of the box will be half the screen width
        boxHeight = 0
        mes = message.split(" ") #Split the message up by spaces
        font = self.__LINK["font24"] #Font to use when rendering
        adding = "" #Text being added to that line
        drawWord = [] #Store all the text in a list to be rendered
        for word in mes: #Loop through all text samples and build a list of strings that are cut off when they get to the end and start on the next element
            if font.size(adding+word)[0] > boxWidth or "\n" in word: #Length would be above the length of the box or the message requested a new line using "\n"
                drawWord.append(adding+"")
                if "\n" in word: #Remove the "\n"
                    spl = word.split("\n")
                    if "" in spl:
                        spl.remove("")
                    adding = spl[0]+" "
                else:
                    adding = word+" "
                boxHeight += 20
            else:
                adding += word+" "
        if len(adding)!=0: #If any are left then add them onto the end
            drawWord.append(adding+"")
            boxHeight+=20
        boxHeight+=20
        boxPos[1] = pos[1]-boxHeight-10 #Re-calculate the box position depening on the text height
        pygame.draw.rect(surf,(0,0,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8]) #Black box background
        mult = abs(math.cos(time.time()*3)) #Box flashing
        pygame.draw.rect(surf,(255*mult,255*mult,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8],3) #Flashing box
        surf.blit(font.render(ctext,16,(255*mult,255*mult,0)),[boxPos[0],boxPos[1]+boxHeight-16])
        for i,a in enumerate(drawWord): #Draw all the text calculated above
            surf.blit(font.render(a,16,(0,255,0)),[boxPos[0],boxPos[1]+(i*20)])
    def nextTutorial(self,kBuf): #Progresses through the tutorial
        for event in kBuf:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if self.tpart[0]<2:
                        self.tpart[0]+=1
                        self.tpart[3] = 0
        if self.__Event.Ref["a1"].settings["open"] and self.tpart[0]==2: #Openeing a1
            self.tpart[0]+=1
            self.tpart[3] = 0
        if self.tpart[0]>=7 and self.tpart[0]<13: #Between part 7 and 13 make sure drone 1 stays in R3
            RM = self.__Event.drones[0].findPosition()
            if RM!=self.__Event.Ref["r3"]: #Drone is out of room, teleport back into
                self.__Event.drones[0].pos = [self.__Event.Ref["r3"].pos[0]+(self.__Event.Ref["r3"].size[0]/2),self.__Event.Ref["r3"].pos[1]+(self.__Event.Ref["r3"].size[1]/2)]
                self.__Event.drones[0].stopNavigation()
        if self.tpart[0]==3: #Selecting drone 1
            if not self.currentDrone is None:
                if self.currentDrone.number!=1: #Deselect drone
                    self.scematic = True
                    if not self.currentDrone is None: #Drone active
                        self.currentDrone.selectControll(False,self.name) #Let drone free
                    self.currentDrone = None
                    self.__command.activeTab = len(self.__command.tabs)-1 #Goto the ships command line
                else:
                    self.tpart[0]+=1
                    self.tpart[3] = 0
        elif self.tpart[0]==4: #Navigate drone to first room
            RM = self.__Event.drones[0].findPosition()
            if type(RM)==self.__Event.getEnt("room"):
                if RM.number==2:
                    self.tpart[0]+=1
                    self.tpart[3] = 0
        elif self.tpart[0]==5: #Navigate drone to second room
            RM = self.__Event.drones[0].findPosition()
            if type(RM)==self.__Event.getEnt("room"):
                if RM.number==3:
                    self.tpart[0]+=1
                    self.tpart[3] = 0
        elif self.tpart[0]==6: #Gathering scrap
            RM = self.__Event.drones[0].findPosition()
            if RM!=self.__Event.Ref["r3"]: #Drone is out of room, teleprot back into
                self.__Event.drones[0].pos = [self.__Event.Ref["r3"].pos[0]+(self.__Event.Ref["r3"].size[0]/2),self.__Event.Ref["r3"].pos[1]+(self.__Event.Ref["r3"].size[1]/2)]
                self.__Event.drones[0].stopNavigation()
            else:
                ENTS = self.__Event.Ref["r3"].EntitiesInside()
                scrapCount = 0
                ScrapReferenceObject = self.__Event.getEnt("scrap")
                for a in ENTS:
                    scrapCount+=int(type(a)==ScrapReferenceObject)
                if scrapCount==3: #1 Scrap was gathered
                    self.tpart[0]+=1
                    self.tpart[3] = 0
        elif self.tpart[0]==7: #Gathering all scrap
            ENTS = self.__Event.Ref["r3"].EntitiesInside()
            scrapCount = 0
            ScrapReferenceObject = self.__Event.getEnt("scrap")
            for a in ENTS:
                scrapCount+=int(type(a)==ScrapReferenceObject)
            if scrapCount==0: #No more scrap in room
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==8: #Enter scematic view
            if self.currentDrone is None:
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==9:
            RM = self.__Event.drones[1].findPosition()
            if RM==self.__Event.Ref["r2"] and not self.__Event.drones[1].onPath(0):
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==10: #Check generator
            RM = self.__Event.drones[1].findPosition()
            if RM==self.__Event.Ref["r2"]:
                if RM.powered:
                    self.tpart[0]+=1
                    self.tpart[3] = 0
                    self.__scemPos = [-600,-400]
                    self.tpart[4] = [False]
        elif self.tpart[0]==11: #Open and close door
            if not self.__Event.Ref["d1"].settings["open"]:
                self.tpart[4][0] = True
            elif self.tpart[4][0]:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==12: #Awaiting motion command to be entered
            if self.__Event.Ref["r2"].SCAN!=0:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==13: #Navigate drone 1 to R2
            if self.__Event.drones[0].findPosition()==self.__Event.Ref["r2"]:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==14: #Close door behind the drone
            if not self.__Event.Ref["d1"].settings["open"]:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==15: #Awaitng motion scan
            if self.__Event.Ref["r2"].SCAN!=0:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==16: #Threat safe
            if self.__Event.Ref["r3"].SCAN==3 and not self.__Event.Ref["d3"].settings["open"]:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==17: #Inside r4
            if not self.currentDrone is None:
                if self.currentDrone.findPosition()==self.__Event.Ref["r4"]:
                    self.tpart[0]+=1
                    self.tpart[3] = 0
                    return 0
            for a in self.__Event.drones:
                if a.findPosition()==self.__Event.Ref["r4"]:
                    self.tpart[0]+=1
                    self.tpart[3] = 0
                    return 0
            if not self.currentDrone is None:
                if self.currentDrone.number!=1: #Deselect drone
                    self.scematic = True
                    if not self.currentDrone is None: #Drone active
                        self.currentDrone.selectControll(False,self.name) #Let drone free
                    self.currentDrone = None
                    self.__command.activeTab = len(self.__command.tabs)-1 #Goto the ships command line
        elif self.tpart[0]==18: #Gather everything in the room
            ENTS = self.__Event.Ref["r4"].EntitiesInside()
            scrapCount = 0
            ScrapReferenceObject = self.__Event.getEnt("scrap")
            FuelReferenceObject = self.__Event.getEnt("fuel")
            for a in ENTS:
                scrapCount+=int(type(a)==ScrapReferenceObject)
                if type(a)==FuelReferenceObject:
                    if not a.used:
                        scrapCount+=1
            if scrapCount==0: #No more scrap in room
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==19: #Naivgate drone 3 to R4
            if self.__Event.drones[2].findPosition()==self.__Event.Ref["r4"]:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==20: #Tow upgrade
            for a in self.__Event.drones[2].upgrades:
                if a.name=="tow":
                    if a.beingUsed():
                        self.tpart[0] += 1
                        self.tpart[3] = 0
                        break
            RM = self.__Event.drones[2].findPosition()
            if RM!=self.__Event.Ref["r4"]: #Drone is out of room, teleport back into
                self.__Event.drones[0].pos = [self.__Event.Ref["r4"].pos[0]+(self.__Event.Ref["r4"].size[0]/2),self.__Event.Ref["r4"].pos[1]+(self.__Event.Ref["r4"].size[1]/2)]
        elif self.tpart[0]==21: #Navigate drone 3 to R1
            if self.__Event.drones[2].findPosition()==self.__Event.Ref["r1"]:
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==22: #Navigate drone 3 to R4
            if self.__Event.drones[2].findPosition()==self.__Event.Ref["r4"]:
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==23: #Interface with interface
            for a in self.__Event.drones[2].upgrades:
                if a.name=="interface":
                    if a.beingUsed():
                        self.tpart[0] += 1
                        self.tpart[3] = 0
                        break
        elif self.tpart[0]==24: #Killed stuff
            if not self.__Event.Ref["swarm"][0].alive:
                self.__Event.Ref["interface"][0].alive = False
                self.tpart[0] += 1
                self.tpart[3] = 0
        elif self.tpart[0]==25: #Killed turret
            if not self.__Event.Ref["turret"][0].alive:
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==26: #Motion scanned
            if self.__Event.Ref["r6"].SCAN!=0 and self.__Event.drones[0].findPosition()==self.__Event.Ref["r4"]:
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==27: #Open d5 and wait
            if self.__Event.Ref["d5"].settings["open"]:
                self.tpart[0] += 1
                self.tpart[3] = 0
                self.tpart[4] = [time.time()+6]
        elif self.tpart[0]==28: #Waiting
            if time.time()>self.tpart[4][0]:
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==29: #Enter room
            if self.__Event.drones[0].findPosition()==self.__Event.Ref["r5"]:
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==30: #Swapping upgrades
            if len(self.force)!=0:
                self.tpart[0]+=1
                self.tpart[3] = 0
            RM = self.__Event.drones[0].findPosition()
            if RM!=self.__Event.Ref["r5"]: #Drone is out of room, teleport back into
                self.__Event.drones[0].pos = [self.__Event.Ref["r5"].pos[0]+(self.__Event.Ref["r5"].size[0]/2),self.__Event.Ref["r5"].pos[1]+(self.__Event.Ref["r5"].size[1]/2)]
                self.__Event.drones[0].stopNavigation()
        elif self.tpart[0]==31: #Swapped all upgrades
            for a in self.__Event.Ref["drone"]:
                if a.ID>0:
                    if len(a.upgrades)==0:
                        self.tpart[0]+=1
                        self.tpart[3] = 0
        elif self.tpart[0]==32: #Exit swap menu
            if len(self.force)==0:
                self.tpart[0]+=1
                self.tpart[3] = 0
        elif self.tpart[0]==33: #Tow disabled drone to R3
            for a in self.__Event.Ref["drone"]:
                if a.ID>0:
                    if a.findPosition()==self.__Event.Ref["r1"]:
                        self.tpart[0]+=1
                        self.tpart[3] = 0
        elif self.tpart[0]==34: #Exiting
            for a in self.__Event.drones:
                if a.findPosition()!=self.__Event.Ref["r1"]:
                    break
            else:
                self.tpart[0]+=1
                self.tpart[3] = 0
    def renderTutorial(self,surf): #Render tutorial overlay
        sx,sy = surf.get_size()
        T = None
        if self.tpart[0]==0: #Welcome screen
            tex = "Welcome to REMOTE, this is a strategy game set in a world full of derilic ships where the only way to survive is gather resources with your drones and progress through each ship"
            ps = [10,sy-10]
        elif self.tpart[0]==1: #Introduction to console tabs
            tex = "These tabs are for your individual drones and their upgrades. \nThe green bar is their health and the slanted text is their upgrades."
            ps = [sx/2.5,sy-CONSOLE_SIZE[1]-175]
            self.tpart[5] = [ [0,[sx-CONSOLE_SIZE[0]-25,sy-CONSOLE_SIZE[1]-175,CONSOLE_SIZE[0],160]],
                            [1,[sx-CONSOLE_SIZE[0]-25,sy-CONSOLE_SIZE[1]-175],[(sx/2.5)+20,sy-CONSOLE_SIZE[1]-175]],
                            [1,[(sx/2.5)+20,sy-CONSOLE_SIZE[1]-175],[(sx/2.5)+20,sy-CONSOLE_SIZE[1]-190]] ]
        elif self.tpart[0]==2: #Introduction to the command line interface
            tex = "This is the command line, use this to controll drones, upgrades and doors \nLets start by typing 'a1' to open/close the airlock we see on our screen"
            ps = [sx/2.5,sy-CONSOLE_SIZE[1]]
            T = "Type 'a1' and hit enter"
            self.tpart[2] = True
            self.tpart[5] = [ [0,[sx-CONSOLE_SIZE[0]-20,sy-CONSOLE_SIZE[1]-20,CONSOLE_SIZE[0],CONSOLE_SIZE[1]]] ]
        elif self.tpart[0]==3: #Request to go to a drone
            tex = "We are now ready to venture the ship, to manualy controll a drone simply press its number on your keyboard \nFor this example lets controll drone 1"
            ps = [10,sy-10]
            self.tpart[1] = True
            self.tpart[5] = []
            T = "Press 1 to controll drone 1"
        elif self.tpart[0]==4: #Tell drone controlls
            tex = "Use the arrow keys to move (or what ever keys you changed it to) \nLeft, right - Turn left and right \nUp, down - Move forward/backward \nNavigate the drone out the ship into the fisrt room"
            ps = [10,sy-10]
            T = "Navigate drone into first room"
        elif self.tpart[0]==5: #Scavange first room
            tex = "Objects that are in BLUE are entities you can interact with, but first lets find some scrap. \nIf there is no scrap in this room then head into the next room above"
            ps = [10,sy-10]
            T = "Navigate drone into second room"
        elif self.tpart[0]==6: #Gather scrap
            tex = "Looks like their scrap in this room, this is indicated by the yellow/orange icons. \nTo gather this scrap type 'gather' in console\n If the console gives you a hint while typing then hit TAB to auto complete!"
            ps = [10,sy-10]
            T = "Type 'gather' and hit return"
        elif self.tpart[0]==7: #Gather more scrap
            tex = "It can be annoying to have to type 'gather' again to gather more scrap! \nLuckily there is a shortcut, type 'gather all' to gather all scrap in the room your in"
            ps = [10,sy-10]
            T = "Type 'gather all' and hit return"
        elif self.tpart[0]==8: #Go into scematic view
            tex = "There are no more rooms to explore, lets head into scematic view to have a better view of the ship. \nYou can access the scematic view by pressing space"
            ps = [10,sy-10]
            T = "Press space to go into scematic view"
        elif self.tpart[0]==9: #Navigation command
            tex = "This is the scematic view, use the arrow keys (same as drones) to move around. \nWhen rooms have a white border it means that they are not powered. \nTo power a room you need a drone with a generator, if we look in the tabs we can see that drone 2 has a generator. \nWe could controll drone 2 and move it towards the generator but lets be lazy! \nType 'navigate 2 r2'"
            ps = [10,sy-10]
            self.tpart[1] = False
            T = "Type 'navigate 2 r2' and hit enter"
            self.tpart[5] = [ [0,[sx-CONSOLE_SIZE[0]+60,sy-CONSOLE_SIZE[1]-80,70,70]],
                            [1,[sx-CONSOLE_SIZE[0]+60,sy-CONSOLE_SIZE[1]-80],[20,sy-CONSOLE_SIZE[1]-80]],
                            [1,[20,sy-CONSOLE_SIZE[1]-80],[20,sy-30] ] ]
        elif self.tpart[0]==10: #Navigation command explained
            tex = "The navigate command takes the drone and the room you want to navigate it to seperated by two spaces, it will auto-pilot any drone you want to a room on the map. \nWe can specify a room by typing its label as shown by the centre of it. e.g. 'navigate 2 r1' \nNext, to use the generator upgrade type 'generator'"
            ps = [10,sy-10]
            self.tpart[5] = []
            T = "Type 'generator' and hit enter"
        elif self.tpart[0]==11: #Door controll
            tex = "We can now see more rooms and controll various parts of the ship. \nFor example, lets open/close a door, close D1 by typing 'd1' and open it again by typing 'd1' \nDo NOT open any other door for now"
            ps = [10,sy-10]
            T = "Type 'd1' and hit enter, then type again to close"
        elif self.tpart[0]==12: #Motion scan rooms
            tex = "Here's the trick, \nThere are monsters in some rooms and we do not know which ones they are in, when we first start a ship the first two rooms will be initialy safe. \nThankfully we can use the motion upgrade on drone 1, type 'motion' to turn the motion scanning on"
            ps = [sx/2.5,sy-CONSOLE_SIZE[1]]
            T = "Type 'motion' and hit enter"
        elif self.tpart[0]==13: #Motion command explination
            tex = "It looks like theres a threat in R4, this means we cannot go in there or our drone will be under attack! \nThis is shown by the red scan lines \nLets do some trickery, navigate drone 1 back into R2"
            ps = [sx/2.5,sy-CONSOLE_SIZE[1]]
            T = "Type 'navigate 1 r2' to navigate drone 1 to R2"
        elif self.tpart[0]==14: #Close door behind drone
            tex = "Notice how the motion scanning stops when we move the drone that is scanning, your drone must be still for you to scan rooms. \nNow lets close D1"
            ps = [10,sy-10]
            T = "Type 'd1' to close D1"
        elif self.tpart[0]==15: #Motion scan
            tex = "Motion Scan again"
            ps = [10,sy-10]
            T = "Type 'motion' to motion scan"
        elif self.tpart[0]==16: #The trickery
            tex = "Now here comes the trickery, lets open D3 and wait for the threat to go into R3 then close the door behind it."
            ps = [10,sy-10]
            T = "Open D3 and close it when the threat is in R3"
        elif self.tpart[0]==17: #Go inside safe room
            tex = "It is now safe to go in R4, open the door towards it and scavenge the room using drone 1 by pressing 1"
            ps = [10,sy-10]
            self.tpart[1] = True
            T = "Open D2 and scavenge the opposite room"
        elif self.tpart[0]==18: #Gather everything
            tex = "Like before, lets use the 'gather all' command to gather everything inside the room."
            ps = [10,sy-10]
            T = "Type 'gather all' to gather everything"
        elif self.tpart[0]==19: #Towing and fuel
            tex = "When gathering all scrap you will notice your drone will gather fuel from the fuel port (BLUE) and be paused for 1.5 seconds. \nFuel is used to go to new ships, if you have no fuel, you'r dead. \nThere is also a yellow box at the top of the room, this is a ship upgrade, if you tow it to your ship room (R1) it will be added to your inventory. \nDrone 3 has a tow upgade, navigate drone 3 to R4"
            ps = [10,sy-10]
            self.tpart[5] = [ [0,[sx-CONSOLE_SIZE[0]+140,sy-CONSOLE_SIZE[1]-80,70,70]],
                            [1,[sx-CONSOLE_SIZE[0]+140,sy-CONSOLE_SIZE[1]-80],[20,sy-CONSOLE_SIZE[1]-80]],
                            [1,[20,sy-CONSOLE_SIZE[1]-80],[20,sy-30] ] ]
            T = "Navigate drone 3 to R4"
        elif self.tpart[0]==20: #Towing
            tex = "To use the tow upgrade, type 'tow' and simular to scrap it will head towards the upgrade and tow it \nMake sure your on drone 3 before you do the command."
            self.tpart[5] = []
            ps = [sx/2.5,sy-CONSOLE_SIZE[1]]
            T = "Type 'tow' to activate the tow upgrade"
        elif self.tpart[0]==21: #Move new upgrade to R1
            tex = "Now we need to add the upgrade to our inventory when we exit the map, naivgate drone 3 back to R1"
            ps = [10,sy-10]
            T = "Naivgate drone 3 to R1"
        elif self.tpart[0]==22: #Navigate drone 3 back to R4
            tex = "It looks like theres an 'interface' in R4, this is the panel againsed the wall (blue). \nDrone 3 has an interface upgrade so it should be able to use this entity. \nNavigate drone 3 to r4 but remember to stop towing the upgrade before by typing 'tow' again"
            ps = [10,sy-10]
            T = "Stop towing, navigate drone 3 to R4"
        elif self.tpart[0]==23: #Drone 3 inside R4
            tex = "Type 'interface' to use the interface upgrade and interface with the interface!"
            ps = [sx/2.5,sy-CONSOLE_SIZE[1]]
            T = "Type 'interface' and hit enter"
        elif self.tpart[0]==24: #Interface commands:
            tex = "This interface has the ability to controll turret defences (as described in console). Turret defences are turrets in a room that will kill anything (including your drones) inside the room. We can see there one in R3 \nType 'defence' to turn defences on."
            ps = [10,sy-10]
            T = "Type 'defence' to turn ship defences on"
        elif self.tpart[0]==25: #Killed NPC
            tex = "As said in the console, the turret has just killed the threat inside the room. But the turret is still on so we can't go inside. \nIn this situation you woulld type 'defence' again and turn the defences off but lets say the interface your using died. \nHow can we go in there, well what we can do is destroy the turret in there, lets use the overload ship upgrade (ship upgrades are above the scematic view tab). \nType 'overload r3'"
            if not self.currentDrone is None:
                self.scematic = True
                if not self.currentDrone is None: #Drone active
                    self.currentDrone.selectControll(False,self.name) #Let drone free
                self.currentDrone = None
                self.__command.activeTab = len(self.__command.tabs)-1 #Goto the ships command line
            self.tpart[1] = False
            self.tpart[5] = [ [0,[sx-CONSOLE_SIZE[0]+220,sy-CONSOLE_SIZE[1]-80,70,70]],
                            [1,[sx-CONSOLE_SIZE[0]+220,sy-CONSOLE_SIZE[1]-80],[20,sy-CONSOLE_SIZE[1]-80]],
                            [1,[20,sy-CONSOLE_SIZE[1]-80],[20,sy-30] ] ]
            ps = [10,sy-10]
            T = "Type 'overload r3' to overload R3"
        elif self.tpart[0]==26: #Scavange more
            self.tpart[1] = True
            self.tpart[5] = []
            tex = "If you want you can now enter R3 becuase the threat is dead. \nThe overload upgrade can also destroy certain threat types although it will destroy anything electronic inside rooms (including your drones) \nBut we still have two more rooms to scavenge, use motion in R4 when your ready."
            ps = [10,sy-10]
            T = "Type 'motion' with drone 1 in R4"
        elif self.tpart[0]==27: #Incorrect scanning
            tex = "R5 scan lines are yellow, why is that? \nWell it means the room cannot be scanned so you might have to come to other stategies to solving this, \nLets open D5 and wait until somethis goes into R6."
            ps = [10,sy-10]
            T = "Open D5"
        elif self.tpart[0]==28:
            tex = ""
            ps = [-100,0]
        elif self.tpart[0]==29:
            tex = "It looks like nothing has came out so lets assume the room is safe, go ahead and enter R5"
            ps = [10,sy-10]
            T = "Open D4 and go into room using drone 1"
        elif self.tpart[0]==30: #Swapping
            tex = "You can see a disabled drone at the back of the room, disabled drones can be repaired to use for other ships and expand your drone fleet. They can also contain upgrades when you first find them. To use get its upgrades, type 'swap'"
            ps = [10,sy-10]
            T = "Type 'swap' to swap upgrades"
        elif self.tpart[0]==31: #Swapping upgrades
            tex = "In this menu you can use the arrow keys to swap upgrades, press enter to move the from one side to the next. \nMove all the upgrades from the disabled drone to drone 1"
            ps = [10,sy-200]
            T = "Transfer upgrade from disabled drone to drone 1"
        elif self.tpart[0]==32: #Exiting swap menu
            tex = "Press 'Esc' to exit the swap menu"
            ps = [10,sy-200]
            T = "Exit swap menu by pressing Esc"
        elif self.tpart[0]==33: #Tow drone
            tex = "You can tow disabled drones and add them to your inventory to be repaired for future use. Use drone 3 to tow the disabled drone back to R1"
            ps = [10,sy-10]
            self.tpart[5] = [ [0,[sx-CONSOLE_SIZE[0]+140,sy-CONSOLE_SIZE[1]-80,70,70]],
                            [1,[sx-CONSOLE_SIZE[0]+140,sy-CONSOLE_SIZE[1]-80],[20,sy-CONSOLE_SIZE[1]-80]],
                            [1,[20,sy-CONSOLE_SIZE[1]-80],[20,sy-30] ] ]
            T = "Navigate drone 3 to R5 and tow drone back to R1"
        elif self.tpart[0]==34: #Finilizing
            tex = "You can scavenge R6 if you want or leave now, once your done you can do a neat trick to quickly leave the ship. \nType 'navigate all r1' and it will navigate all drones to R1 (the ship room)"
            ps = [10,sy-10]
            self.tpart[5] = []
            T = "Type 'navigate all r1' and hit enter"
        elif self.tpart[0]==35:
            tex = "This concludes this tutorial! \nIn the game you will face different challenges and will have to work out stragegies to overcome them to progress. \nType 'exit' to leave the ship your connected to."
            ps = [10,sy-10]
            T = "Type 'exit' to exit the ship and tutorial"
        self.tpart[3] = ((self.tpart[3]*3)+ps[1])/4
        #Render hint box
        if T is None:
            self.renderHint(surf,tex,[ps[0],self.tpart[3]])
        else:
            self.renderHint(surf,tex,[ps[0],self.tpart[3]],T)
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
        if ID in self.__Event.IDLINK:
            self.__Event.IDLINK[ID].REQUEST_DELETE = True
    def __clientDock(self,TO): #Called by the server to dock to an airlock
        self.__Event.ship.dockTo(self.__Event.Ref[TO],True)
    def addCommands(self,tex,drone,flash,extr=-1): #Called by the server to add text to a command line
        if drone==-1: #Scematic view
            dr = len(self.__command.tabs)-1
        elif drone==-2: #All views
            for i in range(0,len(self.__Event.drones)+1):
                if tex!="":
                    self.putLine(tex,extr,flash,i)
                else:
                    self.putLine(extr[0],extr[1],flash,i)
            dr = -2
        else: #A drone command line
            dr = drone
        if dr!=-2:
            if tex!="":
                spl = tex.split("\n")
                for a in spl:
                    self.putLine(a,(255,255,255),flash,dr)
            if extr!=-1:
                spl = extr[0].split("\n")
                for a in spl:
                    self.putLine(a,extr[1],flash,dr)
    def __isKeyDown(self,key): #Returns true if the key is being held down
        if key in self.__HoldKeys: #Has the key been pressed before?
            return self.__HoldKeys[key]
        return False
    def goToDrone(self,number,print=True): #Goto a specific drone number view
        droneNums = {}
        if self.tutorial:
            if not self.tpart[1]: #Drone selecting is disabled
                return False
        for a in self.__Event.drones:
            droneNums[a.number] = a
        if not number in droneNums: #Drone doesen't exist
            if print:
                self.putLine("No such drone "+str(number),(255,255,0),False)
            return False
        else: #Drone exists
            if not self.currentDrone is None:
                self.currentDrone.selectControll(False,self.name) #Let previous drone free
            self.currentDrone = droneNums[number] #Set the current drone object to the one specified
            self.currentDrone.selectControll(True,self.name)
            self.__viewChangeEffect = time.time()+0.1
            self.scematic = False #Is not viewing in scematic view
            self.__command.activeTab = number-1 #Switch to the specific tab of the drone
            self.__UpdateRender = 0
            return True
    def putLine(self,tex,col,flash,Tab=None): #Adds a line to the current command line
        if Tab is None:
            TB = None
        elif type(Tab) != int:
            TB = Tab.number-1
        else:
            TB = Tab
        if TB is None: #Putput to all command lines
            for a in range(len(self.__command.tabs)):
                self.putLine(tex,col,flash,a)
            return None
        else:
            self.__command.replaceLast(tex,col,TB,flash)
        if TB is None:
            self.__command.addLine(self.name+">"+self.__typing,(255,255,255),False)
        else:
            self.__command.addLine(self.name+">"+self.__typing,(255,255,255),False,TB)
    def doCommand(self,command): #Does a command to the currently selected drone/ship
        if command=="":
            return 0
        self.__commands.append(command)
        if len(self.__commands)>COMMAND_HISTORY_LENGTH:
            self.__commands.pop(0)
        self.__commandSelect = 0
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
                spl = tex.split("\n")
                for a in spl:
                    self.__command.addLine(a,col)
            self.__command.addLine(">",(255,255,255))
    def __isAtStart(self,str1,str2): #Returns true/false if the string is at the start of the other string
        if len(str1)>len(str2):
            return False
        for i,a in enumerate(str1): #Find charicters that are the same
            if a!=str2[i]:
                return False
        return True
    def getAllCommands(self): #Returns all the possible commands that can be ran at the current time
        coms = []
        if self.currentDrone is None: #In scematic view
            for a in self.__Event.drones+[self.__Event.ship]: #Go through all drones and ship
                for upg in a.upgrades:
                    for b in upg.caller:
                        if not b in coms:
                            coms.append(b) #Add its commands to the list
        else:
            for upg in self.currentDrone.upgrades:
                for b in upg.caller:
                    if not b in coms:
                        coms.append(b) #Add its commands to the list
        return ["open","close","navigate","dock","swap","flag"]+coms+["pickup","info"]
    def getObjs(self,key): #Return all objects for the given key (used with COMPARAMS to get paramiters)
        res = []
        if key=="e": #Door or airlock
            res.append("all")
            DoorReferenceObject = self.getEnt("door")
            AirlockReferenceObject = self.getEnt("airlock")
            for a in self.__Event.Map:
                if type(a)==DoorReferenceObject or type(a)==AirlockReferenceObject:
                    if a.discovered:
                        res.append(a.reference())
        elif key=="T": #Text
            res.append("Text")
        elif key=="A": #Airlock
            AirlockReferenceObject = self.getEnt("airlock")
            for a in self.__Event.Map:
                if type(a)==AirlockReferenceObject:
                    if a.discovered:
                        res.append(a.reference())
        elif key=="R": #Room
            RoomReferenceObject = self.getEnt("room")
            for a in self.__Event.Map:
                if type(a)==RoomReferenceObject:
                    if a.discovered2:
                        res.append(a.reference())
        return res
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
                            if self.__isAtStart(self.__typing,b) and a.damage!=2: #Should show a hint?
                                self.__typingOut = self.__typing+b[len(self.__typing):].upper()
                                break
                        if self.__typingOut!="":
                            break
                    if self.__typingOut!="":
                        break
            else: #Search active drone for hints
                for a in self.currentDrone.upgrades: #Loop through all the drones upgades
                    for b in a.caller: #Loop throguh all the commands that can be called for this upgade
                        if self.__isAtStart(self.__typing,b) and a.damage!=2: #Should show a hint?
                            self.__typingOut = self.__typing+b[len(self.__typing):].upper()
                            break
                    if self.__typingOut!="":
                        break
            if self.__typingOut == "":
                self.__typingOut = self.__typing+""
    def __safeExit(self): #Safely exit
        ENTS = self.__Event.clean() #Unload the map and return all entities inside the ship room
        self.__Event.drones = []
        self.__LINK["drones"] = []
        DroneReferenceObject = self.getEnt("drone")
        ShipUpgradeReferenceObject = self.getEnt("ShipUpgrade")
        DeadDrones = [] #Stores dead drones (so if theres too many drones, dead drones will be dismantled first)
        for a in ENTS:
            if type(a)==DroneReferenceObject:
                if len(self.__LINK["drones"])>=self.__LINK["shipData"]["maxDrones"]: #Drone fleet is full
                    if len(self.__LINK["shipData"]["reserve"])>=self.__LINK["shipData"]["maxReserve"]: #Reserve fleet is full
                        print("TOO MANY DRONES, dismantling, sorry :(")
                        DeadDrones.append(a)
                    else:
                        if a.alive:
                            self.__LINK["shipData"]["reserve"].append(a)
                        else:
                            DeadDrones.append(a)
                else:
                    if a.alive:
                        self.__LINK["drones"].append(a)
                    else:
                        DeadDrones.append(a)
            elif type(a)==ShipUpgradeReferenceObject: #Entity is a ship upgrade
                if len(self.__LINK["shipData"]["shipUpgs"])<self.__LINK["shipData"]["maxShipUpgs"]: #Place upgrade in ship
                    self.__LINK["shipData"]["shipUpgs"].append([a.type,0,-1,0])
                elif len(self.__LINK["shipData"]["reserveUpgs"])!=self.__LINK["shipData"]["reserveMax"]: #Put upgrade in inventory
                    self.__LINK["shipData"]["reserveUpgs"].append([a.type,0,-1,0])
        for a in DeadDrones:
            if len(self.__LINK["drones"])>=self.__LINK["shipData"]["maxDrones"]: #Drone fleet is full
                if len(self.__LINK["shipData"]["reserve"])>=self.__LINK["shipData"]["maxReserve"]: #Reserve fleet is full
                    if a.alive:
                        self.__LINK["shipData"]["scrap"] += 12
                    else:
                        self.__LINK["shipData"]["scrap"] += 8
                else:
                    self.__LINK["shipData"]["reserve"].append(a)
            else:
                self.__LINK["drones"].append(a)
        for l in range(len(self.__LINK["drones"])): #Bubble sort the drones in order of their number
            for i,a in enumerate(self.__LINK["drones"][:-l]):
                if a.number > self.__LINK["drones"][i+1].number:
                    self.__LINK["drones"][i+1],self.__LINK["drones"][i]=self.__LINK["drones"][i],self.__LINK["drones"][i+1]
        I = 1
        for a in self.__LINK["drones"]:
            a.number = I+0
            I+=1
        for a in self.__LINK["drones"]:
            self.__extrInfo.append([a.settings["name"]+"'s upgrades:",(0,255,255)])
            for b in a.upgrades:
                if b.damage==1:
                    self.__extrInfo.append(["    "+b.name+" upgrade is deteriorating, brake prob = "+str(b.brakeprob)+"%",(255,255,0)])
                elif b.damage==2:
                    self.__extrInfo.append(["    "+b.name+" upgrade is destroyed",(255,0,0)])
        self.__extrInfo.append(["Ship's upgrades:",(0,255,255)])
        for b in self.__LINK["shipEnt"].upgrades:
            if b.damage==1:
                self.__extrInfo.append(["    "+b.name+" upgrade is deteriorating, brake prop = "+str(b.brakeprob)+"%",(255,255,0)])
            elif b.damage==2:
                self.__extrInfo.append(["    "+b.name+" upgrade is destroyed",(255,0,0)])
        self.__LINK["shipEnt"].unloadUpgrades()
        if self.__LINK["fuelCollected"]==0:
            self.__extrInfo.append(["You collected no fuel",(255,0,0)])
        else:
            self.__extrInfo.append(["You collected "+str(self.__LINK["fuelCollected"])+" fuel",(0,255,0)])
        if self.__LINK["scrapCollected"]==0:
            self.__extrInfo.append(["You collected no scrap",(255,0,0)])
        else:
            self.__extrInfo.append(["You collected "+str(self.__LINK["scrapCollected"])+" scrap",(0,255,0)])
    def loop(self,mouse,kBuf,lag): #Constant loop
        global start
        if self.__fail[0]: #Game has failed/connection failure
            for event in kBuf: #Loop for return button pressed
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.__Event.exit and not self.tutorial:
                            self.__LINK["loadScreen"]("shipSelect")
                        else:
                            self.__LINK["loadScreen"]("mainMenu")
            return 0
        if self.__LINK["backgroundStatic"]:
            self.__changeEffect[1]+=lag*4 #Used to alpha overlay
            if self.__changeEffect[1]>=OVERLAY_OPASITY: #Next overlay
                self.__changeEffect[1] = 0
                self.__changeEffect[0] = (self.__changeEffect[0]+1)%len(self.__cols)
        if self.__LINK["multi"]==1: #Is a client
            if self.__LINK["cli"].failConnect:
                self.__fail[0] = True
                self.__fail[4] = "Connection error: "+self.__LINK["cli"].errorReason
        if self.__loading[0] and self.__LINK["multi"]==1: #Loading and is a client
            self.__loading[3] = self.__LINK["cli"].getPercent()
            return 0
        if self.tutorial:
            self.nextTutorial(kBuf)
        if len(self.force)!=0: #A force function has taken over (e.g. swap menu)
            if len(self.force)!=self.__fChange: #Force has just started
                self.__fChange = len(self.force)
                for a in self.__HoldKeys: #Stop all holding keys
                    self.__HoldKeys[a] = False
            for a in self.force:
                a[1](mouse,kBuf,lag)
        else: #Run normaly
            self.__droneMove()
            if not self.__LINK["controller"] is None and self.__controllerMenu[0]==0: #Controller is present and not in menu
                if self.controller_key("x")!=self.__controllerChange["x"]: #Load menu
                    self.__controllerChange["x"] = self.controller_key("x")==True
                    if self.controller_key("x"): #Open command selecting menu
                        self.__controllerMenu[0] = 1
                        self.__controllerMenu[1] = [self.getAllCommands(),0,[],0]
                if self.controller_key("lt")!=self.__controllerChange["lt"]: #Previous drone
                    self.__controllerChange["lt"] = self.controller_key("lt")==True
                    if self.controller_key("lt") and len(self.__Event.drones)!=0:
                        if not self.currentDrone is None:
                            N = self.currentDrone.number-1
                            if N<1:
                                N = len(self.__command.tabs)-1
                            while not self.goToDrone(N,False) and N>1:
                                N-=1
                        else:
                            self.goToDrone(1)
                if self.controller_key("a")!=self.__controllerChange["a"]: #Quick open/close door/airlock
                    self.__controllerChange["a"] = self.controller_key("a")
                    if self.controller_key("a") and not self.__controllSelect is None:
                        self.__controllSelect.toggle()
                if self.controller_key("rt")!=self.__controllerChange["rt"]: #Next drone
                    self.__controllerChange["rt"] = self.controller_key("rt")==True
                    if self.controller_key("rt") and len(self.__Event.drones)!=0:
                        if not self.currentDrone is None:
                            N = self.currentDrone.number+1
                            if N>len(self.__command.tabs)-(len(self.__command.tabs)-len(self.__Event.drones)):
                                N = 1
                            while not self.goToDrone(N,False) and N<len(self.__command.tabs):
                                N+=1
                        else:
                            self.goToDrone(len(self.__Event.drones))
                if self.controller_key("y")!=self.__controllerChange["y"]: #Jump into scematic view
                    self.__controllerChange["y"] = self.controller_key("y")
                    if self.controller_key("y"):
                        self.scematic = True
                        if not self.currentDrone is None: #Drone active
                            self.currentDrone.selectControll(False,self.name) #Let drone free
                        self.currentDrone = None
                        self.__command.activeTab = len(self.__command.tabs)-1 #Goto the ships command line
            self.__fChange = 0
            for event in kBuf: #Loop through keyboard event loops
                if self.tutorial:
                    if not self.tpart[2]:
                        break
                if event.type == pygame.KEYDOWN:
                    self.__HoldKeys[event.key] = True
                    if event.key >= 48 and event.key <=57 and len(self.__typing)==0: #Key is a number
                        self.goToDrone(int(chr(event.key)))
                    elif event.key == pygame.K_SPACE and len(self.__typing)==0: #Exit out of scematic view
                        self.scematic = True
                        if not self.currentDrone is None: #Drone active
                            self.currentDrone.selectControll(False,self.name) #Let drone free
                        self.currentDrone = None
                        self.__command.activeTab = len(self.__command.tabs)-1 #Goto the ships command line
                    elif event.key >= 32 and event.key <= 126 and not event.key in [self.__LINK["controll"]["up"],self.__LINK["controll"]["down"],self.__LINK["controll"]["left"],self.__LINK["controll"]["right"]]: #A key was pressed down for typing
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
                        if self.__LINK["commandSelect"] and len(self.__typing)==0:
                            if self.__controllerMenu[0]!=1:
                                self.__controllerMenu[0] = 1
                                self.__controllerMenu[1] = [self.getAllCommands(),0,[],0]
                                self.__controllerChange["x"] = True
                        else:
                            self.doCommand(self.__typing)
                            self.__typing = ""
                            self.__typingOut = ""
                    elif event.key == pygame.K_UP and self.__isKeyDown(pygame.K_LCTRL):
                        self.__commandSelect += 1
                        if self.__commandSelect>=len(self.__commands):
                            self.__commandSelect = 0
                        self.__typing = self.__commands[-self.__commandSelect]+""
                        self.__hintTyping()
                    elif event.key == pygame.K_DOWN and self.__isKeyDown(pygame.K_LCTRL):
                        self.__commandSelect -= 1
                        if self.__commandSelect<1:
                            self.__commandSelect = len(self.__commands)
                        self.__typing = self.__commands[-self.__commandSelect]+""
                        self.__hintTyping()
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
        if self.__controllerMenu[0]!=0: #A menu is open
            if self.controller_key("b") or self.__isKeyDown(pygame.K_BACKSPACE): #Back button/exit button
                self.__controllerMenu[0] = 0
            if self.__controllerMenu[0]==1: #Command selecting
                if (self.controller_key("up") or self.__isKeyDown(self.__LINK["controll"]["up"]))!=self.__controllerChange["up"] or (time.time()>self.__controllHold and self.__controllHold!=-1):
                    self.__controllerChange["up"] = self.controller_key("up") or self.__isKeyDown(self.__LINK["controll"]["up"])
                    if self.controller_key("up") or self.__isKeyDown(self.__LINK["controll"]["up"]): #Up button
                        if len(self.__controllerMenu[1][2])==0: #Select previous command
                            self.__controllerMenu[1][1]-=1
                            if self.__controllerMenu[1][1]<0:
                                self.__controllerMenu[1][1]=len(self.__controllerMenu[1][0])-1
                        else: #Select previous paramiter
                            self.__controllerMenu[1][3]-=1
                            if self.__controllerMenu[1][3]<0:
                                self.__controllerMenu[1][3]=len(self.__controllerMenu[1][2])-1
                        if self.__controllHold==-1:
                            self.__controllHold = time.time()+0.3
                        else:
                            self.__controllHold = time.time()+0.1
                    elif not self.controller_key("down") and not self.__isKeyDown(self.__LINK["controll"]["down"]):
                        self.__controllHold = -1
                if (self.controller_key("down") or self.__isKeyDown(self.__LINK["controll"]["down"]))!=self.__controllerChange["down"] or (time.time()>self.__controllHold and self.__controllHold!=-1):
                    self.__controllerChange["down"] = self.controller_key("down") or self.__isKeyDown(self.__LINK["controll"]["down"])
                    if self.controller_key("down") or self.__isKeyDown(self.__LINK["controll"]["down"]): #Down button
                        if len(self.__controllerMenu[1][2])==0: #Select next command
                            self.__controllerMenu[1][1]+=1
                            if self.__controllerMenu[1][1]>=len(self.__controllerMenu[1][0]):
                                self.__controllerMenu[1][1]=0
                        else: #Select next paramiter
                            self.__controllerMenu[1][3]+=1
                            if self.__controllerMenu[1][3]>=len(self.__controllerMenu[1][2]):
                                self.__controllerMenu[1][3]=0
                        if self.__controllHold==-1:
                            self.__controllHold = time.time()+0.3
                        else:
                            self.__controllHold = time.time()+0.1
                    elif not self.controller_key("up") and not self.__isKeyDown(self.__LINK["controll"]["up"]):
                        self.__controllHold = -1
                if (self.controller_key("x") or self.__isKeyDown(pygame.K_RETURN))!=self.__controllerChange["x"]: #Execute/select button
                    self.__controllerChange["x"]=self.controller_key("x") or self.__isKeyDown(pygame.K_RETURN)
                    if self.controller_key("x") or self.__isKeyDown(pygame.K_RETURN):
                        PS = COMPARAMS[self.__controllerMenu[1][0][self.__controllerMenu[1][1]]]
                        if PS=="": #No paramiters given
                            self.doCommand(self.__controllerMenu[1][0][self.__controllerMenu[1][1]])
                            self.__controllerMenu[0]=0
                        elif len(self.__controllerMenu[1][2])!=0: #Paramiter selected
                            self.doCommand(self.__controllerMenu[1][0][self.__controllerMenu[1][1]]+" "+self.__controllerMenu[1][2][self.__controllerMenu[1][3]].lower())
                            self.__controllerMenu[0]=0
                        else: #Initilize paramiter selection
                            self.__controllerMenu[1][2] = self.getObjs(PS)
                            self.__controllerMenu[1][3] = 0
        elif self.scematic and not self.__isKeyDown(pygame.K_LCTRL) and len(self.force)==0 and self.__controllerMenu[0]==0: #Is currently in the scematic view
            #Move the scematic view if the arrow keys are being held or pressed.
            sx,sy = self.__LINK["main"].get_size()
            if self.__isKeyDown(self.__LINK["controll"]["up"]) or self.controller_key("up"):
                self.__scemPos[1] -= SCROLL_SPEED*lag
                if self.__scemPos[1]<self.__Event.mapSize[1]-400: #Hit limit on top side of screen
                    self.__scemPos[1] = self.__Event.mapSize[1]-400
            if self.__isKeyDown(self.__LINK["controll"]["down"]) or self.controller_key("down"):
                self.__scemPos[1] += SCROLL_SPEED*lag
                if self.__scemPos[1]>self.__Event.mapSize[2]-sy+400: #Hit limit on bottom side of screen
                    self.__scemPos[1] = self.__Event.mapSize[2]-sy+400
            if self.__isKeyDown(self.__LINK["controll"]["left"]) or self.controller_key("left"):
                self.__scemPos[0] -= SCROLL_SPEED*lag
                if self.__scemPos[0]<self.__Event.mapSize[0]-400: #Hit limit on left side of screen
                    self.__scemPos[0] = self.__Event.mapSize[0]-400
            if self.__isKeyDown(self.__LINK["controll"]["right"]) or self.controller_key("right"):
                self.__scemPos[0] += SCROLL_SPEED*lag
                if self.__scemPos[0]>self.__Event.mapSize[2]-sx+600: #Hit limit on right side of screen
                    self.__scemPos[0] = self.__Event.mapSize[2]-sx+600
        elif not self.currentDrone is None: #Move a drone the player is controlling
            if self.currentDrone.REQUEST_DELETE:
                if self.currentDrone in self.__Event.drones:
                    self.__Event.drones.remove(self.currentDrone)
                self.currentDrone.selectControll(False,self.name)
                self.currentDrone = None
                self.scematic = True
                self.__command.activeTab = len(self.__command.tabs)-1
                self.reloadCommandline()
            elif not self.__isKeyDown(pygame.K_LCTRL) and not self.__LINK["simpleMovement"] and len(self.force)==0 and self.__controllerMenu[0]==0:
                if not self.currentDrone.allowed: #Attempt to take controll as soon as the person using this drone stops controlling it.
                    self.currentDrone.selectControll(True,self.name)
                if self.__isKeyDown(self.__LINK["controll"]["up"]) or self.controller_key("up"):
                    self.currentDrone.go(lag)
                if self.__isKeyDown(self.__LINK["controll"]["down"]) or self.controller_key("down"):
                    self.currentDrone.go(-1*lag)
                if self.__isKeyDown(self.__LINK["controll"]["left"]) or self.controller_key("left"):
                    self.currentDrone.turn(lag*5)
                if self.__isKeyDown(self.__LINK["controll"]["right"]) or self.controller_key("right"):
                    self.currentDrone.turn(-5*lag)
            elif not self.__isKeyDown(pygame.K_LCTRL) and len(self.force)==0:
                mv = False
                if self.__isKeyDown(self.__LINK["controll"]["up"]) or self.controller_key("up"):
                    self.currentDrone.aimTo(0,lag*2)
                    mv = True
                if self.__isKeyDown(self.__LINK["controll"]["down"]) or self.controller_key("down"):
                    self.currentDrone.aimTo(180,lag*2)
                    mv = True
                if self.__isKeyDown(self.__LINK["controll"]["left"]) or self.controller_key("left"):
                    self.currentDrone.aimTo(90,lag*2)
                    mv = True
                if self.__isKeyDown(self.__LINK["controll"]["right"]) or self.controller_key("right"):
                    self.currentDrone.aimTo(270,lag*2)
                    mv = True
                if mv:
                    self.currentDrone.go(lag)
        if self.__Event.exit: #Game has ended due to user entering "exit"
            self.__fail[0] = True
            SCOR = self.__Event.getScore()
            self.__fail[4] = "Your score is "+str(SCOR)
            self.__LINK["shipData"]["maxScore"]+=SCOR
            self.__safeExit()
        if not self.__Event is None and self.__LINK["currentScreen"]==self:
            try:
                self.__Event.loop()
            except:
                self.__LINK["errorDisplay"]("Failed to simulate world tick")
                traceback.print_exc()
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
        self.__loading[4] = "Downloading map"
        self.__DOWNLOAD.append(LN) #Add the downloading map to the buffer
    def finishSYNC(self): #Finished downloading SYNC and possibly the map
        if len(self.__DOWNLOAD)!=0:
            print("Finished loading")
            file = open("maps/SERVER_MAP.map","wb")
            file.write(pickle.dumps(self.__DOWNLOAD))
            file.close()
            self.__loading[0] = False
            self.__DOWNLOAD = []
            self.open("SERVER_MAP.map")
            if self.__LINK["cli"].SYNC["V"]!=VERSION: #Version is different
                self.__fail[0] = True
                if self.__LINK["cli"].SYNC["V"]>VERSION: #Server is more updated
                    self.__fail[4] = "Server has a higher version than you, ("+str(self.__LINK["cli"].SYNC["V"])+")"
                else: #Client is more updated
                    self.__fail[4] = "You have a higher version than server, ("+str(self.__LINK["cli"].SYNC["V"])+")"
                self.__LINK["cli"].close()
    def open(self,name): #Opens a map
        if self.tutorial:
            name = "tutorial.map"
        self.__Event.open(name)
        self.__renderFunc.ents = self.__Event.Map
        self.__droneFeed.ents = self.__Event.Map
        self.__scemPos = [self.__Event.ship.pos[0]-(self.__LINK["reslution"][0]/4),self.__Event.ship.pos[1]-(self.__LINK["reslution"][1]/4)] #Start the scematic position at the ships position
        self.__command.activeTab = len(self.__Event.drones)
        for i,a in enumerate(self.__Event.drones):
            self.__command.tabs.insert(i,["DRONE-"+str(i+1),[[">",[255,255,255],False]],0,[],False,a])
        self.reloadCommandline()
        self.mapLoaded = True
        self.mapLoading = False
    def render(self,surf=None): #Render everything.
        if surf is None:
            surf = self.__LINK["main"]
        scale = ((self.__LINK["reslution"][0]/DEF_RES[0])+(self.__LINK["reslution"][1]/DEF_RES[1]))/2
        if self.__fail[0]: #Connection failure
            surf.blit(self.__fail[1],(self.__fail[2],0))
            #Error message
            fren = self.__LINK["font42"].render(self.__fail[4],16,(0,255,0))
            sx,sy = fren.get_size()
            pygame.draw.rect(surf,(0,0,0),[int(self.__fail[3][0]/2)-int(sx/2)-5,int(self.__fail[3][1]/2)-5,sx+10,sy+10])
            pygame.draw.rect(surf,(0,255,0),[int(self.__fail[3][0]/2)-int(sx/2)-5,int(self.__fail[3][1]/2)-5,sx+10,sy+10],2)
            surf.blit(fren,(int(self.__fail[3][0]/2)-int(sx/2),int(self.__fail[3][1]/2)))
            #'Press return to continue' sign at the bottom of the screen
            fren = self.__LINK["font42"].render("Press return to continue",16,(255,255,0))
            sx,sy = fren.get_size()
            pygame.draw.rect(surf,(0,0,0),[int(self.__fail[3][0]/2)-int(sx/2)-5,int(self.__fail[3][1]*0.8)-5,sx+10,sy+10])
            pygame.draw.rect(surf,(0,255,0),[int(self.__fail[3][0]/2)-int(sx/2)-5,int(self.__fail[3][1]*0.8)-5,sx+10,sy+10],2)
            surf.blit(fren,(int(self.__fail[3][0]/2)-int(sx/2),int(self.__fail[3][1]*0.8)))
            for i,a in enumerate(self.__extrInfo):
                surf.blit(self.__LINK["font24"].render(a[0],16,a[1]),[self.__fail[3][0]/8,(self.__fail[3][1]/8)+(i*30)])
        elif self.__loading[0]: #Loading screen
            surf.blit(self.__loading[1],(self.__loading[2],0))
            pygame.draw.rect(surf,(0,0,0),[50,int(self.__loading[5][1]*0.8),self.__loading[5][0]-100,40],4)
            pygame.draw.rect(surf,(0,0,0),[50,int(self.__loading[5][1]*0.8),self.__loading[5][0]-100,40])
            pygame.draw.rect(surf,(255,255,0),[49,int(self.__loading[5][1]*0.8)-1,self.__loading[5][0]-99,41],2)
            pygame.draw.rect(surf,(0,255,0),[50,int(self.__loading[5][1]*0.8),(self.__loading[5][0]-100)*self.__loading[3],40])
            fren = self.__LINK["font42"].render(self.__loading[4],16,(255,255,255))
            sx,sy = fren.get_size()
            surf.blit(fren,(int(self.__loading[5][0]/2)-int(sx/2),int(self.__loading[5][1]*0.8)+50))
        elif self.scematic: #Is inside the scematic view
            if self.__LINK["DEVDIS"]:
                self.__LINK["render"].drawDevMesh(self.__scemPos[0],self.__scemPos[1],0.8,surf,self.__LINK) #DEVELOPMENT
            self.__renderFunc.render(self.__scemPos[0],self.__scemPos[1],0.8,surf) #Render the map.
            if self.__LINK["backgroundStatic"]:
                sx,sy = surf.get_size()
                for y in range(0,int(sy/50)+1):
                    Y = (y*50)+random.randint(-3,3)-(self.__scemPos[1]%50)
                    for x in range(0,int(sx/50)+1):
                        surf.blit(self.__LINK["content"]["gradient"],(x*50,Y))
        elif not self.currentDrone is None:
            sx,sy = surf.get_size()
            drpos = [self.currentDrone.pos[0]*DRONE_VIEW_SCALE*scale,self.currentDrone.pos[1]*DRONE_VIEW_SCALE*scale] #Find the drones position in screen coordinates
            if self.__LINK["DEVDIS"]:
                self.__LINK["render"].drawDevMesh(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,surf,self.__LINK) #DEVELOPMENT
            self.__renderFunc.render(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,surf,True) #Render the map through drone view.
            self.__droneFeed.render(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,self.currentDrone.angle+90,self.currentDrone.findPosition(),self.currentDrone,surf) #Render map in 3D
            if self.__LINK["viewDistort"]:
                surf = self.__LINK["render"].distort(surf,int((1-(self.currentDrone.health/self.currentDrone.settings["maxHealth"]))*10*int(self.currentDrone.alive)),not self.currentDrone.alive)
                if self.__viewChangeEffect>time.time(): #Screen judder from drone change
                    surf = self.__LINK["render"].distort(surf,0,True)
            if not self.__controllSelect is None:
                pygame.draw.rect(surf,(0,255,0),[(self.__controllSelect.pos[0]*DRONE_VIEW_SCALE*scale)-(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale)),
                                                (self.__controllSelect.pos[1]*DRONE_VIEW_SCALE*scale)-(drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale)),
                                                self.__controllSelect.size[0]*DRONE_VIEW_SCALE*scale,self.__controllSelect.size[1]*DRONE_VIEW_SCALE*scale],12)
            if not self.currentDrone.allowed: #Drone is being controlled by anouther player
                fren = self.__LINK["font42"].render("Drone is being controlled by anouther player",16,(255,255,0))
                sx2,sy2 = fren.get_size()
                pygame.draw.rect(surf,(0,0,0),[int(sx/2)-int(sx2/2)-5,int(sy/4)-5,sx2+10,sy2+10])
                pygame.draw.rect(surf,(0,255,0),[int(sx/2)-int(sx2/2)-5,int(sy/4)-5,sx2+10,sy2+10],2)
                surf.blit(fren,(int(sx/2)-int(sx2/2),int(sy/4)))
            if not self.currentDrone.alive: #Display text saying the drone is disabled when the drone is disabled
                fren = self.__LINK["font42"].render("Drone is disabled",16,(255,0,0))
                sx2,sy2 = fren.get_size()
                pygame.draw.rect(surf,(0,0,0),[int(sx/2)-int(sx2/2)-5,int(sy/4)-5,sx2+10,sy2+10])
                pygame.draw.rect(surf,(0,255,0),[int(sx/2)-int(sx2/2)-5,int(sy/4)-5,sx2+10,sy2+10],2)
                surf.blit(fren,(int(sx/2)-int(sx2/2),int(sy/4)))
        if self.__LINK["DEVDIS"]:
            self.__LINK["render"].drawConnection(10,10,surf,self.__LINK)
        if not self.__loading[0] and not self.__fail[0]:
            sx,sy = surf.get_size()
            self.__command.render(self.__reslution[0]-CONSOLE_SIZE[0]-20,self.__reslution[1]-CONSOLE_SIZE[1]-20,CONSOLE_SIZE[0],CONSOLE_SIZE[1],surf) #Render command line
            if self.__typing!=self.__typingOut: #Hinting
                surf.blit(self.__LINK["font24"].render("Press TAB to auto complete",16,(0,0,255)),[sx-CONSOLE_SIZE[0],sy-20])
        for a in self.force: #Upgrade force menues
            a[2](surf,list(surf.get_size()))
        if self.tutorial:
            mult = abs(math.cos(time.time()*3)) #Box flashing
            for a in self.tpart[5]:
                if a[0]==0: #Rectangle
                    pygame.draw.rect(surf,(255*mult,255*mult,0),a[1],4)
                elif a[0]==1: #Line
                    pygame.draw.line(surf,(255*mult,255*mult,0),a[1],a[2],4)
            self.renderTutorial(surf)
        if self.__controllerMenu[0]!=0: #Render controller menu
            sx,sy = surf.get_size()
            if self.__controllerMenu[0]==1: #Command selecting menu
                WX,WY = sx-CONSOLE_SIZE[0],sy-CONSOLE_SIZE[1]
                mult = abs(math.cos(time.time()*3)) #Box flashing
                #Draw borders
                pygame.draw.rect(surf,(0,0,0),[WX,WY,CONSOLE_SIZE[0]-50,CONSOLE_SIZE[1]-50])
                pygame.draw.rect(surf,(0,255,0),[WX,WY,CONSOLE_SIZE[0]-50,CONSOLE_SIZE[1]-50],3)
                ADD = self.__controllerMenu[1][1]+0 #Text shifting on first column
                if ADD<int((CONSOLE_SIZE[1]-50)/15)/2:
                    ADD = 0
                    pygame.draw.rect(surf,(255*mult,255*mult,0),[WX+5,WY+(self.__controllerMenu[1][1]*15)+4,(CONSOLE_SIZE[0]-80)/2,15],2)
                else:
                    ADD -= (int(((CONSOLE_SIZE[1]-50)/15)/2))-1
                    pygame.draw.rect(surf,(255*mult,255*mult,0),[WX+5,WY+((CONSOLE_SIZE[1]-75)/2),(CONSOLE_SIZE[0]-80)/2,15],2)
                for i,a in enumerate(self.__controllerMenu[1][0][ADD:]): #Display all text on the first column
                    surf.blit(self.__LINK["font24"].render(a,16,(255,255,255)),[WX+5,WY+(i*15)])
                    if WY+(i*15)>sy-100:
                        break
                if len(self.__controllerMenu[1][2])!=0: #Second column is present
                    WX+=(CONSOLE_SIZE[0]-75)/2
                    ADD = self.__controllerMenu[1][3]+0
                    if ADD<int((CONSOLE_SIZE[1]-50)/15)/2:
                        ADD = 0
                        pygame.draw.rect(surf,(255*mult,255*mult,0),[WX+5,WY+(self.__controllerMenu[1][3]*15)+4,(CONSOLE_SIZE[0]-80)/2,15],2)
                    else:
                        ADD -= (int(((CONSOLE_SIZE[1]-50)/15)/2))-1
                        pygame.draw.rect(surf,(255*mult,255*mult,0),[WX+5,WY+((CONSOLE_SIZE[1]-75)/2),(CONSOLE_SIZE[0]-80)/2,15],2)
                    for i,a in enumerate(self.__controllerMenu[1][2][ADD:]): #Display all text on the second column
                        surf.blit(self.__LINK["font24"].render(a,16,(255,255,255)),[WX+5,WY+(i*15)])
                        if WY+(i*15)>sy-100:
                            break
        #Overlay
        if self.__LINK["backgroundStatic"]:
            self.__cols[self.__changeEffect[0]].set_alpha(OVERLAY_OPASITY-self.__changeEffect[1])
            self.__cols[(self.__changeEffect[0]+1)%len(self.__cols)].set_alpha(self.__changeEffect[1])
            surf.blit(self.__cols[self.__changeEffect[0]],(0,0))
            surf.blit(self.__cols[(self.__changeEffect[0]+1)%len(self.__cols)],(0,0))


