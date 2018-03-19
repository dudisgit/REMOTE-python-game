#Do not run this file, it is a module!
import pygame, random, math
import entities.base as base

UPG_COL = (0,204,255)
DISCONNECT_DIST = 40
SPARK_SIZE = 0.5

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the upgrade slot is inside a room
        self.settings["perm"] = False #Is perminantly installed
        self.settings["upgrade"] = "Empty" #What upgrade this supplies
        self.__upg = None #Ship upgrade entity
        self.__upgPos = None
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]:
                simp = "Simple"
            else:
                simp = ""
            self.__upgMod = LINK["render"].Model(LINK,"upgradeSlot"+simp)
            self.__upgBroken = LINK["render"].Model(LINK,"upgradeSlotBroken"+simp)
        self.__used = False
        self.__particle = None
        self.hintMessage = "This is to give the player new ship upgrades. It can be destroyed or sucked out of an airlock."
        self.gameHint = "Use 'tow' upgrade to interact. \nTow upgrade into ship room."
        if self.LINK["multi"]!=-1 and self.LINK["hints"]:
            self.HINT = True #Show hints
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["upgrade slot",self.ID,self.pos,self.settings["perm"],self.settings["upgrade"]]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["perm"] = data[3]
        self.settings["upgrade"] = data[4]
        if self.LINK["multi"]==0 or self.LINK["multi"]==2: #Is single player or server
            #Create the upgrade in this slot
            if data[4]!="Empty":
                self.__upg = self.LINK["create"]("ShipUpgrade",[self.pos[0]+(self.size[0]/4),self.pos[1]+(self.size[1]/4)],data[4],self.settings["perm"])
                self.__upgPos = [self.__upg.pos[0]+0,self.__upg.pos[1]+0]
                self.__upg.upg_typ = data[4]
    def __renderParticle(self,x,y,scale,alpha,surf,a):
        pygame.draw.line(surf,(255,255,0),[x-(math.cos(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3]),y-(math.sin(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3])],[x+(math.cos(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3]),y+(math.sin(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3])],int(1*scale))
    def SyncData(self,data): #Syncs the data with this upgrade
        if data["U"]!=self.__used:
            if data["U"] and self.LINK["particles"]:
                self.__particle = self.LINK["render"].ParticleEffect(self.LINK,self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2),0,360,12,0.8,5,0.5,3,1)
                self.__particle.renderParticle = self.__renderParticle
        self.discovered = data["D"]
        self.__used = data["U"]
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def GiveSync(self): #Returns the synced data for this upgrade
        res = {}
        res["U"] = self.__used
        res["D"] = self.discovered
        return res
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if not self.__used and not self.__upg is None and self.settings["upgrade"]!="Empty":
            dis = math.sqrt(((self.__upg.pos[0]-self.__upgPos[0])**2)+((self.__upg.pos[1]-self.__upgPos[1])**2))
            if dis>DISCONNECT_DIST:
                self.__used = True
                if self.LINK["particles"]: #Particles are enabled
                    self.__particle = self.LINK["render"].ParticleEffect(self.LINK,self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2),0,360,12,0.8,5,0.5,3,1)
                    self.__particle.renderParticle = self.__renderParticle
        if not self.LINK["multi"]==2: #Is not a server
            if not self.__particle is None: #Event loop for particle system if the android is dead
                self.__particle.loop(lag)
        if self.LINK["multi"]!=2 and self.HINT: #Is not server
            if self.__used and not "upg" in self.LINK["hintDone"]:
                self.HINT = False
                self.LINK["hintDone"].append("upg")
            if "upg" in self.LINK["hintDone"]:
                self.HINT = False
    def __ChangePerm(self,LINK,state): #Change if the upgrade slot should be perminantly installed or not
        self.settings["perm"] = state == True
        self.angle = random.randint(0,360)
    def __ChangeUpgrade(self,LINK,upg):
        self.settings["upgrade"] = upg+""
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((280,110)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Permanatly installed",self.settings["perm"],self.__ChangePerm)
        #Get all the possible entities
        adding = ["Empty"]
        for a in self.LINK["shipUp"]:
            adding.append(a)
        self.__cbox = self.LINK["screenLib"].ComboBox(5,75,self.LINK,260,adding,self.__ChangeUpgrade) #Combo box
        self.__cbox.select = adding.index(self.settings["upgrade"])
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__cbox.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
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
        self.__check.render(self.__check.pos[0],self.__check.pos[1],1,1,self.__surface) #Render checkbutton
        self.__cbox.render(self.__cbox.pos[0],self.__cbox.pos[1],1,1,self.__surface) #Render combo box
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,278,surfSize[1]-3],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.HINT = False
        self.__but1 = None
        self.__check = None
        self.__cbox = None
    def editMove(self,ents): #The upgrade slot is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (upgrade slot)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit:
            if self.__inRoom:
                surf.blit(self.getImage("upgradeEmpty"),(x,y))
                if self.settings["upgrade"]!="Empty":
                    if self.settings["perm"]:
                        surf.blit(self.getImage("upgrade"),(x,y))
                    else:
                        self.drawRotate(surf,x,y,self.getImage("upgrade"),self.angle)
            else:
                surf.blit(self.getImage("upgradeWarning"),(x,y))
        else: #Render normal
            surf.blit(self.getImage("upgradeEmpty"),(x,y))
        if self.HINT and self.LINK["multi"]==-1:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,dview):
        return not dview
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render upgade slot in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
        if self.__used:
            self.__upgBroken.render(x+(25*scale),y+(25*scale),0,scale,surf,UPG_COL,ang,eAng,arcSiz)
        else:
            self.__upgMod.render(x+(25*scale),y+(25*scale),0,scale,surf,UPG_COL,ang,eAng,arcSiz)
        if not self.__particle is None: #Particle effects for when the android dies
            self.__particle.render(x-((self.pos[0]-self.__particle.pos[0])*scale),y-((self.pos[1]-self.__particle.pos[1])*scale),scale,ang,eAng,surf)
        if self.HINT:
            self.renderHint(surf,self.gameHint,[x+(25*scale),y+(50*scale)])