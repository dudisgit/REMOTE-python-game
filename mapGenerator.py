import math, sys, pickle, random, importlib, os, render

MESH_BLOCK_SIZE = 125 #Size of a single mesh block (game.py)
PRINT_INFO = False #Print generating infomation

def loadLINK(): #Loads all content (used for map generator)
    LINK = {} #This is a global variable for allowing controll over the whole program through one variable. Every class in this program should have a link to this!
    LINK["errorDisplay"] = print #Used to show errors
    LINK["reslution"] = [1000,700] #Reslution of the game
    LINK["DEV"] = False #Development mode, this will stop the game when errors occur.
    LINK["allPower"] = False #Cheat to enable power to all doors, used for development
    LINK["log"] = print #Used to log infomation (not seen in game unless developer console is turned on)
    LINK["mesh"] = {} #Used for fast entity discovery
    LINK["hints"] = False
    LINK["hintDone"] = []
    LINK["upgradeIDCount"] = 0 #Upgrade ID Count
    LINK["NPCignorePlayer"] = True #Used for development
    LINK["floorScrap"] = False #Enable/disable floor scrap
    LINK["absoluteDoorSync"] = False #Send packets randomly to make doors in SYNC perfectly (bigger the map the more packets)
    LINK["particles"] = False #Disable particle effects on server
    LINK["simpleModels"] = True #Simple models
    LINK["showRooms"] = False
    LINK["backgroundStatic"] = False #Enable/disable background static
    LINK["viewDistort"] = False #Drone view distortion
    LINK["names"] = ["Jeff","Tom","Nathon","Harry","Ben","Fred","Timmy","Potter","Stranger"] #Drone names
    LINK["multi"] = 2
    LINK["render"] = render
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
    LINK["drones"] = [] #Drone list of the players drones
    for i in range(0,3):
        LINK["drones"].append(LINK["ents"]["drone"].Main(i*60,0,LINK,-2-i,i+1))
    
    LINK["shipEnt"] = LINK["ents"]["ship"].Main(0,0,LINK,-1)
    return LINK

class FakeMapGenerator: #Used to hold map entities
    def __init__(self,LINK,fileName):
        self.ents = []
        self.__LINK = LINK
        file = open("maps/"+fileName,"rb")
        DT = pickle.loads(file.read())
        file.close()
        hold = None
        if "create" in LINK:
            hold,LINK["create"] = LINK["create"],self.__fakeCreate
        else:
            LINK["create"] = self.__fakeCreate
        IDS = {}
        for a in DT[1:]:
            self.ents.append(self.getEnt(a[0])(a[2][0],a[2][1],LINK,a[1]+0))
            IDS[a[1]+0] = self.ents[-1]
        for i,a in enumerate(DT[1:]):
            self.ents[i].LoadFile(a,IDS)
        LINK["create"] = hold
    def __fakeCreate(self,*params): #If an entity creates anouther, give back a fake one
        return self.__LINK["null"](0,0,self.__LINK,-12)
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]

