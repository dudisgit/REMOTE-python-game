#Do not run this file, it is a module!
import pygame
import entities.base as base

class Main(base.Main):
    def __init__(self,x,y,LINK):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.settings["open"] = False #Door is opened or closed
        self.settings["attack"] = True #Door is attackable
        self.settings["power"] = [] #Contains a list of generators the door is powered by
        self.settings["lr"] = True #This determines the direction of the door (Left right / Up down)
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the door is inside a room
    def __ChangeState(self,LINK,state): #switches door state
        self.settings["open"] = state == True
    def __ChangeDirection(self,LINK,state): #switches doors state
        self.settings["lr"] = state == True
    def __ChangeAttack(self,LINK,state): #switches doors attackable
        self.settings["attack"] = state == True
    def __LinkTo(self,LINK): #"Link to" button was pressed
        LINK["currentScreen"].linkItem(self,"power") #A bit bodgy but this can only be called in the map designer.
    def __UnlinkAll(self,LINK): #Deletes all links on this entity
        self.settings["power"] = []
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,215)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Open/Close",self.settings["open"],self.__ChangeState) #Door state checkbox
        self.__check2 = self.LINK["screenLib"].CheckButton(5,75,self.LINK,"Direction",self.settings["lr"],self.__ChangeDirection) #Door direction checkbox
        self.__check3 = self.LINK["screenLib"].CheckButton(5,145,self.LINK,"Attackable",self.settings["attack"],self.__ChangeAttack) #Door attack checkbox
        self.__but2 = self.LINK["screenLib"].Button(5,110,self.LINK,"Link power",self.__LinkTo) #Link button
        self.__but3 = self.LINK["screenLib"].Button(5,180,self.LINK,"Unlink all",self.__UnlinkAll)
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check2.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check3.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but2.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but3.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-240:
            windowPos[1] = self.LINK["reslution"][1]-240
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__check1.render(self.__check1.pos[0],self.__check1.pos[1],1,1,self.__surface) #Render checkbutton
        self.__check2.render(self.__check2.pos[0],self.__check2.pos[1],1,1,self.__surface) #Render checkbutton
        self.__check3.render(self.__check3.pos[0],self.__check3.pos[1],1,1,self.__surface) #Render checkbutton
        self.__but2.render(self.__but2.pos[0],self.__but2.pos[1],1,1,self.__surface) #Render link button
        self.__but3.render(self.__but3.pos[0],self.__but3.pos[1],1,1,self.__surface) #Render unlink button
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,208,surfSize[1]-3],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.__but1 = None
        self.__check1 = None
        self.__but2 = None
        self.__but3 = None
        self.__check2 = None
        self.__check3 = None
    def editMove(self,ents): #Room is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
        if type(self.insideRoom(ents,[self.pos[0]+25,self.pos[1]-25],[0,0])) != bool:
            self.settings["lr"] = False
        elif type(self.insideRoom(ents,[self.pos[0]+25,self.pos[1]+75],[0,0])) != bool:
            self.settings["lr"] = False
        elif type(self.insideRoom(ents,[self.pos[0]-25,self.pos[1]+25],[0,0])) != bool:
            self.settings["lr"] = True
        elif type(self.insideRoom(ents,[self.pos[0]+75,self.pos[1]+25],[0,0])) != bool:
            self.settings["lr"] = True
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.__inRoom:
            dead = "Dead"
        else:
            dead = ""
        if edit: #Draw all the power lines
            scrolPos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Calculate the scroll position
            rem = [] #Items to remove because they where deleted
            for a in self.settings["power"]: #Loop through all the power lines an render them
                pygame.draw.line(surf,(100,0,100),[x+(self.size[0]*0.5*scale),y+(self.size[1]*0.5*scale)],
                                                    [((a.pos[0]+(a.size[0]/2))*scale)-scrolPos[0],((a.pos[1]+(a.size[1]/2))*scale)-scrolPos[1]],3)
                if a.REQUEST_DELETE: #Entity is has been deleted (this entity is keeping it alive with its pointer)
                    rem.append(a)
            for a in rem: #Loop through all the entities wanted to be deleted
                self.settings["power"].remove(a)
        if self.settings["open"]:
            if self.settings["lr"]:
                surf.blit(pygame.transform.rotate(self.getImage("doorOpen"+dead),270),(x,y-(25*scale)))
                surf.blit(pygame.transform.rotate(self.getImage("doorOpen"+dead),90),(x,y+(25*scale)))
            else:
                surf.blit(self.getImage("doorOpen"+dead),(x-(25*scale),y))
                surf.blit(pygame.transform.flip(self.getImage("doorOpen"+dead),True,False),(x+(25*scale),y))
        else:
            if self.settings["lr"]:
                surf.blit(pygame.transform.rotate(self.getImage("doorClosed"+dead),90),(x,y))
            else:
                surf.blit(self.getImage("doorClosed"+dead),(x,y))
