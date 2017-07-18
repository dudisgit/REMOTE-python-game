#Do not run this file, it is a module!
import pygame
import entities.base as base

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["open"] = False #Door is opened or closed
        self.settings["power"] = [] #Contains a list of generators the door is powered by
        self.settings["dir"] = 0 #This determines the direction of the airlock
        self.settings["fail"] = False #If the airlock should be allowed to fail
        self.settings["default"] = False #Is the default airlock for ships
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the door is inside a room
        self.hintMessage = "An airlock is like a door but must not conenct two rooms but rather one room to outerspace. \nAn airlock can be made default by using its context/options menu. \nAn airlock also does not need its own power."
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        pows = []
        for i,a in enumerate(self.settings["power"]):
            try:
                pows.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving power link "+str(i)+"(index) in airlock "+str(self.ID)+"(ID) failed.")
        return ["airlock",self.ID,self.pos,self.settings["dir"],self.settings["default"],self.settings["fail"],pows]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["dir"] = data[3]
        self.settings["default"] = data[4]
        self.settings["fail"] = data[5]
        for a in data[6]:
            if a in idRef:
                self.settings["power"].append(idRef[a])
            else:
                self.LINK["errorDisplay"]("Loading power link "+str(a)+"(ID) failed in airlock "+str(self.ID)+"(ID).")
    def __MakeDefault(self,LINK): #Makes the airlock the default airlock to connect to.
        LINK["currentScreen"].noDefault()
        self.settings["default"] = True
    def __ChangeFail(self,LINK,state):
        self.settings["fail"] = state == True
    def __LinkTo(self,LINK): #"Link to" button was pressed
        LINK["currentScreen"].linkItem(self,"power") #A bit bodgy but this can only be called in the map designer.
    def __UnlinkAll(self,LINK): #Deletes all links on this entity
        self.settings["power"] = []
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,180)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].Button(5,40,self.LINK,"Make default",self.__MakeDefault) #Airlock default checkbox
        self.__but2 = self.LINK["screenLib"].Button(5,110,self.LINK,"Link power",self.__LinkTo) #Link button
        self.__but3 = self.LINK["screenLib"].Button(5,75,self.LINK,"Unlink all",self.__UnlinkAll)
        self.__check2 = self.LINK["screenLib"].CheckButton(5,145,self.LINK,"Fail",self.settings["fail"],self.__ChangeFail)
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but2.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__but3.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check2.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-190:
            windowPos[1] = self.LINK["reslution"][1]-190
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__check1.render(self.__check1.pos[0],self.__check1.pos[1],1,1,self.__surface) #Render checkbutton
        self.__check2.render(self.__check2.pos[0],self.__check2.pos[1],1,1,self.__surface) #Render checkbutton
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
        self.HINT = False
        self.__but1 = None
        self.__check1 = None
        self.__check2 = None
        self.__but2 = None
        self.__but3 = None
    def editMove(self,ents): #Room is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
        if type(self.insideRoom(ents,[self.pos[0]+25,self.pos[1]-25],[0,0])) != bool:
            self.settings["dir"] = 0 #Up
        elif type(self.insideRoom(ents,[self.pos[0]+25,self.pos[1]+75],[0,0])) != bool:
            self.settings["dir"] = 1 #Down
        elif type(self.insideRoom(ents,[self.pos[0]-25,self.pos[1]+25],[0,0])) != bool:
            self.settings["dir"] = 2 #Left
        elif type(self.insideRoom(ents,[self.pos[0]+75,self.pos[1]+25],[0,0])) != bool:
            self.settings["dir"] = 3 #Right
        else:
            self.settings["dir"] = -1 #None
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) != bool: #Check if inside a room
            return "Inside room (airlock)"
        #Check if connected to a room
        if self.settings["dir"]==-1:
            return "No room (airlock)"
        return False
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
            if self.settings["default"]: #Is the default airlock
                if self.settings["dir"] == 1: #Down
                    surf.blit(pygame.transform.rotate(self.getImage("ship"),180),(x-(83*scale),y-(250*scale)))
                elif self.settings["dir"] == 0: #Up
                    surf.blit(self.getImage("ship"),(x-(125*scale),y+(50*scale)))
                elif self.settings["dir"] == 2: #Left
                    surf.blit(pygame.transform.rotate(self.getImage("ship"),90),(x+(50*scale),y-(83*scale)))
                elif self.settings["dir"] == 3: #Right
                    surf.blit(pygame.transform.rotate(self.getImage("ship"),270),(x-(250*scale),y-(125*scale)))
        if self.settings["open"]:
            if self.settings["dir"]>=2:
                surf.blit(pygame.transform.rotate(self.getImage("doorAirOpen"+dead),270),(x,y-(25*scale)))
                surf.blit(pygame.transform.rotate(self.getImage("doorAirOpen"+dead),90),(x,y+(25*scale)))
            else:
                surf.blit(self.getImage("doorOpen"+dead),(x-(25*scale),y))
                surf.blit(pygame.transform.flip(self.getImage("doorAirOpen"+dead),True,False),(x+(25*scale),y))
        else:
            if self.settings["dir"]>=2:
                surf.blit(pygame.transform.rotate(self.getImage("doorAirClosed"+dead),90),(x,y))
            else:
                surf.blit(self.getImage("doorAirClosed"+dead),(x,y))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
