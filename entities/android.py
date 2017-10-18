#Do not run this file, it is a module!
import pygame, time
import entities.base as base

SHOW_RATE = 10 #Amount of times a second to scan for drones when in multiplayer (used to save engine resources)

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.isNPC = True
        self.health = 80
        self.speed = 1.5
        self.colisionType = 1 #Circle colision
        self.NPCDist = 70 #NPC distance to target limit
        self.size = [25,25]
        self.beingSucked = False #Make this entity suckable in a vacum
        self.__sShow = True #Show in games scematic view
        self.__first = True #First time this entity has spawned
        self.__lastScan = time.time() #Last time this NPC scanned for a drone
        self.__canSee = False #Drone can see this entity
        self.__inRoom = False #Is true if the NPC is inside a room
        self.hintMessage = "An android is easy to deal with. It is slower than drones and deals minimal damage. \nIt cannot attack doors"
    def takeDamage(self,dmg,reason=""):
        if reason!="radiation": #Android is imune to radiation
            self.health -= dmg
        if self.health<0:
            self.health = 0
            self.alive = False
            self.colisionType = 0 #Disable colision
            self.stopNavigation()
        return self.health == 0
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["android",self.ID,self.pos]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
    def SyncData(self,data): #Syncs the data with this android
        self.pos[0] = ((self.pos[0]*3)+data["x"])/4
        self.pos[1] = ((self.pos[1]*3)+data["y"])/4
        self.angle = ((self.angle*3)+data["a"])/4
    def GiveSync(self): #Returns the synced data for this android
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["a"] = int(self.angle)+0
        return res
    def NPCAttackLoop(self,dist): #Will only be called continuesly if there is a visual path between the target and that its chasing it.
        if dist<200: #Target in range, fire!
            self.NPCATTACK.takeDamage(1)
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            if self.__canSee or self.__first: #Only sync position if the player can see it.
                self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
                self.__first = False
            if time.time()>self.__lastScan:
                self.__lastScan = time.time()+(1/SHOW_RATE)
                self.__canSee = self.NPCDroneSee()
        if self.LINK["multi"]!=1: #Is not a client
            if self.alive:
                self.NPCloop()
            self.colisionType = 0 #Disable colisions, walls only
            self.movePath(lag)
            self.colisionType = 1 #Turn back to circle colision
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,40)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
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
    def editMove(self,ents): #The NPC is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (NPC)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.__inRoom and edit:
            surf.blit(self.getImage("android"),(x,y))
        elif edit:
            if (time.time()%0.5)>0.25:
                surf.blit(self.getImage("android"),(x,y))
        if self.LINK["DEVDIS"] and self.findPosition()!=-1:
            scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
            for a in self.paths:
                lastPos = [((self.pos[0]+(self.size[0]/2))*scale)-scrpos[0],((self.pos[1]+(self.size[1]/2))*scale)-scrpos[1]]
                if a[0]==0:
                    col = (255,255,0)
                else:
                    col = (255,0,255)
                for b in a[1]:
                    pygame.draw.line(surf,col,lastPos,[(b[0]*scale)-scrpos[0],(b[1]*scale)-scrpos[1]],4)
                    lastPos = [(b[0]*scale)-scrpos[0],(b[1]*scale)-scrpos[1]]
            for a in self.LINK["drones"]:
                self.linePathVisual([self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2)],[a.pos[0]+(a.size[0]/2),a.pos[1]+(a.size[1]/2)],surf,scrpos,scale)
        if not edit and self.LINK["DEVDIS"]: #Display NPC when in development mode
            self.drawRotate(surf,x-((self.size[0]/2)*scale),y-((self.size[1]/2)*scale),self.getImage("android"),self.angle)
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
