#Main screen for drones
import pygame, time, pickle

SCROLL_SPEED = 2 #Scematic scroll speed

class Main:
    def __init__(self,LINK):
        self.__LINK = LINK
        self.Map = [] #Used to store the map inside
        self.Ref = {} #Used as a reference for other objects to find a selection of objects faster.
        self.__renderFunc = LINK["render"].Scematic(LINK,False) #Class to render entities
        self.__reslution = LINK["reslution"] #Reslution of the game
        self.__renderFunc.ents = self.Map #Make sure the rendering class gets updates from this one through a pointer
        self.scematic = True #If viewing in scematic view
        self.__scemPos = [0,0] #Scematic position
        self.__HoldKeys = {} #Keys being held down
    def __isKeyDown(self,key): #Returns true if the key is being held down
        if key in self.__HoldKeys: #Has the key been pressed before?
            return self.__HoldKeys[key]
        return False
    def loop(self,mouse,kBuf,lag):
        for event in kBuf: #Loop through keyboard event loops
            if event.type == pygame.KEYDOWN:
                self.__HoldKeys[event.key] = True
            elif event.type == pygame.KEYUP:
                self.__HoldKeys[event.key] = False
        if self.scematic: #Is currently in the scematic view
            #Move the scematic view if the arrow keys are being held or pressed.
            if self.__isKeyDown(pygame.K_UP):
                self.__scemPos[1] -= SCROLL_SPEED
            if self.__isKeyDown(pygame.K_DOWN):
                self.__scemPos[1] += SCROLL_SPEED
            if self.__isKeyDown(pygame.K_LEFT):
                self.__scemPos[0] -= SCROLL_SPEED
            if self.__isKeyDown(pygame.K_RIGHT):
                self.__scemPos[0] += SCROLL_SPEED
    def getEnt(self,name): #Returns the entity with the name
        if name in self.__LINK["ents"]: #Does the entity exist?
            return self.__LINK["ents"][name].Main #Return the sucsessful entity
        else: #Raise an error and return a null entity
            self.__LINK["errorDisplay"]("Tried to create entity but doesen't exist '"+name+"'")
        return self.__LINK["null"]
    def open(self,name): #Opens a map
        try:
            file = open("maps/"+name,"rb")
        except:
            self.__LINK["errorDisplay"]("Failed to open file!",sys.exc_info())
            return 0
        try:
            data = pickle.loads(file.read())
        except:
            self.__LINK["errorDisplay"]("Failed to pickle load file")
            file.close()
            return 0
        self.Map = []
        self.Ref = {}
        idRef = {}
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
        for i,a in enumerate(data[1:]):
            try:
                self.Map[i].LoadFile(a,idRef)
            except:
                self.__LINK["errorDisplay"]("Error when loading entity ",a,sys.exc_info())
        self.__renderFunc.ents = self.Map #Make sure the rendering class gets updates from this one through a pointer
        file.close()
        self.__LINK["log"]("Opened file sucsessfuly!")
    def render(self,surf=None):
        if surf is None:
            surf = self.__LINK["main"]
        if self.scematic: #Is inside the scematic view
            self.__renderFunc.render(self.__scemPos[0],self.__scemPos[1],0.5,surf) #Render the map.
