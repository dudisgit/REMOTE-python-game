#Do not run this file, it is a module!
import pygame, random
import entities.base as base

RANDOM_DIE = 30 #Percentage chance the interface will be destroyed when the room is vacuumed
INTERFACE_COL = (0,204,255) #Colour of the interface when rendered in 3D

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["god"] = True #Interface is indestructable
        self.settings["scan"] = False #Is the interface allowed to scan a room
        self.settings["power"] = [] #Contains a list of generators the interface is powered by
        self.turrets = [] #Turrets that are linked to this interface (appended by the turrets)
        self.defence = False #Activate/deactivate defences
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]:
                simp = "Simple"
            else:
                simp = ""
            self.__interfaceWall = LINK["render"].Model(LINK,"interfaceWall"+simp)
            self.__interface = LINK["render"].Model(LINK,"interface"+simp)
        self.linkable = ["inter"] #Make the interface accept link upgrades
        self.__sShow = True #Show in games scematic view
        self.__wallAngle = -1 #Wall angle the interface is laying on, left, right, up, down
        self.__inRoom = False #Is true if the interface is inside a room
        self.__isVac = False #Used to detect change in air pressure inside the current room
        self.powered = False #Is this interface powered or not
        self.hintMessage = "An interface can be used to controll turrets or survey the ship. They must be powered and can be accessed using the interface upgrade on a drone."
        self.gameHint = "Use 'interface' upgrade to interact. \nWill controll ship defences and survey rooms"
        if self.LINK["multi"]!=-1 and self.LINK["hints"]:
            self.HINT = True #Show hints
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        pows = []
        for i,a in enumerate(self.settings["power"]):
            try:
                pows.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving power link "+str(i)+"(index) in interface "+str(self.ID)+"(ID) failed.")
        return ["interface",self.ID,self.pos,self.settings["god"],self.settings["scan"],pows]
    def toggleDefence(self): #Toggle defences on/off
        self.defence = not self.defence
    def scanShip(self): #Scans all the ships rooms, like a survayor
        self.LINK["showRooms"] = True
    def afterLoad(self):
        self.__curRoom = self.findPositionAbsolute()
        if self.pos[0]==self.__curRoom.pos[0]:
            self.__wallAngle = 0
        elif self.pos[0]+self.size[0]==self.__curRoom.pos[0]+self.__curRoom.size[0]:
            self.__wallAngle = 1
        elif self.pos[1]==self.__curRoom.pos[1]:
            self.__wallAngle = 2
        elif self.pos[1]+self.size[1]==self.__curRoom.pos[1]+self.__curRoom.size[1]:
            self.__wallAngle = 3
    def loop2(self,lag): #Ran if single player or server
        self.powered = False #Make the interface unpowered
        if len(self.settings["power"])==0 and type(self.__curRoom)==self.getEnt("room"): #Check if either room is powered
            self.powered = self.__curRoom.powered == True #Base interface's power on the room its in
        else: #Check all power connections if this interface is powered
            for a in self.settings["power"]: #Go through all generators this upgrade is linked to to find one that is active
                if a.active:
                    self.powered = True
                    break
        if type(self.__curRoom)==self.getEnt("room"):
            if self.__curRoom.air != self.__isVac and self.alive:
                self.__isVac = self.__curRoom.air == True
                if not self.__isVac and random.randint(0,100)<RANDOM_DIE and not self.settings["god"]: #Destroy the generator
                    self.alive = False
                    self.LINK["outputCommand"]("Interface in "+self.__curRoom.reference()+" has been destroyed due to outside exposure.",(255,0,0),False)
    def SyncData(self,data): #Syncs the data with this interface
        self.alive = data["A"]
        self.discovered = data["D"]
        self.powered = data["P"]
    def GiveSync(self): #Returns the synced data for this interface
        res = {}
        res["A"] = self.alive
        res["D"] = self.discovered
        res["P"] = self.powered
        return res
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=1: #Single player or server
            self.loop2(lag)
        if self.LINK["multi"]!=2 and self.HINT: #Is not server
            if "inter" in self.LINK["hintDone"] or (self.LINK["multi"]==1 and self.powered):
                self.HINT = False
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["god"] = data[3]
        self.settings["scan"] = data[4]
        for a in data[5]:
            if a in idRef:
                self.settings["power"].append(idRef[a])
            else:
                self.LINK["errorDisplay"]("Loading power link "+str(a)+"(ID) failed in interface "+str(self.ID)+"(ID).")
    def __ChangeGod(self,LINK,state): #switches godmode on the interface
        self.settings["god"] = state == True
    def __LinkTo(self,LINK): #"Link to" button was pressed
        LINK["currentScreen"].linkItem(self,"power") #A bit bodgy but this can only be called in the map designer.
    def __ChangeScan(self,LINK,state): #switches the scannable mode on the interface
        self.settings["scan"] = state == True
    def __UnlinkAll(self,LINK): #Deletes all links on this entity
        self.settings["power"] = []
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,180)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Indestructable",self.settings["god"],self.__ChangeGod) #Generator godmode checkbox
        self.__check3 = self.LINK["screenLib"].CheckButton(5,75,self.LINK,"Ship survey command",self.settings["scan"],self.__ChangeScan) #Scan command checkbox
        self.__but2 = self.LINK["screenLib"].Button(5,145,self.LINK,"Link power",self.__LinkTo) #Link power button
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
    def editMove(self,ents): #Interface is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (interface)"
        elif len(self.settings["power"])==0:
            return "No power (interface)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit: #Draw all the power lines
            scrolPos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Calculate the scroll position
            rem = [] #Items to remove because they where deleted
            for a in self.settings["power"]: #Loop through all the power lines to render them
                pygame.draw.line(surf,(100,0,100),[x+(self.size[0]*0.5*scale),y+(self.size[1]*0.5*scale)],
                                                    [((a.pos[0]+(a.size[0]/2))*scale)-scrolPos[0],((a.pos[1]+(a.size[1]/2))*scale)-scrolPos[1]],3)
                if a.REQUEST_DELETE: #Entity is has been deleted (this entity is keeping it alive with its pointer)
                    rem.append(a)
            for a in rem: #Loop through all the entities wanted to be deleted
                self.settings["power"].remove(a)
        if edit:
            if self.__inRoom:
                surf.blit(self.getImage("interface"),(x,y))
            else:
                surf.blit(self.getImage("interfaceDead"),(x,y))
        else:
            if self.alive: #Interface is alive
                D = ""
            else: #Interface is dead
                D = "Dead"
            if self.__wallAngle==-1: #Not againsed a wall
                surf.blit(self.getImage("interface"+D),(x,y))
            elif self.__wallAngle==0: #Left
                surf.blit(self.getImage("interfaceWall"+D),(x,y))
            elif self.__wallAngle==1: #Right
                surf.blit(pygame.transform.rotate(self.getImage("interfaceWall"+D),180),(x,y))
            elif self.__wallAngle==2: #Up
                surf.blit(pygame.transform.rotate(self.getImage("interfaceWall"+D),90),(x,y-(25*scale)))
            elif self.__wallAngle==3: #Down
                surf.blit(pygame.transform.rotate(self.getImage("interfaceWall"+D),270),(x,y+(25*scale)))
        if self.HINT and self.LINK["multi"]==-1:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,Dview=False,arcSiz=-1): #Should the generator render in scematic view
        return not Dview
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render the interface in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        if self.__wallAngle==-1:
            self.__interface.render(x+(25*scale),y+(12*scale),0,scale/2,surf,INTERFACE_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(25*scale),y+(25*scale)])
        elif self.__wallAngle==0: #Left
            self.__interfaceWall.render(x+(12*scale),y+(12.5*scale),90,scale/1.6,surf,INTERFACE_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x,y+(25*scale)])
        elif self.__wallAngle==1: #Right
            self.__interfaceWall.render(x+(40*scale),y+(12.5*scale),270,scale/1.6,surf,INTERFACE_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(50*scale),y+(25*scale)])
        elif self.__wallAngle==2: #Up
            self.__interfaceWall.render(x+(18*scale),y+(12.5*scale),0,scale/1.6,surf,INTERFACE_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(20*scale),y])
        elif self.__wallAngle==3: #Down
            self.__interfaceWall.render(x+(18*scale),y+(40*scale),180,scale/1.6,surf,INTERFACE_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(20*scale),y+(50*scale)])
