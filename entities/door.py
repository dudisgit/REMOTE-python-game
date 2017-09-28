#Do not run this file, it is a module!
import pygame, time, random
import entities.base as base

RANDOM_DIE = 10 #Percentage change that the door will get destroyed when a room gets vacuumed

class Main(base.Main):
    def __init__(self,x,y,LINK,ID,number=-1):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.number = number #The door number this door is
        self.settings["open"] = False #Door is opened or closed
        self.settings["attack"] = True #Door is attackable
        self.settings["power"] = [] #Contains a list of generators the door is powered by
        self.settings["lr"] = True #This determines the direction of the door (Left right / Up down)
        self.powered = True #If the door is powered on not
        self.trying = False #Is the door trying to close?
        self.__isVac = False #Is outisde the door a vacuum
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the door is inside a room
        self.hintMessage = "A door must be placed between two rooms. It can be opened or closed as long as its powered by a generator or room. \nIf linked to a generator, the rooms next to it will not power it!"
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        pows = []
        for i,a in enumerate(self.settings["power"]):
            try:
                pows.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving power link "+str(i)+"(index) in door "+str(self.ID)+"(ID) failed.")
        return ["door",self.ID,self.pos,self.settings["open"],self.settings["attack"],self.settings["lr"],pows]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["open"] = data[3]
        self.settings["attack"] = data[4]
        self.settings["lr"] = data[5]
        for a in data[6]:
            if a in idRef:
                self.settings["power"].append(idRef[a])
            else:
                self.LINK["errorDisplay"]("Loading power link "+str(a)+"(ID) failed in door "+str(self.ID)+"(ID).")
    def afterLoad(self): #Called after the entity has loaded
        if self.LINK["multi"] != -1: #Is not loaded in map editor
            #This is for finding the connected rooms to this door
            if not self.settings["lr"]:
                self.room1 = self.findPosition([self.pos[0]+25,self.pos[1]-25],[1,1])
                self.room2 = self.findPosition([self.pos[0]+25,self.pos[1]+75],[1,1])
            else:
                self.room1 = self.findPosition([self.pos[0]-25,self.pos[1]+25],[1,1])
                self.room2 = self.findPosition([self.pos[0]+75,self.pos[1]+25],[1,1])
            if self.room1 == -1:
                self.room1 = None
            else:
                self.room1.doors.append(self)
            if self.room2 == -1:
                self.room2 = None
            else:
                self.room2.doors.append(self)
    def SyncData(self,data): #Syncs the data with this drone
        self.settings["open"] = data["O"]
        self.trying = data["T"]
        self.alive = data["A"]
    def GiveSync(self): #Returns the synced data for this drone
        res = {}
        res["O"] = self.settings["open"]
        res["T"] = self.trying
        res["A"] = self.alive
        return res
    def loop2(self,lag): #This is "loop" but will apply actions to the door (single player/server, not client)
        if self.trying and self.powered:
            if len(self.EntitiesInside())==0:
                self.CLOSE()
                self.trying = False
        if not self.room1 is None and not self.room2 is None and self.alive: #Door is valid
            if (not self.room1.air or not self.room2.air) and not self.__isVac: #A room has been vacuumed without the door knowing
                self.__isVac = True
                if random.randint(0,100)<RANDOM_DIE: #Random chance wether the door should be destroyed or not
                    self.alive = False
                    self.LINK["outputCommand"]("Door "+str(self.number)+" has been destroyed due to outside exposure.",(255,0,0))
            elif self.room1.air and self.room2.air:
                self.__isVac = False
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=1: #Is not a client
            self.loop2(lag)
    def toggle(self): #Open/close the door and return any errors
        errs = ""
        if self.powered:
            if self.settings["open"]:
                errs = self.CLOSE()
            else:
                errs = self.OPEN()
        else:
            errs = "Door not powered"
        return errs
    def OPEN(self): #Opens the door
        errs = ""
        if not self.alive:
            errs = "Door has been destroyed"
        elif self.powered:
            self.settings["open"] = True
            self.trying = False
        else:
            errs = "Door not powered"
        return errs
    def CLOSE(self): #Closes the door
        errs = ""
        if not self.alive:
            errs = "Door has been destroyed"
        elif self.powered:
            if len(self.EntitiesInside())!=0:
                errs = "Door is being blocked"
                self.trying = True
            else:
                self.settings["open"] = False
        else:
            errs = "Door not powered"
        return errs
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
        self.__surface = pygame.Surface((210,180)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Open/Close",self.settings["open"],self.__ChangeState) #Door state checkbox
        self.__check3 = self.LINK["screenLib"].CheckButton(5,75,self.LINK,"Attackable",self.settings["attack"],self.__ChangeAttack) #Door attack checkbox
        self.__but2 = self.LINK["screenLib"].Button(5,145,self.LINK,"Link power",self.__LinkTo) #Link button
        self.__but3 = self.LINK["screenLib"].Button(5,110,self.LINK,"Unlink all",self.__UnlinkAll)
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
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
        if windowPos[1]>self.LINK["reslution"][1]-190:
            windowPos[1] = self.LINK["reslution"][1]-190
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__check1.render(self.__check1.pos[0],self.__check1.pos[1],1,1,self.__surface) #Render checkbutton
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
        self.HINT = False
        self.__but1 = None
        self.__check1 = None
        self.__but2 = None
        self.__but3 = None
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
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) != bool: #Check if inside a room
            return "Inside room (door)"
        #Check if next to a room
        romConnect = False
        save = self.settings["lr"] == True
        self.settings["lr"] = False
        self.editMove(ents)
        if self.settings["lr"] != False:
            romConnect = True
        else:
            self.settings["lr"] = True
            self.editMove(ents)
            if self.settings["lr"]!=True:
                romConnect = True
        self.settings["lr"] = save == True
        #Check if connected to a room
        if not romConnect:
            return "No room (door)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.__inRoom and edit:
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
        elif self.LINK["DEVDIS"]: #Development display (used to display door connections
            if not self.settings["lr"]:
                pygame.draw.circle(surf,(255,0,0),[int(x+(25*scale)),int(y-(25*scale))],4)
                pygame.draw.circle(surf,(255,0,0),[int(x+(25*scale)),int(y+(75*scale))],4)
            else:
                pygame.draw.circle(surf,(255,0,0),[int(x-(25*scale)),int(y+(25*scale))],4)
                pygame.draw.circle(surf,(255,0,0),[int(x+(75*scale)),int(y+(25*scale))],4)
            scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
            if not self.room1 is None:
                pygame.draw.line(surf,(255,0,0),[x,y],[(self.room1.pos[0]*scale)-scrpos[0],(self.room1.pos[1]*scale)-scrpos[1]])
            if not self.room2 is None:
                pygame.draw.line(surf,(255,0,0),[x,y],[(self.room2.pos[0]*scale)-scrpos[0],(self.room2.pos[1]*scale)-scrpos[1]])
        if self.alive and not self.powered: #If the door is not powered
            dead = "Power"
        elif not self.alive:
            dead = "Dead"
        if self.settings["open"]: #Door is open
            if self.trying and (time.time()-int(time.time()))>0.5:
                d = 20
            else:
                d = 25
            if self.settings["lr"]: #Left to right
                surf.blit(pygame.transform.rotate(self.getImage("doorOpen"+dead),270),(x,y-(d*scale)))
                surf.blit(pygame.transform.rotate(self.getImage("doorOpen"+dead),90),(x,y+(d*scale)))
            else: #Up to down
                surf.blit(self.getImage("doorOpen"+dead),(x-(d*scale),y))
                surf.blit(pygame.transform.flip(self.getImage("doorOpen"+dead),True,False),(x+(d*scale),y))
            pygame.draw.rect(surf,(150,150,150),[x,y,self.size[0]*scale,self.size[1]*scale]) #Draw grey background when door is open
        else: #Door is closed
            if self.settings["lr"]: #Left to right
                surf.blit(pygame.transform.rotate(self.getImage("doorClosed"+dead),90),(x,y))
            else: #Up to down
                surf.blit(self.getImage("doorClosed"+dead),(x,y))
        if self.number != -1: #Draw the number the door is
            textSurf = self.LINK["font16"].render("D"+str(self.number),16,(255,255,255)) #Create a surface that is the rendered text
            textSize = list(textSurf.get_size()) #Get the size of the text rendered
            textSurf = pygame.transform.scale(textSurf,(int(textSize[0]*scale*1.2),int(textSize[1]*scale*1.2)))
            textSize2 = list(textSurf.get_size()) #Get the size of the text rendered
            pygame.draw.rect(surf,(0,0,0),[x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale)]+textSize2) #Draw a black background for the text to be displayed infront of
            surf.blit(textSurf,(x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale))) #Render text
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