class MapGenerator:
    def __init__(self,LINK,dificulty,saveName,roomsOnly=False):
        self.__saveName = saveName
        self.__dif = dificulty #1-10
        if LINK is None:
            self.__LINK = loadLINK()
        else:
            self.__LINK = LINK
        self.__roomsOnly = roomsOnly
        self.__IDCount = 1
        self.attackDoors = True
        self.ents = []
        self.Mesh = {}
        if PRINT_INFO:
            print("############### START #################")
        self.__generate()
        if PRINT_INFO:
            print("\t\tSAVING")
        self.__save()
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def __mapValid(self,ent=None): #Return true if the map is valid
        RoomReferenceObject = self.getEnt("room")
        if not ent is None:
            Ents = []
            for x in range(int(ent.pos[0]/MESH_BLOCK_SIZE)-1,int((ent.pos[0]+ent.size[0])/MESH_BLOCK_SIZE)+1):
                if x in self.Mesh:
                    for y in range(int(ent.pos[1]/MESH_BLOCK_SIZE)-1,int((ent.pos[1]+ent.size[1])/MESH_BLOCK_SIZE)+1):
                        if y in self.Mesh[x]:
                            for a in self.Mesh[x][y]:
                                if type(a)==RoomReferenceObject and not a.REQUEST_DELETE:
                                    if not a in Ents:
                                        Ents.append(a)
            for a in Ents:
                if not a.editMove(Ents):
                    return False
        else:
            for a in self.ents:
                if type(a)==RoomReferenceObject:
                    if not a.editMove(self.ents):
                        return False
        return True
    def __getAtPosition(self,x,y,includeRoom=True): #Returns what door/airlock/room this entity is in.
        pos = [x,y]
        size = [0,0]
        bsize = 1
        for x in range(int(pos[0]/MESH_BLOCK_SIZE)-bsize,int(pos[0]/MESH_BLOCK_SIZE)+int(size[0]/MESH_BLOCK_SIZE)+bsize): #Loop through a 3x3 square in MESH to find entities
            if x in self.Mesh: #X column exists
                for y in range(int(pos[1]/MESH_BLOCK_SIZE)-bsize,int(pos[1]/MESH_BLOCK_SIZE)+int(size[1]/MESH_BLOCK_SIZE)+bsize):
                    if y in self.Mesh[x]: #Y column exists
                        for ENT in self.Mesh[x][y]:
                            #Check if this entity is atall inside or touching the possible room/door/airlock
                            inside = (pos[0]>=ENT.pos[0] and pos[0]<=ENT.pos[0]+ENT.size[0] and pos[1]>=ENT.pos[1] and pos[1]<=ENT.pos[1]+ENT.size[1])
                            inside = inside or (pos[0]+size[0]>=ENT.pos[0] and pos[0]+size[0]<=ENT.pos[0]+ENT.size[0] and pos[1]>=ENT.pos[1] and pos[1]<=ENT.pos[1]+ENT.size[1])
                            inside = inside or (pos[0]+size[0]>=ENT.pos[0] and pos[0]+size[0]<=ENT.pos[0]+ENT.size[0] and pos[1]+size[1]>=ENT.pos[1] and pos[1]+size[1]<=ENT.pos[1]+ENT.size[1])
                            inside = inside or (pos[0]>=ENT.pos[0] and pos[0]<=ENT.pos[0]+ENT.size[0] and pos[1]+size[1]>=ENT.pos[1] and pos[1]+size[1]<=ENT.pos[1]+ENT.size[1])
                            if inside and not ENT.REQUEST_DELETE:
                                if not (type(ENT)==self.getEnt("room") and not includeRoom):
                                    return ENT
        return -1
    def __placeEnt(self,RM,ent,duplicate=False):
        if not duplicate:
            ents = RM.EntitiesInside() #RM.findInside(self.ents,[RM])
            for a in ents:
                if type(a)==self.getEnt(ent):
                    return a
        rpos = [round(random.randint(RM.pos[0],RM.pos[0]+RM.size[0]-26)/50)*50,round(random.randint(RM.pos[1],RM.pos[1]+RM.size[1]-26)/50)*50]
        if not self.__roomFull(RM):
            while self.__getAtPosition(rpos[0]+25,rpos[1]+25,False)!=-1:
                rpos = [round(random.randint(RM.pos[0],RM.pos[0]+RM.size[0]-26)/50)*50,round(random.randint(RM.pos[1],RM.pos[1]+RM.size[1]-26)/50)*50]
        self.ents.append(self.getEnt(ent)(rpos[0],rpos[1],self.__LINK,self.__IDCount))
        self.addToMesh(self.ents[-1])
        self.__IDCount+=1
        return self.ents[-1]
    def __roomFull(self,RM): #Returns true if a room is full
        for x in range(int(RM.size[0]/50)):
            for y in range(int(RM.size[1]/50)):
                if self.__getAtPosition(RM.pos[0]+(x*50)+25,RM.pos[1]+(y*50)+25,False)==-1:
                    return False
        return True
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
    def __generate(self): #Generate the map
        sizeX = random.randint(2,3)*50*self.__dif
        sizeY = random.randint(2,3)*50*self.__dif
        self.ents = []
        self.__LINK["mesh"] = self.Mesh
        Rooms = []
        RoomDoors = {}
        DoorRooms = {}
        if PRINT_INFO:
            print("\t\tGEN ROOM")
        #Room generation
        for x in range(int(sizeX/50)):
            for y in range(int(sizeY/50)):
                self.ents.append(self.getEnt("room")(x*50,y*50,self.__LINK,self.__IDCount) ) #Make new room
                self.ents[-1].size = [50*random.randint(1,2),50*random.randint(1,2)]
                while self.ents[-1].size[0]==50 and self.ents[-1].size[1]==50:
                    self.ents[-1].size = [50*random.randint(1,2),50*random.randint(1,2)]
                self.addToMesh(self.ents[-1])
                if not self.__mapValid(self.ents[-1]): #Room cannot exist
                    self.ents[-1].delete()
                    self.ents.pop().deleteMesh()
                else: #Room can exist
                    Rooms.append(self.ents[-1])
                    RoomDoors[self.ents[-1]] = []
                    self.ents[-1].deleteMesh()
                    self.ents[-1].size = [random.randint(1,min(8,int((sizeX-self.ents[-1].pos[0])/50)))*50,
                                            random.randint(1,min(8,int((sizeY-self.ents[-1].pos[1])/50)))*50] #Random size
                    self.addToMesh(self.ents[-1])
                    while not self.__mapValid(self.ents[-1]): #Keep generating random sizes until the minimum size is created
                        self.ents[-1].deleteMesh()
                        self.ents[-1].size = [random.randint(1,min(8,int((sizeX-self.ents[-1].pos[0])/50)))*50,
                                            random.randint(1,min(8,int((sizeY-self.ents[-1].pos[1])/50)))*50]
                        self.addToMesh(self.ents[-1])
                    self.__IDCount+=1
        if len(Rooms)<=2:
            self.__generate()
            return None
        #Door generation
        if PRINT_INFO:
            print("\t\tGEN DOORS")
        Done = []
        for a in Rooms:
            for x in range(int(a.size[0]/50)): #Doors accross the top side of a room
                PS = self.__getAtPosition(a.pos[0]+(x*50)+25,a.pos[1]-75)
                if type(PS)==self.getEnt("room"):
                    if not [a,PS] in Done and not [PS,a] in Done: #Door hasn't been created before
                        XP = (max(a.pos[0],PS.pos[0])+min(a.pos[0]+a.size[0],PS.pos[0]+PS.size[0]))/2
                        self.ents.append(self.getEnt("door")(int(XP/50)*50,a.pos[1]-50,self.__LINK,self.__IDCount))
                        self.ents[-1].editMove(self.ents,True)
                        self.addToMesh(self.ents[-1])
                        self.__IDCount+=1
                        RoomDoors[a].append(self.ents[-1])
                        RoomDoors[PS].append(self.ents[-1])
                        DoorRooms[self.ents[-1]] = [a,PS]
                        Done.append([a,PS])
            for y in range(int(a.size[1]/50)): #Doors accross the left side of a room
                PS = self.__getAtPosition(a.pos[0]-75,a.pos[1]+(y*50)+25)
                if type(PS)==self.getEnt("room"):
                    if not [a,PS] in Done and not [PS,a] in Done: #Door hasn't been created before
                        YP = (max(a.pos[1],PS.pos[1])+min(a.pos[1]+a.size[1],PS.pos[1]+PS.size[1]))/2
                        self.ents.append(self.getEnt("door")(a.pos[0]-50,int(YP/50)*50,self.__LINK,self.__IDCount))
                        self.ents[-1].editMove(self.ents,True)
                        self.addToMesh(self.ents[-1])
                        self.__IDCount+=1
                        RoomDoors[a].append(self.ents[-1])
                        RoomDoors[PS].append(self.ents[-1])
                        DoorRooms[self.ents[-1]] = [a,PS]
                        Done.append([a,PS])
        rem = []
        for a in Rooms:
            if len(RoomDoors[a])==0:
                a.delete()
                a.deleteMesh()
                rem.append(a)
                self.ents.remove(a)
        for a in rem:
            Rooms.remove(a)
        #Path planning (Hidden path the user should follow in the game)
        Path = []
        if PRINT_INFO:
            print("\t\t PATH PLAN")
        Starting = [] #Two starting rooms
        DIR = random.randint(0,3) #Direction of the starting room (left, right, up, down)
        #Select a random starting room according to random direction and also spawn an airlock
        if DIR==0: #Left
            sels = []
            for a in Rooms:
                if a.pos[0]==0 and len(RoomDoors[a])>1:
                    sels.append(a)
            if len(sels)==0:
                for a in Rooms:
                    if a.pos[0]==0:
                        sels.append(a)
            Starting.append(sels[random.randint(0,len(sels)-1)])
            self.ents.append(self.getEnt("airlock")(Starting[0].pos[0]-50,int(random.randint(Starting[0].pos[1],Starting[0].pos[1]+Starting[0].size[1]-10)/50)*50,self.__LINK,self.__IDCount))
        elif DIR==1: #Right
            Most = [-1,None]
            for a in Rooms:
                if (a.pos[0]+a.size[0]>Most[0] or Most[0]==-1) and len(RoomDoors[a])>=1:
                    Most = [a.pos[0]+a.size[0],a]
            if Most[1] is None:
                for a in Rooms:
                    if a.pos[0]+a.size[0]>Most[0] or Most[0]==-1:
                        Most = [a.pos[0]+a.size[0],a]
            Starting.append(Most[1])
            self.ents.append(self.getEnt("airlock")(Starting[0].pos[0]+Starting[0].size[0],int(random.randint(Starting[0].pos[1],Starting[0].pos[1]+Starting[0].size[1]-10)/50)*50,self.__LINK,self.__IDCount))
        elif DIR==2: #Top
            sels = []
            for a in Rooms:
                if a.pos[1]==0 and len(RoomDoors[a])>1:
                    sels.append(a)
            if len(sels)==0:
                for a in Rooms:
                    if a.pos[1]==0 :
                        sels.append(a)
            Starting.append(sels[random.randint(0,len(sels)-1)])
            self.ents.append(self.getEnt("airlock")(int(random.randint(Starting[0].pos[0],Starting[0].pos[0]+Starting[0].size[0]-10)/50)*50,Starting[0].pos[1]-50,self.__LINK,self.__IDCount))
        elif DIR==3: #Down
            Most = [-1,None]
            for a in Rooms:
                if (a.pos[1]+a.size[1]>Most[0] or Most[0]==-1) and len(RoomDoors[a])>=1:
                    Most = [a.pos[1]+a.size[1],a]
            if Most[1] is None:
                for a in Rooms:
                    if a.pos[1]+a.size[1]>Most[0] or Most[0]==-1:
                        Most = [a.pos[1]+a.size[1],a]
            Starting.append(Most[1])
            self.ents.append(self.getEnt("airlock")(int(random.randint(Starting[0].pos[0],Starting[0].pos[0]+Starting[0].size[0]-10)/50)*50,Starting[0].pos[1]+Starting[0].size[1],self.__LINK,self.__IDCount))
        else:
            print("NO DIR, ERR")
        self.__IDCount+=1
        self.ents[-1].settings["default"] = True #Make airlock the default one for docking
        self.ents[-1].editMove(self.ents)
        self.addToMesh(self.ents[-1])
        #Select a random secondary starting room
        sels = []
        for a in RoomDoors[Starting[0]]:
            RM = None
            if DoorRooms[a][0]==Starting[0]:
                RM = DoorRooms[a][1]
            else:
                RM = DoorRooms[a][0]
            if len(RoomDoors[RM])>1:
                sels.append(a)
        if len(sels)==0:
            for a in RoomDoors[Starting[0]]:
                sels.append(a)
            if len(sels)==0:
                self.__generate()
                return None
        RandomDoor = sels[random.randint(0,len(sels)-1)]
        RandomDoor.settings["open"] = True #Door between both starting rooms will be open
        if DoorRooms[RandomDoor][0]==Starting[0]:
            Starting.append(DoorRooms[RandomDoor][1])
        else:
            Starting.append(DoorRooms[RandomDoor][0])
        RoomDoors[Starting[0]].append(self.ents[-1])
        Path.append(Starting[1])
        if self.__roomsOnly:
            return None
        #Generate user path
        ThreatRoom = []
        Path = self.__figurePath(Path,RoomDoors,DoorRooms,Starting)
        if PRINT_INFO:
            print("\t\tPLAN THREATS")
        #Plan room threats
        for i,a in enumerate(Path[2:]):
            if random.randint(0,10)<self.__dif and not a in Starting:
                selfIndex = Path.index(a)
                strat = random.randint(1,5) #Strategy
                threat = ["android","swarm","brute"][random.randint(0,2)]
                Empty = None
                DoorTo = None
                ThreatRoom.append(a)
                for b in RoomDoors[a]: #Check if this room has a room next to it that threats can go into.
                    RM = None
                    if b == DoorRooms[b][0]==a:
                        RM = DoorRooms[b][1]
                    else:
                        RM = DoorRooms[b][0]
                    if not RM in Starting: #Room is not a starting room
                        if Path.index(RM)>selfIndex:
                            Empty = RM
                            DoorTo = b
                            break
                if strat==1: #Move threat to secondary room
                    if not Empty is None:
                        self.ents.append(self.getEnt(threat)(a.pos[0]+(int((a.size[0]-10)/50)*50),a.pos[1]+(int((a.size[1]-10)/50)*50),self.__LINK,self.__IDCount))
                        self.__IDCount+=1
                elif strat==2: #Close threat behind an open door between two rooms.
                    if not Empty is None:
                        self.ents.append(self.getEnt(threat)(a.pos[0]+(int((a.size[0]-10)/100)*50),a.pos[1]+(int((a.size[1]-10)/100)*50),self.__LINK,self.__IDCount))
                        self.__IDCount+=1
                        DoorTo.settings["open"] = True
                elif strat==3: #Airlock to outside
                    if a.pos[0]==0 or a.pos[1]==0:
                        if a.pos[0]==0:
                            self.ents.append(self.getEnt("airlock")(-50,a.pos[1]+(int((a.size[1]-10)/50)*50),self.__LINK,self.__IDCount))
                            self.__IDCount+=1
                        else:
                            self.ents.append(self.getEnt("airlock")(a.pos[0]+(int((a.size[0]-10)/50)*50),-50,self.__LINK,self.__IDCount))
                            self.__IDCount+=1
                        self.ents[-1].editMove(self.ents)
                        self.ents[-1].settings["fail"] = random.randint(0,5)==1 #20% chance of the airlock failing
                        RoomDoors[a].append(self.ents[-1])
                        if random.randint(0,1)==1: #50 percent chance that a threat is in the room with an airlock
                            self.ents.append(self.getEnt(threat)(a.pos[0]+(int((a.size[0]-10)/50)*50),a.pos[1]+(int((a.size[1]-10)/50)*50),self.__LINK,self.__IDCount))
                            self.__IDCount+=1
                elif strat==4: #Turret defence
                    if not Empty is None:
                        if (Empty.size[0]>50 or Empty.size[1]>50) and (a.size[0]>50 or a.size[1])>50:
                            Interface = self.__placeEnt(Empty,"interface")
                            Interface.settings["god"] = random.randint(0,1)
                            Turret = self.__placeEnt(a,"turret")
                            Turret.settings["inter"].append(Interface)
                            if random.randint(0,1)==1: #50% chance a threat will be in the room with a defence
                                self.ents.append(self.getEnt(threat)(a.pos[0]+(int((a.size[0]-10)/50)*50),a.pos[1]+(int((a.size[1]-10)/50)*50),self.__LINK,self.__IDCount))
                                self.__IDCount+=1
                elif strat==5: #Radiation leak
                    a.settings["radiation"] = True
                if random.randint(0,5)==1 and self.ents[-1].isNPC: #Percentage chance the NPC will attack doors
                    if type(self.ents[-1])!=self.getEnt("android"):
                        self.ents[-1].settings["attack"] = self.attackDoors
                if type(self.ents[-1]) == self.getEnt("swarm"):
                    if random.randint(0,3)==1 and not self.__roomFull(a) and not a in Starting: #14% chance of their being a vent
                        self.__placeEnt(a,"vent")
                self.addToMesh(self.ents[-1])
        if PRINT_INFO:
            print("\t\tGEN PLACEMENT")
        #Generator placement
        gen = self.__placeEnt(Starting[0],"generator")
        gen.settings["god"] = random.randint(0,1) #50% chance the generator is indestructable
        genLengs = [[gen,0]]
        Starting[0].settings["power"].append(gen)
        curGen = gen
        for a in Path: #Go through every room, create new generators, link paths of rooms to previous generators and calculate distances
            if random.randint(0,20)==1: #5% chance of creating a new generator
                a.settings["power"].append(curGen)
                curGen = self.__placeEnt(a,"generator")
                curGen.settings["god"] = random.randint(0,1) #50% chance the generator is indestructable
                genLengs.append([curGen,0])
            a.settings["power"].append(curGen)
            calc = math.sqrt( (((a.pos[0]+(a.size[0]/2))-curGen.pos[0])**2) + (((a.pos[1]+(a.size[1]/2))-curGen.pos[1])**2) )
            if calc>genLengs[-1][1]:
                genLengs[-1][1] = calc+0
        if PRINT_INFO:
            print("\t\t\tCONNECTING ROOMS TO GENS")
        for a in Rooms: #Make all rooms near a generator be powered by it due to its maximum reach when creating new generators
            for b in genLengs:
                if math.sqrt( (((a.pos[0]+(a.size[0]/2))-b[0].pos[0])**2) + (((a.pos[1]+(a.size[1]/2))-b[0].pos[1])**2) )<b[1]:
                    if not b[0] in a.settings["power"]:
                        a.settings["power"].append(b[0])
        AirlockReferenceObject = self.getEnt("airlock")
        InterfaceReferenceObject = self.getEnt("interface")
        TurretReferenceObject = self.getEnt("turret")
        for a in Rooms: #Link all airlocks to their room
            for b in RoomDoors[a]:
                if type(b)==AirlockReferenceObject:
                    b.settings["power"] = a.settings["power"]
            Ents = a.EntitiesInside()
            for b in Ents:
                if type(b)==InterfaceReferenceObject or type(b)==TurretReferenceObject:
                    b.settings["power"] = a.settings["power"]
        if PRINT_INFO:
            print("\t\tSCRAP, UPG, VENT PLACEMENT")
        #Scrap, ship upgrades and vent plotting.
        for a in Rooms:
            if a.size[0]>50 and a.size[1]>50:
                if a in ThreatRoom:
                    for i in range(random.randint(2,8)): #Put scrap inside the room
                        if self.__roomFull(a):
                            break
                        self.__placeEnt(a,"scrap",True)
                else:
                    for i in range(random.randint(0,2)): #Put scrap inside the room
                        if self.__roomFull(a):
                            break
                        self.__placeEnt(a,"scrap",True)
                if random.randint(0,10)==1 and not self.__roomFull(a): #10% chance of their being a ship upgrade
                    self.__placeEnt(a,"upgrade slot")
                    upgs = ["Empty"]+list(self.__LINK["shipUp"])
                    self.ents[-1].settings["upgrade"] = upgs[random.randint(0,len(upgs)-1)]
                    self.ents[-1].settings["perm"] = random.randint(0,5)==1 #20% chance the upgrade is perminant
                if random.randint(0,10)==1 and not self.__roomFull(a): #10% chance of their being an interface
                    inter = self.__placeEnt(a,"interface")
                    inter.settings["power"] = a.settings["power"]
                    inter.settings["scan"] = True
                    inter.settings["god"] = random.randint(0,1) #50% chance the interface is indestructable
                if random.randint(0,7)==1 and not self.__roomFull(a) and not a in Starting: #14% chance of their being a vent
                    self.__placeEnt(a,"vent")
                if random.randint(0,10)==1 and not self.__roomFull(a): #10% chance of their being a drone
                    drone = self.__placeEnt(a,"drone")
                    adding = [""]
                    for a in self.__LINK["upgrade"]: #Get list of upgrades to add to a drone
                        if not a in ["base","swap","pickup","info"]:
                            adding.append(a)
                    tR = random.randint(3,4)
                    if tR==4:
                        drone.settings["upgrades"].append(["",0,-1])
                    for i in range(tR):
                        drone.settings["upgrades"][i][0] = adding[random.randint(0,len(adding)-1)]
                        if drone.settings["upgrades"][i][0]!="":
                            drone.settings["upgrades"][i][1] = random.randint(0,2)
                    if random.randint(0,2)==1: #33% chance the drone is perminantly disabled
                        drone.settings["health"]=0
        if not self.__roomFull(Path[-1]): #Place a fuel port at the end of the path
            self.__placeEnt(Path[-1],"fuel")
    def __figurePath(self,Paths,RoomDoors,DoorRooms,ignore=[]): #Used to figure out a hidden path for the player to take
        curDoor = [Paths[-1]]
        while len(curDoor)!=0:
            DR = curDoor.pop()
            for a in RoomDoors[DR]: #Gather doors that the player can go through and havn't been looked at before
                RM = None
                if DoorRooms[a][0]==DR:
                    RM = DoorRooms[a][1]
                else:
                    RM = DoorRooms[a][0]
                if not RM in Paths and not RM in ignore and not RM in curDoor:
                    Paths.append(RM)
                    curDoor.append(RM)
        """for a in sels: #Go through each door thats allowed
            if not a in Paths: #Check if its still allowed (might be changed due to recursion)
                Paths.append(a)
                Paths = self.__figurePath(Paths,RoomDoors,DoorRooms,ignore)"""
        return Paths
    def __save(self): #Save the generated map
        build = [self.__IDCount+0]
        for a in self.ents:
            try:
                build.append(a.SaveFile())
            except:
                self.__LINK["errorDisplay"]("Error when saving entitiy ",a,sys.exc_info())
        file = open("maps/"+self.__saveName,"wb")
        file.write(pickle.dumps(build))
        file.close()
