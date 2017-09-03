#Main screen for drones
import pygame, time, pickle, sys

SCROLL_SPEED = 2 #Scematic scroll speed
CONSOLE_SIZE = [440,205] #Size of the console
DRONE_VIEW_SCALE = 3 #Drone view zoom in
DEF_RES = [1000,700] #Default reslution, this will be used to scale up the screen if required
MESH_BLOCK_SIZE = 125 #Size of a single mesh block

def getMapMash(MAP): #Gets the map hash for the specific map
    file = open("maps/"+MAP,"rb")
    MLEN = len(file.read())
    file.close()
    MLEN = MLEN % 65535
    return MLEN
class GameEventHandle: #Used to simulate and handle the events of the game world (NOT VISUAL)
    def __init__(self, LINK):
        self.__LINK = LINK
        self.Map = [] #Stores ALL entities. Order does not matter
        self.Ref = {} #Reference, used to access specific types of entities
        self.__lastTime = time.time() #Used to tackle lag
        self.drones = LINK["drones"] #All the drones used
        self.ship = LINK["shipEnt"] #The main ship of the map
        self.Mesh = {} #Used to speed up entitiy discovery, this is a 2D dictionary
        LINK["mesh"] = self.Mesh #Set the global MESH to this classes one.
    def loop(self): # Called continuesly as an event loop for all entities in the map
        lag = (time.time()-self.__lastTime)*30 # Used to vary lag
        self.__lastTime = time.time()
        for a in self.Map: # Loop through all objects and call their event loop
            a.loop(lag)
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
        idRef = {} #Used to initaly link entities up together
        doorCount = 1 #Counting doors
        airCount = 1 #Counting airlocks
        roomCount = 1 #Counting rooms
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
            idRef[a[1]+0] = self.Map[-1]
            if not a[0] in self.Ref: #Entity doesen't have its own directory, create one
                self.Ref[a[0]] = []
            self.Ref[a[0]].append(self.Map[-1]) #Add the entitiy to a list of ones its same type.
        defaultAir = None #The default airlock found.
        for i,a in enumerate(data[1:]): #Load all the netities settings
            try:
                self.Map[i].LoadFile(a,idRef)
                if type(self.Map[i]) == self.getEnt("airlock"): #Entity is an airlock
                    if self.Map[i].settings["default"]: #Is the default airlock
                        defaultAir = self.Map[i]
            except:
                self.__LINK["errorDisplay"]("Error when loading entity ",a,sys.exc_info())
            self.addToMesh(self.Map[i]) #Add the entitiy to the MESH
        if defaultAir is None:
            self.__LINK["log"]("There is no default airlock, finding one...")
            if "a1" in self.Ref:
                defaultAir = self.Ref["a1"]
            else:
                self.__LINK["log"]("There are no airlocks on this map, an exception is about to raise")
        self.Map.append(self.ship) #Add the main ship to the map
        self.ship.dockTo(defaultAir) #Dock the ship to an airlock
        self.Map.append(self.ship.room) #Add the ships room to the map
        self.addToMesh(self.ship) #Add the ship to the MESH
        self.addToMesh(self.ship.room) #Add the ship's room to the MESH
        for i,a in enumerate(self.drones): #Add all the users drones to the map
            self.Map.append(a)
            if self.ship.LR: #Is the ship left to right
                a.pos = [self.ship.room.pos[0]+(i*60)+40,self.ship.room.pos[1]+40]
            else:
                a.pos = [self.ship.room.pos[0]+40,self.ship.room.pos[1]+(i*60)+40]
            self.addToMesh(a) #Add the drone to the MESH
            if self.__LINK["multi"] == 2: #Is server
                self.__LINK["serv"].SYNC["e"+str(a.ID)] = a.GiveSync()
        file.close()
        self.__LINK["mesh"] = self.Mesh #Link the new MESH to the global one
        self.__LINK["log"]("Opened file sucsessfuly!")

