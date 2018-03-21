#Do not run this file, it is a module!
import pygame, random, time
import entities.base as base

DOCK_DELAY = 4 #Time taken to dock to anouther airlock
DEFAULT_UPGRADE_LIMIT = 2 #Default upgrade limit on ships

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.size = [200,250]
        self.discovered = True
        self.__inRoom = True #The ship is allways visible
        self.__sShow = True #Ship will allways be visible in scematic view
        self.__forceEject = False #Used to detect wether the dock command was entered twise
        self.airlock = None #Airlock this ship is docked to
        self.dockTime = 0 #Time until the ship has finished docking
        self.room = self.getEnt("room")(x+50,y,LINK,-6,1) #The ships room
        self.room.size = [120,250]
        self.room.discovered2 = True
        self.room.ship = self #Giving the ships room a link to the ship
        self.room.isShipRoom = True #Make the room attached a ship room
        self.LR = False #Left to right direction
        self.settings["upgrades"] = []
        self.PERM_UPG = [] #Not used
        for i in range(DEFAULT_UPGRADE_LIMIT):
            self.settings["upgrades"].append(["",0,-1])
        self.upgrades = [] #Upgrades used by the ship
        self.hintMessage = "This entity should not be able to be spawned"
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["ship",self.ID,self.pos,self.settings["upgrades"]]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["upgrades"] = data[3]
        self.loadUpgrades()
    def loadUpgrades(self): #Loads all the upgrades into the ship
        self.upgrades = []
        for i,a in enumerate(self.settings["upgrades"]):
            if a[0]!="":
                if a[2]!=-1:
                    self.upgrades.append(self.LINK["shipUp"][a[0]].Main(self.LINK,a[2]))
                else:
                    self.upgrades.append(self.LINK["shipUp"][a[0]].Main(self.LINK,self.LINK["upgradeIDCount"]+0))
                    self.settings["upgrades"][i][2] = self.LINK["upgradeIDCount"]+0
                    self.LINK["upgradeIDCount"] += 1
                if len(a)==4:
                    self.upgrades[-1].brakeprob = a[3]+0
                self.upgrades[-1].damage = a[1]
                self.upgrades[-1].drone = self #Link the upgrade to this ship
    def unloadUpgrades(self): #Imports all the upgrades into the ship for saving (used in multiplayer)
        for a in self.settings["upgrades"]:
            a = ["",0,-1,0]
        for i,a in enumerate(self.upgrades):
            self.settings["upgrades"][i] = [a.name.lower(),a.damage+0,a.ID,a.brakeprob]
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,40)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def loop(self,lag):
        if time.time()>self.dockTime and self.dockTime!=0: #Reset docking timer when docking has completed
            self.dockTime = 0
            if self.LINK["multi"]!=1: #Is not a client, single player or server
                if not self.airlock.alive: #Airlock is dead
                    self.airlock.OPEN(True)
                self.LINK["outputCommand"]("Successfully docked to A"+str(self.airlock.number),(0,255,0),False)
        if self.LINK["multi"]!=1: #Is not a client, single player or server
            for a in self.upgrades: #Do an event loop on all upgrades
                a.loop(lag)
        else: #Is a client
            for a in self.upgrades: #Do an event loop on all upgrades
                a.clientLoop(lag)
    def dockTo(self,airlock,first=False): #Docks the ship to a specific airlock
        if self.dockTime!=0:
            return "Ship is still docking, please wait",(255,255,0)
        if not self.airlock is None: #Is docked to an airlock
            out = self.airlock.CLOSE()
            if out=="Airlock is being blocked" and not self.__forceEject:
                self.__forceEject = True
                return "Airlock is being blocked, re-enter to force",(255,255,0)
            if out!="Airlock is being blocked" and self.__forceEject:
                self.__forceEject = False
            self.airlock.room2 = None
            self.room.doors = [airlock]
        else: #First time docking to an airlock
            self.airlock = airlock
        airlock.CLOSE(True)
        self.dockTime = time.time()+DOCK_DELAY #Make sure nothing can open or dock until the ship has finished docking to the airlock
        self.room.dirDoors = [[],[],[],[]] #Used to store doors with direction
        bpos = [self.room.pos[0]+0,self.room.pos[1]+0]
        bpos2 = [self.pos[0]+0,self.pos[1]+0]
        allE = self.room.EntitiesInside()
        if airlock.settings["dir"] == 1: #Up
            self.pos = [airlock.pos[0]-(self.size[0]/2),airlock.pos[1]-self.size[1]]
            self.room.dirDoors[1] = [airlock] #Add this airlock to the BOTTOM of the room
        elif airlock.settings["dir"] == 0: #Down
            self.pos = [airlock.pos[0]-(self.size[0]/2),airlock.pos[1]+50]
            self.room.dirDoors[0] = [airlock] #Add this airlock to the TOP side of the room
        elif airlock.settings["dir"] == 2: #Right
            self.pos = [airlock.pos[0]+50,airlock.pos[1]-(self.size[0]/2)]
            self.room.dirDoors[2] = [airlock] #Add this airlock to the LEFT side of the room
        elif airlock.settings["dir"] == 3: #Left
            self.pos = [airlock.pos[0]-self.size[1],airlock.pos[1]-(self.size[0]/2)]
            self.room.dirDoors[3] = [airlock] #Add this airlock to the RIGHT side of the room
        if airlock.settings["dir"] <= 1:
            self.room.size = [150,250]
            self.LR = False
            self.room.pos = [self.pos[0]+50,self.pos[1]]
        else:
            self.room.size = [250,150]
            self.LR = True
            self.room.pos = [self.pos[0],self.pos[1]+50]
        self.room.reloadCorners() #Reload the ship rooms corners for fast rendering
        if not first:
            if (self.airlock.settings["dir"]>1 and airlock.settings["dir"]>1) or (self.airlock.settings["dir"]<=1 and airlock.settings["dir"]<=1):
                for a in allE: #Move all entities inside the ship room to the new location
                    if a!=self:
                        bpos3 = [a.pos[0]+0,a.pos[1]+0]
                        a.pos = [a.pos[0]+(self.room.pos[0]-bpos[0]),a.pos[1]+(self.room.pos[1]-bpos[1])]
                        a.changeMesh(bpos3)
            else:
                for a in allE: #Move all entities inside the ship room to the new location but when the room size has changed
                    if a!=self:
                        bpos3 = [a.pos[0]+0,a.pos[1]+0]
                        a.pos = [a.pos[0]+(self.room.pos[0]-bpos[0]),a.pos[1]+(self.room.pos[1]-bpos[1])]
                        a.pos = [self.room.pos[0]+(a.pos[1]-self.room.pos[1]),self.room.pos[1]+(a.pos[0]-self.room.pos[0])]
                        a.changeMesh(bpos3)
            for a in allE: #Tell all entities they where teleported
                a.teleported()
        self.room.teleported(bpos)
        self.room.changeMesh(bpos)
        self.room.reloadSize()
        self.changeMesh(bpos2)
        airlock.room2 = self.room
        if self.__forceEject:
            self.airlock.OPEN(True)
            self.__forceEject = False
        self.airlock = airlock
        self.room.doors = [airlock]
        return "Docking to A"+str(airlock.number),(0,255,0)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-90:
            windowPos[1] = self.LINK["reslution"][1]-90
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,208,surfSize[1]-3],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.HINT = False
        self.__but1 = None
    def editMove(self,ents): #The ship is being moved (using map editor)
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        return "Ship should not be spawned"
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if ((time.time()-int(time.time()))*2)%1>0.5 or self.dockTime==0:
            if self.LR:
                surf.blit(pygame.transform.rotate(self.getImage("ship"),90),(x,y))
            else:
                surf.blit(self.getImage("ship"),(x,y))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
