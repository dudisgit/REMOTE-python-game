#Do not run this file, it is a module!
import pygame
import entities.base as base

FUEL_COL = (0,204,255)

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["god"] = False
        self.used = False #Has the fuel outlet been used by a drone.
        self.renderSize = [-60,-60,110,110] #Used to have a bigger radius when rendering in 3D (does not effect scale)
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]:
                simp = "Simple"
            else:
                simp = ""
            self.__fuel = LINK["render"].Model(LINK,"fuel"+simp)
            self.__fuelWall = LINK["render"].Model(LINK,"fuelWall"+simp)
        self.__wallAngle = -1 #Wall angle the interface is laying on, left, right, up, down
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the fuel outlet is inside a room
        self.hintMessage = "Fuel outlets can be collected by drones to allow the player to move forward to different ships. \nUnless godmode is turned on, they can be destroyed by air locks."
        self.gameHint = "Use 'gather' upgrade to interact. \nWill gather fuel to use for more ships"
        if self.LINK["multi"]!=-1 and self.LINK["hints"]:
            self.HINT = True #Show hints
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["fuel",self.ID,self.pos,self.settings["god"]==True]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["god"] = data[3]
    def SyncData(self,data): #Syncs the data with this lure
        self.used = data["U"]
        self.discovered = data["D"]
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
    def GiveSync(self): #Returns the synced data for this lure
        res = {}
        res["U"] = self.used
        res["D"] = self.discovered
        return res
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=2 and self.HINT: #Is not server
            if self.used and not "fuel" in self.LINK["hintDone"]:
                self.HINT = False
                self.LINK["hintDone"].append("fuel")
            if "fuel" in self.LINK["hintDone"]:
                self.HINT = False
    def __ChangeGod(self,LINK,state):
        self.settings["god"] = state == True
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,80)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Destructable",self.settings["god"],self.__ChangeGod) #Destructable checkbox
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
        if windowPos[1]>self.LINK["reslution"][1]-90:
            windowPos[1] = self.LINK["reslution"][1]-90
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__check1.render(self.__check1.pos[0],self.__check1.pos[1],1,1,self.__surface) #Render checkbutton
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
    def editMove(self,ents): #Fuel outlet is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (fuel outlet)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit:
            if self.__inRoom:
                surf.blit(self.getImage("fuelAlive"),(x,y))
            else:
                surf.blit(self.getImage("fuelDead"),(x,y))
        else:
            if self.alive:
                if self.used:
                    surf.blit(self.getImage("fuelUsed"),(x,y))
                else:
                    surf.blit(self.getImage("fuelAlive"),(x,y))
            else:
                surf.blit(self.getImage("fuelDead"),(x,y))
        if self.HINT and self.LINK["multi"]==-1:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,Dview=False,arcSiz=-1): #Should the generator render in scematic view
        return not Dview
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render the fuel port in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        if self.__wallAngle==-1:
            self.__fuel.render(x+(25*scale),y+(12*scale),0,scale/2.5,surf,FUEL_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(25*scale),y+(25*scale)])
        elif self.__wallAngle==0: #Left
            self.__fuelWall.render(x+(23*scale),y+(12.5*scale),270,scale/2.5,surf,FUEL_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x,y+(25*scale)])
        elif self.__wallAngle==1: #Right
            self.__fuelWall.render(x+(25*scale),y+(18*scale),90,scale/2.5,surf,FUEL_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(50*scale),y+(25*scale)])
        elif self.__wallAngle==2: #Up
            self.__fuelWall.render(x+(18*scale),y+(23*scale),180,scale/2.5,surf,FUEL_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(20*scale),y])
        elif self.__wallAngle==3: #Down
            self.__fuelWall.render(x+(18*scale),y+(27*scale),0,scale/2.5,surf,FUEL_COL,ang,eAng,arcSiz)
            if self.HINT:
                self.renderHint(surf,self.gameHint,[x+(20*scale),y+(50*scale)])
