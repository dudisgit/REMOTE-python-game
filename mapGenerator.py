import math, sys, pickle, random, importlib, os, render

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
        self.__ents = []
        self.__generate()
        self.__save()
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def __mapValid(self): #Return true if the map is valid
        RoomReferenceObject = self.getEnt("room")
        for a in self.__ents:
            if type(a)==RoomReferenceObject:
                if not a.editMove(self.__ents):
                    return False
        return True
    def __getAtPosition(self,x,y,includeRoom=True): #Returns the entity at the position
        for a in self.__ents:
            if x>a.pos[0] and y>a.pos[1] and x<a.pos[0]+a.size[0] and y<a.pos[1]+a.size[1] and not (type(a)==self.getEnt("room") and not includeRoom):
                return a
        return -1
    def __placeEnt(self,RM,ent,duplicate=False):
        if not duplicate:
            ents = RM.findInside(self.__ents,[RM])
            for a in ents:
                if type(a)==self.getEnt(ent):
                    return a
        rpos = [int(random.randint(RM.pos[0],RM.pos[0]+RM.size[0]-10)/50)*50,int(random.randint(RM.pos[1],RM.pos[1]+RM.size[1]-10)/50)*50]
        while self.__getAtPosition(rpos[0]+25,rpos[1]+25,False)!=-1:
            rpos = [int(random.randint(RM.pos[0],RM.pos[0]+RM.size[0]-10)/50)*50,int(random.randint(RM.pos[1],RM.pos[1]+RM.size[1]-10)/50)*50]
        self.__ents.append(self.getEnt(ent)(rpos[0],rpos[1],self.__LINK,self.__IDCount))
        self.__IDCount+=1
        return self.__ents[-1]
    def __roomFull(self,RM): #Returns true if a room is full
        for x in range(int(RM.size[0]/50)):
            for y in range(int(RM.size[1]/50)):
                if self.__getAtPosition(RM.pos[0]+(x*50)+25,RM.pos[1]+(y*50)+25,False)==-1:
                    return False
        return True
    def __generate(self): #Generate the map
        sizeX = random.randint(2,3)*50*self.__dif
        sizeY = random.randint(2,3)*50*self.__dif
        self.__ents = []
        Rooms = []
        RoomDoors = {}
        DoorRooms = {}
        #Room generation
        for x in range(int(sizeX/50)):
            for y in range(int(sizeY/50)):
                self.__ents.append(self.getEnt("room")(x*50,y*50,self.__LINK,self.__IDCount) ) #Make new room
                self.__ents[-1].size = [50*random.randint(1,2),50*random.randint(1,2)]
                while self.__ents[-1].size[0]==50 and self.__ents[-1].size[1]==50:
                    self.__ents[-1].size = [50*random.randint(1,2),50*random.randint(1,2)]
                if not self.__mapValid(): #Room cannot exist
                    self.__ents.pop()
                else: #Room can exist
                    Rooms.append(self.__ents[-1])
                    RoomDoors[self.__ents[-1]] = []
                    self.__ents[-1].size = [random.randint(1,min(8,int((sizeX-self.__ents[-1].pos[0])/50)))*50,
                                            random.randint(1,min(8,int((sizeY-self.__ents[-1].pos[1])/50)))*50] #Random size
                    while not self.__mapValid(): #Keep generating random sizes until the minimum size is created
                        self.__ents[-1].size = [random.randint(1,min(8,int((sizeX-self.__ents[-1].pos[0])/50)))*50,
                                            random.randint(1,min(8,int((sizeY-self.__ents[-1].pos[1])/50)))*50]
                    self.__IDCount+=1
        if len(Rooms)<=2:
            self.__generate()
            return None
        #Door generation
        Done = []
        for a in Rooms:
            for x in range(int(a.size[0]/50)): #Doors accross the top side of a room
                if type(self.__getAtPosition(a.pos[0]+(x*50)+25,a.pos[1]-75))==self.getEnt("room"):
                    PS = self.__getAtPosition(a.pos[0]+(x*50)+25,a.pos[1]-75)
                    if not [a,PS] in Done and not [PS,a] in Done: #Door hasn't been created before
                        XP = (max(a.pos[0],PS.pos[0])+min(a.pos[0]+a.size[0],PS.pos[0]+PS.size[0]))/2
                        self.__ents.append(self.getEnt("door")(int(XP/50)*50,a.pos[1]-50,self.__LINK,self.__IDCount))
                        self.__ents[-1].editMove(self.__ents)
                        self.__IDCount+=1
                        RoomDoors[a].append(self.__ents[-1])
                        RoomDoors[PS].append(self.__ents[-1])
                        DoorRooms[self.__ents[-1]] = [a,PS]
                        Done.append([a,PS])
            for y in range(int(a.size[1]/50)): #Doors accross the left side of a room
                if type(self.__getAtPosition(a.pos[0]-75,a.pos[1]+(y*50)+25))==self.getEnt("room"):
                    PS = self.__getAtPosition(a.pos[0]-75,a.pos[1]+(y*50)+25)
                    if not [a,PS] in Done and not [PS,a] in Done: #Door hasn't been created before
                        YP = (max(a.pos[1],PS.pos[1])+min(a.pos[1]+a.size[1],PS.pos[1]+PS.size[1]))/2
                        self.__ents.append(self.getEnt("door")(a.pos[0]-50,int(YP/50)*50,self.__LINK,self.__IDCount))
                        self.__ents[-1].editMove(self.__ents)
                        self.__IDCount+=1
                        RoomDoors[a].append(self.__ents[-1])
                        RoomDoors[PS].append(self.__ents[-1])
                        DoorRooms[self.__ents[-1]] = [a,PS]
                        Done.append([a,PS])
        #Path planning (Hidden path the user should follow in the game)
        Path = []
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
                    if a.pos[0]==0 :
                        sels.append(a)
            Starting.append(sels[random.randint(0,len(sels)-1)])
            self.__ents.append(self.getEnt("airlock")(Starting[0].pos[0]-50,int(random.randint(Starting[0].pos[1],Starting[0].pos[1]+Starting[0].size[1]-10)/50)*50,self.__LINK,self.__IDCount))
        elif DIR==1: #Right
            Most = [-1,None]
            for a in Rooms:
                if (a.pos[0]+a.size[0]>Most[0] or Most[0]==-1) and len(RoomDoors[a])>1:
                    Most = [a.pos[0]+a.size[0],a]
            if Most[1] is None:
                for a in Rooms:
                    if a.pos[0]+a.size[0]>Most[0] or Most[0]==-1:
                        Most = [a.pos[0]+a.size[0],a]
            Starting.append(Most[1])
            self.__ents.append(self.getEnt("airlock")(Starting[0].pos[0]+Starting[0].size[0],int(random.randint(Starting[0].pos[1],Starting[0].pos[1]+Starting[0].size[1]-10)/50)*50,self.__LINK,self.__IDCount))
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
            self.__ents.append(self.getEnt("airlock")(int(random.randint(Starting[0].pos[0],Starting[0].pos[0]+Starting[0].size[0]-10)/50)*50,Starting[0].pos[1]-50,self.__LINK,self.__IDCount))
        elif DIR==3: #Down
            Most = [-1,None]
            for a in Rooms:
                if (a.pos[1]+a.size[1]>Most[0] or Most[0]==-1) and len(RoomDoors[a])>1:
                    Most = [a.pos[1]+a.size[1],a]
            if Most[1] is None:
                for a in Rooms:
                    if a.pos[1]+a.size[1]>Most[0] or Most[0]==-1:
                        Most = [a.pos[1]+a.size[1],a]
            Starting.append(Most[1])
            self.__ents.append(self.getEnt("airlock")(int(random.randint(Starting[0].pos[0],Starting[0].pos[0]+Starting[0].size[0]-10)/50)*50,Starting[0].pos[1]+Starting[0].size[1],self.__LINK,self.__IDCount))
        else:
            print("NO DIR, ERR")
        self.__IDCount+=1
        self.__ents[-1].settings["default"] = True #Make airlock the default one for docking
        self.__ents[-1].editMove(self.__ents)
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
        RoomDoors[Starting[0]].append(self.__ents[-1])
        Path.append(Starting[1])
        if self.__roomsOnly:
            return None
        #Generate user path
        Path = self.__figurePath(Path,RoomDoors,DoorRooms,Starting)
        #Plan room threats
        for i,a in enumerate(Path[1:]):
            if random.randint(0,10)<self.__dif and random.randint(1,2)==2:
                selfIndex = Path.index(a)
                strat = random.randint(1,4) #Strategy
                threat = ["android","swarm","brute"][random.randint(0,2)]
                Empty = None
                DoorTo = None
                for b in RoomDoors[a]: #Check if this room has a room text to it that threats can go into.
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
                        self.__ents.append(self.getEnt(threat)(a.pos[0]+(int(a.size[0]/100)*50),a.pos[1]+(int(a.size[1]/100)*50),self.__LINK,self.__IDCount))
                        self.__IDCount+=1
                elif strat==2: #Close threat behind an open door between two rooms.
                    if not Empty is None:
                        self.__ents.append(self.getEnt(threat)(a.pos[0]+(int(a.size[0]/100)*50),a.pos[1]+(int(a.size[1]/100)*50),self.__LINK,self.__IDCount))
                        self.__IDCount+=1
                        b.settings["open"] = True
                elif strat==3: #Airlock to outside
                    if a.pos[0]==0 or a.pos[1]==0:
                        if a.pos[0]==0:
                            self.__ents.append(self.getEnt("airlock")(-50,a.pos[1]+(int(a.size[1]/100)*50),self.__LINK,self.__IDCount))
                            self.__IDCount+=1
                        else:
                            self.__ents.append(self.getEnt("airlock")(a.pos[0]+(int(a.size[0]/100)*50),-50,self.__LINK,self.__IDCount))
                            self.__IDCount+=1
                        self.__ents[-1].editMove(self.__ents)
                        RoomDoors[a].append(self.__ents[-1])
                        if random.randint(0,1)==1: #50 percent chance that a threat is in the room with an airlock
                            self.__ents.append(self.getEnt(threat)(a.pos[0]+(int(a.size[0]/100)*50),a.pos[1]+(int(a.size[1]/100)*50),self.__LINK,self.__IDCount))
                            self.__IDCount+=1
                elif strat==4: #Turret defence
                    if not Empty is None:
                        if (Empty.size[0]>50 or Empty.size[1]>50) and (a.size[0]>50 or a.size[1])>50:
                            Interface = self.__placeEnt(Empty,"interface")
                            Interface.settings["god"] = random.randint(0,1)
                            Turret = self.__placeEnt(a,"turret")
                            Turret.settings["inter"].append(Interface)
                            if random.randint(0,1)==1: #50% chance a threat will be in the room with a defence
                                self.__ents.append(self.getEnt(threat)(a.pos[0]+(int(a.size[0]/100)*50),a.pos[1]+(int(a.size[1]/100)*50),self.__LINK,self.__IDCount))
                                self.__IDCount+=1
                if random.randint(0,5)==1 and self.__ents[-1].isNPC: #Percentage chance the NPC will attack doors
                    if type(self.__ents[-1])!=self.getEnt("android"):
                        self.__ents[-1].settings["attack"] = self.attackDoors
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
            Ents = a.findInside(self.__ents)
            for b in Ents:
                if type(b)==InterfaceReferenceObject or type(b)==TurretReferenceObject:
                    b.settings["power"] = a.settings["power"]
        #Scrap, ship upgrades and vent plotting.
        for a in Rooms:
            if a.size[0]>50 and a.size[1]>50:
                for i in range(random.randint(0,5)): #Put scrap inside the room
                    if self.__roomFull(a):
                        break
                    self.__placeEnt(a,"scrap",True)
                if random.randint(0,10)==1 and not self.__roomFull(a): #10% chance of their being a ship upgrade
                    self.__placeEnt(a,"upgrade slot")
                    upgs = ["Empty"]+list(self.__LINK["shipUp"])
                    self.__ents[-1].settings["upgrade"] = upgs[random.randint(0,len(upgs)-1)]
                    self.__ents[-1].settings["perm"] = random.randint(0,5)==1 #20% chance the upgrade is perminant
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
                    for i in range(3):
                        drone.settings["upgrades"][i][0] = adding[random.randint(0,len(adding)-1)]
                        if drone.settings["upgrades"][i][0]!="":
                            drone.settings["upgrades"][i][1] = random.randint(0,2)
                    if random.randint(0,2)==1: #33% chance the drone is perminantly disabled
                        drone.settings["health"]=0
        if not self.__roomFull(Path[-1]): #Place a fuel port at the end of the path
            self.__placeEnt(Path[-1],"fuel")
    def __figurePath(self,Paths,RoomDoors,DoorRooms,ignore=[]): #Used to figure out a hidden path for the player to take
        sels = []
        for a in RoomDoors[Paths[-1]]: #Gather doors that the player can go through and havn't been looked at before
            RM = None
            if DoorRooms[a][0]==Paths[-1]:
                RM = DoorRooms[a][1]
            else:
                RM = DoorRooms[a][0]
            if not RM in Paths and not RM in ignore:
                sels.append(RM)
        for a in sels: #Go through each door thats allowed
            if not a in Paths: #Check if its still allowed (might be changed due to recursion)
                Paths.append(a)
                Paths = self.__figurePath(Paths,RoomDoors,DoorRooms,ignore)
        return Paths
    def __save(self): #Save the generated map
        build = [self.__IDCount+0]
        for a in self.__ents:
            try:
                build.append(a.SaveFile())
            except:
                self.__LINK["errorDisplay"]("Error when saving entitiy ",a,sys.exc_info())
        file = open("maps/"+self.__saveName,"wb")
        file.write(pickle.dumps(build))
        file.close()
