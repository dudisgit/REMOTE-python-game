#Do not run this file, it is a module!
import pygame
import entities.base as base

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["god"] = True
        self.active = False #Is the generator currently on
        self.linkable = ["power"] #A list of names that can connect to this entity
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the generator is inside a room
        self.hintMessage = "A generator powers electronics around the ship and can be accessed using a drone or a ship upgrade. \nIt can power other stuff like doors, rooms, airlocks, etc"
    def __ChangeGod(self,LINK,state): #switches godmode on/off on the generator
        self.settings["god"] = state == True
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["generator",self.ID,self.pos,self.settings["god"]]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["god"] = data[3]
    def loop(self,lag):
        pass
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,100)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Indestructible",self.settings["god"],self.__ChangeGod) #Godmode checkbox
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-150:
            windowPos[1] = self.LINK["reslution"][1]-150
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__check1.render(self.__check1.pos[0],self.__check1.pos[1],1,1,self.__surface) #Render checkbutton
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,208,98],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.HINT = False
        self.__but1 = None
        self.__check1 = None
    def editMove(self,ents): #Generator is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool #Is true if the generator is currently inside a room
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool:
            return "No room (generator)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit:
            if self.__inRoom: #If inside room then show a green icon
                surf.blit(self.getImage("generatorOn"),(x,y))
            else: #else a red.
                surf.blit(self.getImage("generatorDead"),(x,y))
        else:
            if self.active:
                surf.blit(self.getImage("generatorOn"),(x,y))
            else:
                surf.blit(self.getImage("generatorOff"),(x,y))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
