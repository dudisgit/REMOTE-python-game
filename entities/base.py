#This file is the base entitie that all other entites inheret to.
import pygame,time,math,cmath

MESH_BLOCK_SIZE = 125 #Size of a single mesh block (game.py)
ROOM_BORDER = 5 # Width of a boarder in a room
DOOR_BORDER = 5 #Border of a door

def nothing(*args): #Does nothing
    pass

class Main(object):
    def __init__(self,x,y,LINK,ID):
        LINK["errorDisplay"]("Base entitie was created but shouldn't be. This class is for inheriting uses only!")
        self.init(x,y,LINK)
        self.ID = ID
    def init(self,x,y,LINK): #Called to initialize variables
        self.pos = [x,y] #Position of the entity
        self.size = [50,50] #Size of the entity
        self.angle = 0 #Angle of the entitity
        self.overide = False #If this entitiy should overwrite the SYNC settings (multipalyer)
        self.alive = True #Is the entitiy alive (Should only be used for destructable entities)
        self.settings = {} #Settings of the entity, this is a vital part since this is what is saved to the file along with position and size.
        self.linkable = [] #A list containing items describing what entity can link to this one.
        self.REQUEST_DELETE = False #If the entity is requesting to be deleted
        self.colisionType = 0 #Type of colision, 0 = Off/Walls only, 1 = Circle, 2 = Box
        self.LINK = LINK #Cannot make it __LINK because the class it is inhertited by will not be able to access it.
        self.HINT = False #Hint what the object does
        self.paths = [] # Paths this entity should follow
        self.beingSucked = None #Is being sucked out of an airlock, None = is a solid object, else True/False
        self.hintMessage = "NO HINT" #Hinting message
    def getEnt(self,name): #Returns the entity with the name
        if name in self.LINK["ents"]: #Does the entity exist?
            return self.LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.LINK["errorDisplay"]("Tried to get entity but doesen't exist '"+name+"'")
        return self.LINK["null"]
    def teleported(self): #Called when this entity has been teleported, used in ship docking
        pass
    def EntitiesInside(self,includeRoom=False,pos=None,size=None,bsize=1): #Returns all entities inside this one (game). Ignores airlocks, rooms and doors
        if pos is None:
            pos = self.pos
        if size is None:
            size = self.size
        ents = []
        for x in range(int(pos[0]/MESH_BLOCK_SIZE)-bsize,int(pos[0]/MESH_BLOCK_SIZE)+int(size[0]/MESH_BLOCK_SIZE)+bsize): #Loop through a 3x3 square in MESH to find entities
            if x in self.LINK["mesh"]: #X column exists
                for y in range(int(pos[1]/MESH_BLOCK_SIZE)-bsize,int(pos[1]/MESH_BLOCK_SIZE)+int(size[1]/MESH_BLOCK_SIZE)+bsize):
                    if y in self.LINK["mesh"][x]: #Y column exists
                        for ENT in self.LINK["mesh"][x][y]:
                            if ENT.pos[0]+ENT.size[0]>pos[0] and ENT.pos[0]<pos[0]+size[0] and ENT.pos[1]+ENT.size[1]>pos[1] and ENT.pos[1]<pos[1]+size[1]:
                                if (type(ENT)!=self.getEnt("room") and type(ENT)!=self.getEnt("door") and type(ENT)!=self.getEnt("airlock") and ENT!=self) or includeRoom:
                                    if not ENT in ents:
                                        ents.append(ENT)
        return ents
    def __DIJgetEnt(self,ENTID): #Returns the index of the specific entitiy
        for i,a in enumerate(self.__DIJdist):
            if a[0].ID==ENTID:
                return i
        self.LINK["errorDisplay"]("Tried to reference entity ID "+str(ENTID)+" when finding path but it doesen't exist in the dijstra map.")
    def __buildDij(self,ENT,ignoreDoor=False): #Gets all the doors and rooms and puts their distance in self.__DIJdist
        if ENT in self.__DIJvisit: #If this entity has allredey been visited then do not run
            return 0
        self.__DIJvisit.append(ENT) #Make this room visited
        if type(ENT)==self.getEnt("room"): #Is a room
            ITM = len(self.__DIJdist)+0 #Used to change this entities contents in __DIJdist
            self.__DIJdist.append([ENT,-1,"",[]]) #Add the entity to __DIJdist, index of addition is ITM
            for a in ENT.doors: #Go through every door in the room that has not been visited
                if not a in self.__DIJvisit: #Has the door not been visited yet
                    self.__DIJvisit.append(a)
                    if not a.room1 is None and not a.room2 is None and (a.settings["open"] or ignoreDoor): #Door is valid and possibly open
                        if a.room1 == ENT: #If this room is the doors first connection then go to the second one.
                            self.__buildDij(a.room2,ignoreDoor)
                        else:
                            self.__buildDij(a.room1,ignoreDoor)
                        self.__DIJdist.append([a,-1,"",[a.room1,a.room2]]) #Add this door to the __DIJdist list
                    elif type(a) == self.getEnt("airlock") and (a.settings["open"] or ignoreDoor):
                        if a.room2 is None: #Not connected to a ship
                            self.__DIJdist.append([a,-1,"",[a.room1]])
                        else: #Is connected to a ship
                            self.__DIJdist.append([a,-1,"",[a.room1,a.room2]])
                            self.__buildDij(a.room2,ignoreDoor)
                    elif a.settings["open"] or ignoreDoor: #Add the door even if its missing rooms but remove most of its connections
                        if a.room1 is None and a.room2 is None:
                            self.__DIJdist.append([a,-1,"",[]])
                        elif a.room1 is None:
                            self.__DIJdist.append([a,-1,"",[self.room2]])
                        elif a.room2 is None:
                            self.__DIJdist.append([a,-1,"",[self.room1]])
                        else:
                            self.__DIJdist.append([a,-1,"",[self.room1,self.room2]])
                if not a.room1 is None and (not a.room2 is None or type(a)==self.getEnt("airlock")) and (a.settings["open"] or ignoreDoor): #Add the door to the rooms list of connections
                    self.__DIJdist[ITM][3].append(a)
        else: #Is a door
            #Add the door to the __DIJdist list with the correct connections
            if ENT.room1 is None and ENT.room2 is None:
                self.__DIJdist.append([ENT,-1,"",[]])
            elif ENT.room1 is None:
                self.__DIJdist.append([ENT,-1,"",[ENT.room2]])
            elif ENT.room2 is None:
                self.__DIJdist.append([ENT,-1,"",[ENT.room1]])
            else:
                self.__DIJdist.append([ENT,-1,"",[ENT.room1,ENT.room2]])
            if not ENT.room1 is None: #Check the doors first room for paths
                if not ENT.room1 in self.__DIJvisit:
                    self.__buildDij(ENT.room1,ignoreDoor)
            if not ENT.room2 is None: #Check the doors second room for paths
                if not ENT.room2 in self.__DIJvisit:
                    self.__buildDij(ENT.room2,ignoreDoor)
    def __distance(self,ENT1,ENT2): #Returns the distance between ENT1 and ENT2
        e1pos = [ENT1.pos[0]+(ENT1.size[0]/2),ENT1.pos[1]+(ENT1.size[1]/2)] #Center of entity 1
        e2pos = [ENT2.pos[0]+(ENT2.size[0]/2),ENT2.pos[1]+(ENT2.size[1]/2)] #Center of entity 2
        return math.sqrt(( (ENT1.pos[0]-ENT2.pos[0]) **2)+( (ENT1.pos[1]-ENT2.pos[1]) **2)) #Distance between them
    def __dijSort(self): #Sorts the __DIJdist list into order of distances using the bubble sort algorithm
        hasDone = True
        sub = 1
        while hasDone: #Will continue until the list is sorted
            hasDone = False
            for i in range(0,len(self.__DIJdist)-sub):
                if (self.__DIJdist[i][1]>self.__DIJdist[i+1][1] and self.__DIJdist[i+1][1]!=-1) or self.__DIJdist[i][1]==-1: #Swap
                    self.__DIJdist[i],self.__DIJdist[i+1]=self.__DIJdist[i+1],self.__DIJdist[i]
                    hasDone = True
            sub += 1
    def __dij(self,goal,ignoreDoor=False):
        visited = [] #Doors/rooms/airlocks that have allredey been processed
        curPos = self.findPosition() #Find the room/door this entity is currently in
        if curPos == -1:
            self.LINK["errorDisplay"]("Failed to generate path, entity is outside the map!")
            return -1
        self.__buildDij(curPos,ignoreDoor)
        while len(self.__DIJdist)!=0: #Keep repeating till the list of distances are cleared
            itm = self.__DIJdist.pop(0) #Pop the first item of __DIJdist
            for a in itm[3]: #Go through all the rooms connections (doors/airlocks)
                if not a.ID in visited:
                    index = self.__DIJgetEnt(a.ID) #Get the index of the door/airlock
                    itm2 = self.__DIJdist[index] #Get a pointer for the door/airlock inside the __DIJdist list
                    if itm2[1]==-1 or itm[1]+self.__distance(itm[0],a)<itm2[1]: #Update the distance if we've found a shorter path
                        self.__DIJdist[index][1] = itm[1]+self.__distance(itm[0],a) #Update the distance
                        self.__DIJdist[index][2] = itm[2]+"/"+str(a.ID) #Update the path to get to this entity
            self.__dijSort() #Sort the list
            visited.append(itm[0].ID+0) #Make sure this object is not visited again
            if itm[0]==goal: #Have we reached our goal?
                return itm
        return -1
    def __turnDijToPath(self,Plist): #Turns the results from the dijstra algorithm into lists of positions
        res = []
        spl = Plist.split("/") #Split into a list of ID's for each entity
        lastPos = [self.pos[0]+0,self.pos[1]+0]
        for a in spl[1:]:
            if a!="": #Is not empty
                ent = self.LINK["IDs"][int(a)]
                if type(ent)==self.getEnt("door") or type(ent)==self.getEnt("airlock"): #Entity is a door
                    if type(ent)==self.getEnt("airlock"): #Find direction left to right in an airlock
                        DIR = ent.settings["dir"]>=2
                    else:#A normal door
                        DIR = ent.settings["lr"]
                    if DIR: #Is left to right door/airlock
                        if lastPos[0]>ent.pos[0]:
                            res.append([ent.pos[0]+(ent.size[0]*1.5),ent.pos[1]+(ent.size[1]/2),ent])
                            res.append([ent.pos[0]-(ent.size[0]/2),ent.pos[1]+(ent.size[1]/2),None])
                        else:
                            res.append([ent.pos[0]-(ent.size[0]/2),ent.pos[1]+(ent.size[1]/2),ent])
                            res.append([ent.pos[0]+(ent.size[0]*1.5),ent.pos[1]+(ent.size[1]/2),None])
                    else: #Is up to down door/airlock
                        if lastPos[1]>ent.pos[1]:
                            res.append([ent.pos[0]+(ent.size[0]/2),ent.pos[1]+(ent.size[1]*1.5),ent])
                            res.append([ent.pos[0]+(ent.size[0]/2),ent.pos[1]-(ent.size[1]/2),None])
                        else:
                            res.append([ent.pos[0]+(ent.size[0]/2),ent.pos[1]-(ent.size[1]/2),ent])
                            res.append([ent.pos[0]+(ent.size[0]/2),ent.pos[1]+(ent.size[1]*1.5),None])
                    if ent.room2 is None and type(ent)==self.getEnt("airlock"): #Is an open but empty airlock
                        res.pop() #Make sure the drone goes straight into the airlock
                elif a==spl[-1]: #End of the path room
                    res.append([ent.pos[0]+(ent.size[0]/2),ent.pos[1]+(ent.size[1]/2),ent])
                lastPos = [ent.pos[0]+0,ent.pos[1]+0]
        curPos = self.findPosition()
        if curPos!=self.getEnt("room") and curPos!=-1 and len(res)!=0: #Entity started in a door
            if type(curPos)==self.getEnt("airlock"): #Find direction left to right in an airlock
                DIR = curPos.settings["dir"]>=2
            elif type(curPos)==self.getEnt("door"):#A normal door
                DIR = curPos.settings["lr"]
            else:
                return res
            lastPos = [res[0][0]+0,res[0][1]+0]
            if DIR: #Is left to right door/airlock
                if lastPos[0]<curPos.pos[0]:
                    res.insert(0,[curPos.pos[0]-(curPos.size[0]/2),curPos.pos[1]+(curPos.size[1]/2),None])
                else:
                    res.insert(0,[curPos.pos[0]+(curPos.size[0]*1.5),curPos.pos[1]+(curPos.size[1]/2),None])
            else: #Is up to down door/airlock
                if lastPos[1]<curPos.pos[1]:
                    res.insert(0,[curPos.pos[0]+(curPos.size[0]/2),curPos.pos[1]-(curPos.size[1]/2),None])
                else:
                    res.insert(0,[curPos.pos[0]+(curPos.size[0]/2),curPos.pos[1]+(curPos.size[1]*1.5),None])
        return res
    def isPathTo(self,ENT,StartPos=None): #Returns True if its possible to navigate to the destination
        if StartPos is None:
            StartPos = self.pos
        self.__DIJdist = [] #Distances to all the entities
        self.__DIJvisit = [] #Entiteis that have finished scanning
        if type(ENT)!=self.getEnt("room") and type(ENT)!=self.getEnt("door") and type(ENT)!=self.getEnt("airlock"):
            goal = ENT.findPosition()
            if goal == -1:
                self.LINK["errorDisplay"]("Failed to get entities map position. Outside map?")
                return -1
        else:
            goal = ENT
        return self.__dij(goal,False)!=-1
    def suckOutOfAirlock(self,PATH): #Suck this entity out of an airlock
        P = ""
        spl = PATH.split("/")
        for a in spl:
            P="/"+str(a)+P
        self.paths.append([1,self.__turnDijToPath(P)])
        self.beingSucked = True
    def pathTo(self,ENT,ignoreDoor=False,force=False): #Returns the path to the specific entitiy
        #This is returning a list of positions and entities the path is directing
        #Syntax
        #[posx,posy,ent]
        self.__DIJdist = [] #Distances to all the entities
        #Syntax
        #[Entity, distance, path, [Connections]]
        self.__DIJvisit = [] #Entiteis that have finished scanning
        if type(ENT)!=self.getEnt("room") and type(ENT)!=self.getEnt("door") and type(ENT)!=self.getEnt("airlock"):
            goal = ENT.findPosition()
            if goal == -1:
                self.LINK["errorDisplay"]("Failed to get entities map position. Outside map?")
                return -1
        else:
            goal = ENT
        path = self.__dij(goal,ignoreDoor)
        if path==-1: #Failed to find path
            return False
        else:
            rem = []
            for a in self.paths:
                if (a[0]==0 and not force) or (a[0]==1 and force): #Normal navigation path
                    rem.append(a)
            for a in rem:
                self.paths.remove(a)
            fin = self.__turnDijToPath(path[2])
            if len(fin)!=0:
                self.paths.append([0,fin])
            return True
    def movePath(self,lag): #Moves the position of this entity to the relative path
        rem = []
        REACH_END = False #Has reached the end of the path if this entity is being sucked out an airlock
        for a in self.paths: #Go through all the paths
            sp = [self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2)] #Entities center position
            angle = math.atan2(sp[0]-a[1][0][0],sp[1]-a[1][0][1])*180/math.pi #Angle of the target
            angle = int(angle) % 360 #Put into the range 0-360
            if a[0]==0:
                dist2 = 0 #Angular distance from the entities angle and the targets angle
                if angle > self.angle: #This is an algorithm for turning in a proper direction smothly
                    if angle - self.angle > 180:
                        dist2 = 180 - (angle - 180 - self.angle)
                        self.angle-=lag*(dist2**0.7)
                    else:
                        dist2 = angle - self.angle
                        self.angle+=lag*(dist2**0.7)
                else:
                    if self.angle - angle > 180:
                        dist2 = 180 - (self.angle - 180 - angle)
                        self.angle+=lag*(dist2**0.7)
                    else:
                        dist2 = self.angle - angle
                        self.angle-=lag*(dist2**0.7)
                try:
                    self.angle = int(self.angle) % 360 #Make sure this entitys angle is not out of range
                except:
                    self.angle = int(cmath.phase(self.angle)) % 360 #Do the same before but unconvert it from a complex number
                speed = 2*lag #Speed to move at
            else: #Being sucked out an airlock
                speed = 6*lag
            bpos = [self.pos[0]+0,self.pos[1]+0] #Before position
            if a[0]==0:
                self.pos[0]-=math.sin(self.angle/180*math.pi)*speed
                self.pos[1]-=math.cos(self.angle/180*math.pi)*speed
            else: #Being sucked out an airlock
                self.pos[0]-=math.sin(angle/180*math.pi)*speed
                self.pos[1]-=math.cos(angle/180*math.pi)*speed
            self.changeMesh(bpos) #Move the drone to anouther MESH
            HIT = self.applyPhysics(lag) #Apply hit-box detection
            dist = math.sqrt(((sp[0]-a[1][0][0])**2)+((sp[1]-a[1][0][1])**2)) #Distance from the target node
            if type(a[1][0][2]) == self.getEnt("airlock") or type(a[1][0][2]) == self.getEnt("door"):
                if not a[1][0][2].settings["open"]:
                    if type(self)==self.getEnt("drone") and a[0]==0:
                        self.LINK["outputCommand"]("Drone navigation opstructed",(255,255,0),self)
                    rem.append(a)
            if a[0]==1:
                if not a[1][-1][2].settings["open"]:
                    rem.append(a)
            if dist<12.5 or (type(a[1][0][2]) == self.getEnt("room") and HIT): #Finished going through the path.
                if len(a[1])==1 and a[0]==1 and type(a[1][0][2])==self.getEnt("airlock"):
                    REACH_END = True
                a[1].pop(0)
                if len(a[1])==0:
                    rem.append(a)
        for a in rem: #Remove paths
            if a[0]==1 and REACH_END:
                self.beingSucked = False
                self.REQUEST_DELETE = True #Delete this entity
                self.deleting()
            elif a[0]==1:
                self.beingSucked = False
            if a in self.paths: #Sometimes a path can request deletion twise!
                self.paths.remove(a)
    def afterLoad(self): #Called after the map has finished loading
        pass
    def deleting(self): #Called when this entity is being deleted
        pass
    def stopNavigation(self,typ=0): #Stops all navigation paths on the specific one
        rem = []
        for a in self.paths:
            if a[0]==typ:
                rem.append(a)
        for a in rem:
            self.paths.remove(a)
    def findPosition(self,pos=None,size=None): #Returns what door/airlock/room this entity is in.
        if pos is None:
            pos = self.pos
        if size is None:
            size = self.size
        bsize = 1
        for x in range(int(pos[0]/MESH_BLOCK_SIZE)-bsize,int(pos[0]/MESH_BLOCK_SIZE)+int(size[0]/MESH_BLOCK_SIZE)+bsize): #Loop through a 3x3 square in MESH to find entities
            if x in self.LINK["mesh"]: #X column exists
                for y in range(int(pos[1]/MESH_BLOCK_SIZE)-bsize,int(pos[1]/MESH_BLOCK_SIZE)+int(size[1]/MESH_BLOCK_SIZE)+bsize):
                    if y in self.LINK["mesh"][x]: #Y column exists
                        for ENT in self.LINK["mesh"][x][y]:
                            #Check if this entity is atall inside or touching the possible room/door/airlock
                            inside = (pos[0]>=ENT.pos[0] and pos[0]<=ENT.pos[0]+ENT.size[0] and pos[1]>=ENT.pos[1] and pos[1]<=ENT.pos[1]+ENT.size[1])
                            inside = inside or (pos[0]+size[0]>=ENT.pos[0] and pos[0]+size[0]<=ENT.pos[0]+ENT.size[0] and pos[1]>=ENT.pos[1] and pos[1]<=ENT.pos[1]+ENT.size[1])
                            inside = inside or (pos[0]+size[0]>=ENT.pos[0] and pos[0]+size[0]<=ENT.pos[0]+ENT.size[0] and pos[1]+size[1]>=ENT.pos[1] and pos[1]+size[1]<=ENT.pos[1]+ENT.size[1])
                            inside = inside or (pos[0]>=ENT.pos[0] and pos[0]<=ENT.pos[0]+ENT.size[0] and pos[1]+size[1]>=ENT.pos[1] and pos[1]+size[1]<=ENT.pos[1]+ENT.size[1])
                            if inside:
                                if type(ENT)==self.getEnt("room") or type(ENT)==self.getEnt("door") or type(ENT)==self.getEnt("airlock"):
                                    return ENT
        return -1
    def insideRoom(self,ents,pos=None,size=None): #Returns the room if this entity is inside one.
        if pos is None:
            pos = self.pos
        if size is None:
            size = self.size
        for a in ents:
            if type(a) == self.getEnt("room"):
                #Checks all 4 corners of the entity to check if it is inside this one
                ins = pos[0] >= a.pos[0] and pos[1] >= a.pos[1] and pos[0] < a.pos[0]+a.size[0] and pos[1] < a.pos[1]+a.size[1] #Top left
                ins2 = pos[0]+size[0] > a.pos[0] and pos[1] > a.pos[1] and pos[0]+size[0] < a.pos[0]+a.size[0] and pos[1] < a.pos[1]+a.size[1] #Bottom right
                ins3 = pos[0] > a.pos[0]+a.size[0] and pos[1]+size[1] > a.pos[1] and pos[0] < a.pos[0]+a.size[0] and pos[1]+size[1] < a.pos[1]+a.size[1] #Top right
                ins4 = pos[0]+size[0] > a.pos[0] and pos[1]+size[1] > a.pos[1] and pos[0]+size[0] < a.pos[0]+a.size[0] and pos[1]+size[1] < a.pos[1]+a.size[1] #Bottom left
                if ins or ins2 or ins3 or ins4:
                    return a
        return False
    def getImage(self,name): #Gets an image, returns a error and defualt surface otherwise
        if name in self.LINK["cont"]: #Return the image
            return self.LINK["cont"][name]
        self.LINK["errorDisplay"]("missing image '"+name+"'")
        gen = pygame.Surface((140,60))
        font = pygame.font.SysFont("impact",16)
        gen.blit(font.render("Error, missing image",16,(255,255,255)),[0,0])
        return gen
    def __doPhysEnt(self,ENT,lag,opts): #Applys physics againsed one specific entity
        if ENT==self: #Exits to stop coliding with itself
            return opts
        res = opts
        if type(ENT)==self.getEnt("room") and not "d" in opts: #Possibly coliding with a rooms walls
            if self.pos[0]>ENT.pos[0] and self.pos[1]>ENT.pos[1] and self.pos[0]<ENT.pos[0]+ENT.size[0] and self.pos[1]<ENT.pos[1]+ENT.size[1]: #Is inside the room
                bpos = [self.pos[0]+0,self.pos[1]+0] #Before position
                if self.pos[0]<ENT.pos[0]+ROOM_BORDER:
                    self.pos[0] = ENT.pos[0]+ROOM_BORDER
                if self.pos[1]<ENT.pos[1]+ROOM_BORDER:
                    self.pos[1] = ENT.pos[1]+ROOM_BORDER
                if self.pos[0]+self.size[0]>ENT.pos[0]+ENT.size[0]-ROOM_BORDER:
                    self.pos[0] = ENT.pos[0]+ENT.size[0]-ROOM_BORDER-self.size[0]
                if self.pos[1]+self.size[1]>ENT.pos[1]+ENT.size[1]-ROOM_BORDER:
                    self.pos[1] = ENT.pos[1]+ENT.size[1]-ROOM_BORDER-self.size[1]
                if self.pos!=bpos: #Add before position to a variable incase a door is in the entities path
                    if not "a" in opts:
                        res = "a"+str(bpos[0])+","+str(bpos[1])
        elif type(ENT)==self.getEnt("door") or type(ENT)==self.getEnt("airlock"): #Possibly coloding with a doors walls
            if ENT.settings["open"]:
                if type(ENT)==self.getEnt("airlock"):
                    lr = ENT.settings["dir"]>=2 #Left to right orientation
                else:
                    lr = ENT.settings["lr"] == True
                if "a" in opts: #Get the drones last position before it colided with a rooms walls
                    spl = opts.split(",")
                    bpos = [float(spl[0][1:]),float(spl[1])]
                else: #Get the drones position normaly
                    bpos = self.pos
                if lr: #Right to left
                    if (bpos[1]>=ENT.pos[1] and bpos[1]+self.size[1]<=ENT.pos[1]+ENT.size[1] and bpos[0]+self.size[0]>ENT.pos[0] and bpos[0]<ENT.pos[0]+ENT.size[0]) or (bpos[1]>=ENT.pos[1] and bpos[1]+self.size[1]<=ENT.pos[1]+ENT.size[1] and bpos[0]+self.size[0]>ENT.pos[0]-ROOM_BORDER and bpos[0]<ENT.pos[0]+ENT.size[0]+ROOM_BORDER):
                        if "a" in opts: #Tell other rooms that they cannot colide with this entity
                            self.pos = bpos.copy()
                            res = "d"
                        #Colide with doors walls
                        if self.pos[1]<ENT.pos[1]+DOOR_BORDER:
                            self.pos[1] = ENT.pos[1]+DOOR_BORDER
                        if self.pos[1]+self.size[1]>ENT.pos[1]+ENT.size[1]-DOOR_BORDER:
                            self.pos[1] = ENT.pos[1]+ENT.size[1]-DOOR_BORDER-self.size[1]
                else: #Up to down
                    if (bpos[0]>=ENT.pos[0] and bpos[0]+self.size[0]<=ENT.pos[0]+ENT.size[0] and bpos[1]+self.size[1]>ENT.pos[1] and bpos[1]<ENT.pos[1]+ENT.size[1]) or (bpos[0]>=ENT.pos[0] and bpos[0]+self.size[0]<=ENT.pos[0]+ENT.size[0] and bpos[1]+self.size[1]>ENT.pos[1]-ROOM_BORDER and bpos[1]<ENT.pos[1]+ENT.size[1]+ROOM_BORDER):
                        if "a" in opts: #Tell other rooms that they cannot colide with this entity
                            self.pos = bpos.copy()
                            res = "d"
                        #Colide with doors walls
                        if self.pos[0]<ENT.pos[0]+DOOR_BORDER:
                            self.pos[0] = ENT.pos[0]+DOOR_BORDER
                        if self.pos[0]+self.size[0]>ENT.pos[0]+ENT.size[0]-DOOR_BORDER:
                            self.pos[0] = ENT.pos[0]+ENT.size[0]-DOOR_BORDER-self.size[0]
        elif ENT.colisionType!=0 and self.colisionType!=0: #Is this entity is colidable
            if ENT.colisionType==1: #Circle
                dist = math.sqrt(( (self.pos[0]-ENT.pos[0])**2 ) + ( (self.pos[1]-ENT.pos[1])**2 ))
                if dist<30: #Is coliding
                    if len(opts)==0:
                        res = "o"
                    ang = math.atan2((self.pos[0]-ENT.pos[0]),(self.pos[1]-ENT.pos[1]))
                    self.pos = [ENT.pos[0]+(math.sin(ang)*30),ENT.pos[1]+(math.cos(ang)*30)]
            else: #Box colision
                if self.pos[0]>ENT.pos[0] and self.pos[0]<ENT.pos[0]+ENT.size[0] and self.pos[1]>ENT.pos[1] and self.pos[1]<ENT.pos[1]+ENT.size[1]:
                    if len(opts)==0:
                        res = "o"
                    ang = math.atan2((self.pos[0]-(ENT.pos[0]+(ENT.size[0]/2))),(self.pos[1]-(ENT.pos[1]+(ENT.size[1]/2))))
                    self.pos = [self.pos[0]+(math.sin(ang)*4*lag),self.pos[1]+(math.cos(ang)*4*lag)]
        return res
    def applyPhysics(self,lag=1): #Applys the physics to this entity
        bpos = [self.pos[0]+0,self.pos[1]+0]
        opts = ""
        for x in range(int(self.pos[0]/MESH_BLOCK_SIZE)-1,int(self.pos[0]/MESH_BLOCK_SIZE)+int(self.size[0]/MESH_BLOCK_SIZE)+1): #Loop through a 3x3 square in MESH to find coliding entities
            if x in self.LINK["mesh"]: #X column exists
                for y in range(int(self.pos[1]/MESH_BLOCK_SIZE)-1,int(self.pos[1]/MESH_BLOCK_SIZE)+int(self.size[1]/MESH_BLOCK_SIZE)+1):
                    if y in self.LINK["mesh"][x]: #Y column exists
                        for ENT in self.LINK["mesh"][x][y]: #Loop through every entitiy of this block
                            opts=self.__doPhysEnt(ENT,lag,opts) #Check if this entitiy is coliding with the specific other entity
        self.changeMesh(bpos) #Change the position of the MESH so its accurate with the current entity
        return "o" in opts
    def deleteMesh(self,pos=None): #Removes this entities mesh link
        if pos is None:
            pos = self.pos
        for x in range(round(pos[0]/MESH_BLOCK_SIZE)-1,round(pos[0]/MESH_BLOCK_SIZE)+round(self.size[0]/MESH_BLOCK_SIZE)+1): #Delete this entity from the MESH before
            if x in self.LINK["mesh"]:
                for y in range(round(pos[1]/MESH_BLOCK_SIZE)-1,round(pos[1]/MESH_BLOCK_SIZE)+round(self.size[1]/MESH_BLOCK_SIZE)+1):
                    if y in self.LINK["mesh"][x]:
                        if self in self.LINK["mesh"][x][y]:
                            self.LINK["mesh"][x][y].remove(self)
    def changeMesh(self,before): #Moves the entity into a different mesh
        if round(before[0]/MESH_BLOCK_SIZE)!=round(self.pos[0]/MESH_BLOCK_SIZE) or round(before[1]/MESH_BLOCK_SIZE)!=round(self.pos[1]/MESH_BLOCK_SIZE): #Move the mesh
            self.deleteMesh(before)
            for x in range(round(self.pos[0]/MESH_BLOCK_SIZE)-1,round(self.pos[0]/MESH_BLOCK_SIZE)+round(self.size[0]/MESH_BLOCK_SIZE)+1): #Add this entity to the MESH after it has moved (3x3 square)
                if not x in self.LINK["mesh"]:
                    self.LINK["mesh"][x] = {}
                for y in range(round(self.pos[1]/MESH_BLOCK_SIZE)-1,round(self.pos[1]/MESH_BLOCK_SIZE)+round(self.size[1]/MESH_BLOCK_SIZE)+1):
                    if not y in self.LINK["mesh"][x]:
                        self.LINK["mesh"][x][y] = []
                    self.LINK["mesh"][x][y].append(self)
    def findInside(self,ents,exceptions = []): #Retruns all the entities inside this one
        res = []
        for a in ents:
            #Checks all 4 corners of the entity to check if it is inside this one
            ins = a.pos[0] >= self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0] < self.pos[0]+self.size[0] and a.pos[1] < self.pos[1]+self.size[1] #Top left
            ins2 = a.pos[0]+a.size[0] > self.pos[0] and a.pos[1]+a.size[1] > self.pos[1] and a.pos[0]+a.size[0] < self.pos[0]+self.size[0] and a.pos[1]+a.size[1] < self.pos[1]+self.size[1] #Bottom right
            ins3 = a.pos[0]+a.size[0] > self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0]+a.size[0] < self.pos[0]+self.size[0] and a.pos[1] < self.pos[1]+self.size[1] #Top right
            ins4 = a.pos[0] >= self.pos[0] and a.pos[1]+a.size[1] > self.pos[1] and a.pos[0] < self.pos[0]+self.size[0] and a.pos[1]+a.size[1] < self.pos[1]+self.size[1] #Bottom left
            if (ins or ins2 or ins3 or ins4) and not a in exceptions:
                res.append(a)
        return res
    def findInsideOrNextTo(self,ents,exceptions = []): #Retruns all the entities inside and next to this one (next as in touching)
        res = []
        for a in ents:
            #Checks all 4 corners of the entity to check if it is inside or next to this one
            ins = a.pos[0] >= self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0] <= self.pos[0]+self.size[0] and a.pos[1] <= self.pos[1]+self.size[1] #Top left
            ins2 = a.pos[0]+a.size[0] >= self.pos[0] and a.pos[1]+a.size[1] >= self.pos[1] and a.pos[0]+a.size[0] <= self.pos[0]+self.size[0] and a.pos[1]+a.size[1] <= self.pos[1]+self.size[1] #Bottom right
            ins3 = a.pos[0]+a.size[0] >= self.pos[0] and a.pos[1] >= self.pos[1] and a.pos[0]+a.size[0] <= self.pos[0]+self.size[0] and a.pos[1] <= self.pos[1]+self.size[1] #Top right
            ins4 = a.pos[0] >= self.pos[0] and a.pos[1]+a.size[1] >= self.pos[1] and a.pos[0] <= self.pos[0]+self.size[0] and a.pos[1]+a.size[1] <= self.pos[1]+self.size[1] #Bottom left
            if (ins or ins2 or ins3 or ins4) and not a in exceptions:
                res.append(a)
        return res
    def renderHint(self,surf,message,pos): #Render a hint box
        screenRes = self.LINK["reslution"] #Screen reslution
        boxPos = [pos[0]+10,pos[1]+10] #Position of the box
        boxWidth = screenRes[0]/2 #Width of the box will be half the screen width
        boxHeight = 0
        mes = message.split(" ") #Split the message up by spaces
        charLength = 10 #Length of 1 charicter (constant)
        font = self.LINK["font24"] #Font to use when rendering
        adding = "" #Text being added to that line
        drawWord = [] #Store all the text in a list to be rendered
        for word in mes: #Loop through all text samples and build a list of strings that are cut off when they get to the end and start on the next element
            if (len(adding)+len(word))*charLength > boxWidth or "\n" in word: #Length would be above the length of the box or the message requested a new line using "\n"
                drawWord.append(adding+"")
                if "\n" in word: #Remove the "\n"
                    spl = word.split("\n")
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
        boxPos[1] = pos[1]-boxHeight-10 #Re-calculate the box position depening on the text height
        pygame.draw.rect(surf,(0,0,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8]) #Black box background
        mult = abs(math.cos(time.time()*3)) #Box flashing
        pygame.draw.rect(surf,(255*mult,255*mult,0),[boxPos[0]-4,boxPos[1]-4,boxWidth,boxHeight+8],3) #Flashing box
        for i,a in enumerate(drawWord): #Draw all the text calculated above
            surf.blit(font.render(a,16,(0,255,0)),[boxPos[0],boxPos[1]+(i*20)])
    def rightPos(self): #Returns the last position and size of the box
        if self.__surface is None:
            return [0,0,0,0]
        return [self.__lastRenderPos[0]+0,self.__lastRenderPos[1]+0]+list(self.__surface.get_size())
    def canShow(self): #Return wether the entitie should show on a scematic view in the game (doesen't apply to map editor)
        return self.__sShow == True
    def drawRotate(self,applySurf,x,y,surf,angle): #This function will rotate a surface round its center and draw it to the screen.
        siz = list(surf.get_size())
        sub = [abs(math.sin(angle/90*math.pi)*siz[0]/5),abs(math.sin(angle/90*math.pi)*siz[1]/5)]
        applySurf.blit(pygame.transform.rotate(surf,angle),(x-sub[0],y-sub[1]))
    def delete(self): #Deletes the entity.
        self.REQUEST_DELETE = True

