#Do not run this file, it is a module!
import pygame, random
import entities.base as base

RANDOM_DIE = 30 #Percentage chance the generator will be destroyed when the room is vacuumed
GENERATOR_COL = (0,204,255) #Colour of the generator when rendered in 3D

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["god"] = True
        self.active = False #Is the generator currently on
        self.linkable = ["power"] #A list of names that can connect to this entity
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]:
                self.__gen = LINK["render"].Model(LINK,"generatorSimple")
            else:
                self.__gen = LINK["render"].Model(LINK,"generator")
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the generator is inside a room
        self.__isVac = False #Used to detect changes in room pressure
        self.__curRoom = None #Room the generator is in
        self.hintMessage = "A generator powers electronics around the ship and can be accessed using a drone or a ship upgrade. \nIt can power other stuff like doors, rooms, airlocks, etc"
        self.gameHint = "Use 'generator' upgrade to interact. \nWill power rooms and equipment."
        if self.LINK["multi"]!=-1 and self.LINK["hints"]:
            self.HINT = True #Show hints
    def __ChangeGod(self,LINK,state): #switches godmode on/off on the generator
        self.settings["god"] = state == True
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["generator",self.ID,self.pos,self.settings["god"]]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["god"] = data[3]
    def afterLoad(self):
        self.__curRoom = self.findPositionAbsolute()
    def SyncData(self,data): #Syncs the data with this drone
        self.active = data["O"]
        self.alive = data["A"]
        self.discovered = data["D"]
    def GiveSync(self): #Returns the synced data for this drone
        res = {}
        res["O"] = self.active
        res["A"] = self.alive
        res["D"] = self.discovered
        return res
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if not self.alive:
            self.active = False
        if self.LINK["multi"]!=1 and type(self.__curRoom)==self.getEnt("room"): #Is not a client, single player or server
            if self.__curRoom.air != self.__isVac and self.alive:
                self.__isVac = self.__curRoom.air == True
                if not self.__isVac and random.randint(0,100)<RANDOM_DIE and not self.settings["god"]: #Destroy the generator
                    self.alive = False
                    self.active = False
                    self.LINK["outputCommand"]("Generator in "+self.__curRoom.reference()+" has been destroyed due to outside exposure.",(255,0,0),False)
            if self.LINK["allPower"]:
                self.active = True
        if self.LINK["multi"]!=2: #Is not server
            if "gen" in self.LINK["hintDone"] or (self.LINK["multi"]==1 and self.active):
                self.HINT = False
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
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit:
            if self.__inRoom: #If inside room then show a green icon
                surf.blit(self.getImage("generatorOn"),(x,y))
            else: #else a red.
                surf.blit(self.getImage("generatorDead"),(x,y))
        else:
            if not self.alive:
                surf.blit(self.getImage("generatorDead"),(x,y))
            elif self.active:
                surf.blit(self.getImage("generatorOn"),(x,y))
            else:
                surf.blit(self.getImage("generatorOff"),(x,y))
        if self.HINT and self.LINK["multi"]==-1:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,Dview=False): #Should the generator render in scematic view
        return not Dview
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render generator in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        self.__gen.render(x+(25*scale),y+(25*scale),0,scale/1.5,surf,GENERATOR_COL,ang,eAng,arcSiz)
        if self.HINT:
            self.renderHint(surf,self.gameHint,[x+(25*scale),y+(50*scale)])