class Main: #Used as the screen object for rendering and interaction
    def __init__(self,LINK):
        self.__LINK = LINK
        self.Map = [] #Used to store the map inside
        self.Ref = {} #Used as a reference for other objects to find a selection of objects faster.
        self.mapLoaded = False #Is the map loaded or not
        self.mapLoading = False #Is the map loading
        self.__renderFunc = LINK["render"].Scematic(LINK,False) #Class to render entities
        self.__command = LINK["render"].CommandLine(LINK,3) #Class to render command line
        self.__reslution = LINK["reslution"] #Reslution of the game
        self.__Event = None; # Stores the class "GameEventHandle" to handle events for entities
        self.__renderFunc.ents = self.Map #Make sure the rendering class gets updates from this one through a pointer
        self.scematic = True #If viewing in scematic view
        self.__scemPos = [0,0] #Scematic position
        self.__HoldKeys = {} #Keys being held down
        self.__DOWNLOAD = [] #Used to store downloads (map)
        self.currentDrone = None #A reference to the currently selected drone
    def __isKeyDown(self,key): #Returns true if the key is being held down
        if key in self.__HoldKeys: #Has the key been pressed before?
            return self.__HoldKeys[key]
        return False
    def goToDrone(self,number): #Goto a specific drone number view
        if number>len(self.__Event.drones) or number<=0: #Drone doesen't exist
            self.__command.addLine("No such drone "+str(number),(255,255,0))
        else: #Drone exists
            self.currentDrone = self.__Event.drones[number-1] #Set the current drone object to the one specified
            self.scematic = False #Is not viewing in scematic view
            self.__command.activeTab = number-1 #Switch to the specific tab of the drone
    def loop(self,mouse,kBuf,lag): #Constant loop
        global start
        for event in kBuf: #Loop through keyboard event loops
            if event.type == pygame.KEYDOWN:
                self.__HoldKeys[event.key] = True
                if event.key >= 48 and event.key <=57: #Key is a number
                    self.goToDrone(int(chr(event.key)))
                elif event.key == pygame.K_SPACE: #Exit out of scematic view
                    self.scematic = True
                    self.currentDrone = None
                    self.__command.activeTab = len(self.__Event.drones) #Goto the ships command line
            elif event.type == pygame.KEYUP:
                self.__HoldKeys[event.key] = False
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
            if self.__isKeyDown(self.__LINK["controll"]["up"]):
                self.currentDrone.go(lag*2)
            if self.__isKeyDown(self.__LINK["controll"]["down"]):
                self.currentDrone.go(-2*lag)
            if self.__isKeyDown(self.__LINK["controll"]["left"]):
                self.currentDrone.turn(lag*4)
            if self.__isKeyDown(self.__LINK["controll"]["right"]):
                self.currentDrone.turn(-4*lag)
        if not self.__Event is None:
            self.__Event.loop()
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def downLoadingMap(self,LN): #Function called to save a peaice of the map
        print("GOT,",LN)
        if type(LN)==str: #Map has finished downloading
            file = open("maps/"+LN,"wb")
            file.write(pickle.dumps(self.__DOWNLOAD)) #Save the downloaded map
            file.close()
            self.__LINK["log"]("Finished downloading map")
            self.open(LN) #Open the saved map
            self.__DOWNLOAD = [] #Clear up some memory
        else:
            self.__DOWNLOAD.append(LN) #Add the downloading map to a 
    def joinGame(self): #Joins a multiplayer server (downloads map)
        for maps in self.__LINK["maps"]: #Find the map (if it exists)
            if getMapMash(maps) == self.__LINK["cli"].SYNC["M"]["h"]: #Found the map, load it
                self.open(maps)
                break
        else: #Request to download the map
            self.__LINK["log"]("Missing map '"+self.__LINK["cli"].SYNC["M"]["n"]+"' downloading...")
            self.__DOWNLOAD = []
            self.__LINK["cli"].TRIGGER["dsnd"] = self.downLoadingMap #Downloading map function
            self.__LINK["cli"].sendTrigger("dwnl")
            self.mapLoading = True
    def open(self,name): #Opens a map
        self.__Event = GameEventHandle(self.__LINK)
        self.__Event.open(name)
        self.__renderFunc.ents = self.__Event.Map
        self.__scemPos = [self.__Event.ship.pos[0]-(self.__LINK["reslution"][0]/2),self.__Event.ship.pos[1]-(self.__LINK["reslution"][1]/2)] #Start the scematic position at the ships position
        self.__command.activeTab = len(self.__Event.drones)
        self.mapLoaded = True
        self.mapLoading = False
    def render(self,surf=None): #Render everything.
        if surf is None:
            surf = self.__LINK["main"]
        scale = ((self.__LINK["reslution"][0]/DEF_RES[0])+(self.__LINK["reslution"][1]/DEF_RES[1]))/2
        if self.scematic: #Is inside the scematic view
            self.__renderFunc.render(self.__scemPos[0],self.__scemPos[1],0.8,surf) #Render the map.
            #self.__LINK["render"].drawDevMesh(self.__scemPos[0],self.__scemPos[1],0.8,surf,self.__LINK) #DEVELOPMENT
        elif not self.currentDrone is None:
            drpos = [self.currentDrone.pos[0]*DRONE_VIEW_SCALE*scale,self.currentDrone.pos[1]*DRONE_VIEW_SCALE*scale] #Find the drones position in screen coordinates
            self.__renderFunc.render(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,surf) #Render the map through drone view.
            #self.__LINK["render"].drawDevMesh(drpos[0]-(self.__LINK["reslution"][0]/2)+(25*scale),drpos[1]-(self.__LINK["reslution"][1]/2)+(25*scale),DRONE_VIEW_SCALE*scale,surf,self.__LINK) #DEVELOPMENT
        self.__command.render(self.__reslution[0]-CONSOLE_SIZE[0]-20,self.__reslution[1]-CONSOLE_SIZE[1]-20,CONSOLE_SIZE[0],CONSOLE_SIZE[1],surf) #Render command line
