#Do not run this file, it is a module!
import pygame, time, random
import entities.base as base

RADIATION_DELAY = 6 #Delay until the airlock will fill the room with radiation
AIRLOCK_COL = (255,255,255) #Colour of the airlock

class Main(base.Main):
    def __init__(self,x,y,LINK,ID,number=-1):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.number = number #The door number this door is
        self.settings["open"] = False #Door is opened or closed
        self.settings["power"] = [] #Contains a list of generators the door is powered by
        self.settings["dir"] = 0 #This determines the direction of the airlock
        self.settings["fail"] = False #If the airlock should be allowed to fail
        self.settings["default"] = False #Is the default airlock for ships
        self.powered = False #Is the airlock powered
        self.room1 = None #The room the airlock is attached to.
        self.room2 = None #The room of the ship (will be none if not docked)
        self.trying = False #Is the airlock trying to close
        self.__updateAgain = time.time()+random.randint(4,9) #Time until the door will update all users that its still open/closed
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the door is inside a room
        self.__radFill = 0 #Time until the airlock should fill the room with radiation
        self.hintMessage = "An airlock is like a door but must not conenct two rooms but rather one room to outerspace. \nAn airlock can be made default by using its context/options menu. \nAn airlock also does not need its own power."
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        pows = []
        for i,a in enumerate(self.settings["power"]):
            try:
                pows.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving power link "+str(i)+"(index) in airlock "+str(self.ID)+"(ID) failed.")
        return ["airlock",self.ID,self.pos,self.settings["dir"],self.settings["default"],self.settings["fail"],pows]
    def __roomAddDirection(self,RM): #Adds this door to the rooms door position checking (used for 3D rendering when missing walls for door spaces)
        if self.pos[1]+self.size[1]==RM.pos[1]: #Door is on the TOP side of the room
            RM.dirDoors[0].append(self)
        if self.pos[1]==RM.pos[1]+RM.size[1]: #Door is on the BOTTOM side of the room
            RM.dirDoors[1].append(self)
        if self.pos[0]+self.size[0]==RM.pos[0]: #Door is on the LEFT side of the room
            RM.dirDoors[2].append(self)
        if self.pos[0]==RM.pos[0]+RM.size[0]: #Door is on the RIGHT side of the room
            RM.dirDoors[3].append(self)
        RM.reloadCorners() #Reload the rooms corners for fast rendering
    def afterLoad(self): #Called after the entity has loaded
        if self.LINK["multi"] != -1: #Is not loaded in map editor
            #This is for finding the connected rooms to this door
            if not self.settings["dir"]>=2: #Left to right
                self.room1 = self.findPosition([self.pos[0]+25,self.pos[1]-25],[1,1])
                if self.room1==-1:
                    self.room1 = self.findPosition([self.pos[0]+25,self.pos[1]+75],[1,1])
                elif self.room1.isShipRoom:
                    self.__roomAddDirection(self.room1)
                    self.room2 = self.findPosition([self.pos[0]+25,self.pos[1]-25],[1,1])
                    self.room1 = self.findPosition([self.pos[0]+25,self.pos[1]+75],[1,1])
                else:
                    self.room2 = self.findPosition([self.pos[0]+25,self.pos[1]+75],[1,1])
                    if self.room2 == -1:
                        self.room2 = None
            else:
                self.room1 = self.findPosition([self.pos[0]-25,self.pos[1]+25],[1,1])
                if self.room1==-1:
                    self.room1 = self.findPosition([self.pos[0]+75,self.pos[1]+25],[1,1])
                elif self.room1.isShipRoom:
                    self.room2 = self.findPosition([self.pos[0]-25,self.pos[1]+25],[1,1])
                    self.__roomAddDirection(self.room1)
                    self.room1 = self.findPosition([self.pos[0]+75,self.pos[1]+25],[1,1])
                else:
                    self.room2 = self.findPosition([self.pos[0]+75,self.pos[1]+25],[1,1])
                    if self.room2 == -1:
                        self.room2 = None
            if self.room1 == -1:
                self.room1 = None
                self.LINK["errorDisplay"]("Failed to link airlock to room, outside map? ("+str(self.ID)+")")
            else:
                self.room1.doors.append(self)
                self.__roomAddDirection(self.room1)
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def SyncData(self,data): #Syncs the data with this drone
        self.settings["open"] = data["O"]
        self.powered = data["P"]
        self.trying = data["T"]
    def GiveSync(self): #Returns the synced data for this drone
        res = {}
        res["O"] = self.settings["open"]
        res["T"] = self.trying
        res["P"] = self.powered
        return res
    def loop2(self,lag): #This is "loop" but will apply actions to the airlock (single player/server, not client)
        if self.trying and self.powered:
            if len(self.EntitiesInside())==0:
                self.CLOSE()
                self.trying = False
        if self.LINK["multi"]==2 and time.time()>self.__updateAgain and self.LINK["absoluteDoorSync"]: #Is a server, this will update all users telling them the door is still open
            #This is incase the very unlikely chance the door doesen't sync its open/closed state
            self.__updateAgain = time.time()+random.randint(5,12) #Update again in a random time
            send = [["s",self.settings["open"]==True,"e"+str(self.ID),"O"]]
            for a in self.LINK["serv"].users: #Send data to all users
                self.LINK["serv"].users[a].sendUDP(send)
        self.powered = False
        for a in self.settings["power"]:
            if a.active:
                self.powered = True
                break
        self.powered = self.powered or not self.room2 is None
        if self.LINK["allPower"]:
            self.powered = True
        if time.time()>self.__radFill and self.__radFill!=0: #Fill the room with radiation
            #Find the position of where to start
            if self.settings["dir"]==0:
                POS = [self.pos[0]+25,self.pos[1]+0]
            elif self.settings["dir"]==1:
                POS = [self.pos[0]+25,self.pos[1]+50]
            elif self.settings["dir"]==2:
                POS = [self.pos[0]+0,self.pos[1]+25]
            else:
                POS = [self.pos[0]+50,self.pos[1]+25]
            self.room1.radBurst(POS) #Start the radiation
            self.__radFill = 0
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=1: #Is not a client
            self.loop2(lag)
    def toggle(self): #Open/close the airlock and return any errors
        errs = ""
        if self.powered:
            if self.settings["open"]:
                errs = self.CLOSE()
            else:
                errs = self.OPEN()
        else:
            errs = "Airlock not powered"
        return errs
    def OPEN(self): #Opens the door
        errs = ""
        if self.powered: #Airlock is powered
            if not self.room2 is None: #Ship is docked to airlock
                if self.room2.ship.dockTime!=0: #Ship is still docking to airlock
                    return "Ship is still docking to airlock"
            else:
                if self.settings["dir"]==0:
                    POS = [self.pos[0]+25,self.pos[1]+0]
                elif self.settings["dir"]==1:
                    POS = [self.pos[0]+25,self.pos[1]+50]
                elif self.settings["dir"]==2:
                    POS = [self.pos[0]+0,self.pos[1]+25]
                else:
                    POS = [self.pos[0]+50,self.pos[1]+25]
                self.room1.airBurst(POS,"/"+str(self.ID),self)
                self.__radFill = time.time()+RADIATION_DELAY #Delay radiation filling
            self.settings["open"] = True
            self.trying = False
        else:
            errs = "Airlock not powered"
        return errs
    def CLOSE(self): #Closes the door
        errs = ""
        if self.powered:
            if len(self.EntitiesInside())!=0:
                errs = "Airlock is being blocked"
                self.trying = True
            else:
                self.settings["open"] = False
                self.__radFill = 0 #Stop any radiation filling
        else:
            errs = "Airlock not powered"
        return errs
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
        elif self.LINK["DEVDIS"]: #Development display (used to display door connections
            if not self.settings["dir"]>=2:
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
        if self.settings["open"]: #Airlock is open
            if self.trying and (time.time()-int(time.time()))>0.5:
                d = 20
            else:
                d = 25
            if self.settings["dir"]>=2: #Left to right
                surf.blit(pygame.transform.rotate(self.getImage("doorAirOpen"+dead),270),(x,y-(d*scale)))
                surf.blit(pygame.transform.rotate(self.getImage("doorAirOpen"+dead),90),(x,y+(d*scale)))
            else: #Up to down
                surf.blit(self.getImage("doorAirOpen"+dead),(x-(d*scale),y))
                surf.blit(pygame.transform.flip(self.getImage("doorAirOpen"+dead),True,False),(x+(d*scale),y))
            pygame.draw.rect(surf,(150,150,150),[x,y,self.size[0]*scale,self.size[1]*scale]) #Draw grey background when door is open
        else: #Airlock is closed
            if self.settings["dir"]>=2: #Lef to right
                surf.blit(pygame.transform.rotate(self.getImage("doorAirClosed"+dead),90),(x,y))
            else: #Up to down
                surf.blit(self.getImage("doorAirClosed"+dead),(x,y))
        if self.number != -1: #Draw the number the airlock is
            textSurf = self.LINK["font16"].render("A"+str(self.number),16,(255,255,255)) #Create a surface that is the rendered text
            textSize = list(textSurf.get_size()) #Get the size of the text rendered
            textSurf = pygame.transform.scale(textSurf,(int(textSize[0]*scale*1.2),int(textSize[1]*scale*1.2)))
            textSize2 = list(textSurf.get_size()) #Get the size of the text rendered
            pygame.draw.rect(surf,(0,0,0),[x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale)]+textSize2) #Draw a black background for the text to be displayed infront of
            surf.blit(textSurf,(x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale))) #Render text
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,Dview=False): #Should the airlock render in scematic view
        return not Dview
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render the airlock in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        if self.LINK["simpleModels"]:
            simp = "Simple"
        else:
            simp = ""
        C = (255,255,255)
        if self.trying and (time.time()-int(time.time()))>0.5: #Airlock is trying to open/close
            C = (255,255,0)
        elif not self.alive:
            C = (255,0,0)
        if self.number != -1: #Draw the number the airlock is
            textSurf = self.LINK["font16"].render("A"+str(self.number),16,C) #Create a surface that is the rendered text
            textSize = list(textSurf.get_size()) #Get the size of the text rendered
            textSurf = pygame.transform.scale(textSurf,(int(textSize[0]*scale*1.2),int(textSize[1]*scale*1.2)))
            textSize2 = list(textSurf.get_size()) #Get the size of the text rendered
            pygame.draw.rect(surf,(0,0,0),[x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale)]+textSize2) #Draw a black background for the text to be displayed infront of
            surf.blit(textSurf,(x+(((self.size[0]/2)-(textSize[0]/2))*scale),y+((self.size[1]/4)*scale))) #Render text
        if self.settings["open"]: #Airlock is open
            if self.settings["dir"]>=2: #Airlock is left to right
                self.LINK["render"].renderModel(self.LINK["models"]["doorOpen"],x+(20*scale),y+(22*scale),0,scale/2.5,surf,AIRLOCK_COL,ang,eAng,arcSiz)
            else: #Airlock is up to down
                self.LINK["render"].renderModel(self.LINK["models"]["doorOpen"],x+(20*scale),y+(30*scale),90,scale/2.5,surf,AIRLOCK_COL,ang,eAng,arcSiz)
        else: #Airlock is closed
            if self.settings["dir"]>=2: #Airlock is left to right
                if ((self.settings["dir"]==2 and not self.room2 is None) or self.settings["dir"]==3) and x<sx/2:
                    self.LINK["render"].renderModel(self.LINK["models"]["doorClose"+simp],x+(14.5*scale),y+(22*scale),0,scale/2.5,surf,AIRLOCK_COL,ang,eAng,arcSiz)
                if ((self.settings["dir"]==3 and not self.room2 is None) or self.settings["dir"]==2) and x>=sx/2:
                    self.LINK["render"].renderModel(self.LINK["models"]["doorClose"+simp],x+(36*scale),y+(26*scale),180,scale/2.5,surf,AIRLOCK_COL,ang,eAng,arcSiz)
            else: #Airlock is up to down
                if ((self.settings["dir"]==1 and not self.room2 is None) or self.settings["dir"]==0) and y>sy/2:
                    self.LINK["render"].renderModel(self.LINK["models"]["doorClose"+simp],x+(23*scale),y+(36*scale),90,scale/2.5,surf,AIRLOCK_COL,ang,eAng,arcSiz)
                if ((self.settings["dir"]==0 and not self.room2 is None) or self.settings["dir"]==1) and y<=sy/2:
                    self.LINK["render"].renderModel(self.LINK["models"]["doorClose"+simp],x+(26*scale),y+(16*scale),270,scale/2.5,surf,AIRLOCK_COL,ang,eAng,arcSiz)
