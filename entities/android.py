#Do not run this file, it is a module!
import pygame, time
import entities.base as base

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.isNPC = True
        self.health = 80
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the NPC is inside a room
        self.hintMessage = "An android is easy to deal with. It is slower than drones and deals minimal damage. \nIt cannot attack doors"
    def takeDamage(self,dmg,reason=""):
        self.health -= dmg
        if self.health<0:
            self.health = 0
            self.alive = False
        return self.health == 0
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["android",self.ID,self.pos]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
    def loop(self,lag):
        pass
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
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
