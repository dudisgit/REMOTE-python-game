#Do not run this file, it is a module!
import pygame, time
import entities.base as base

ATTACK_DELAY = 4.5 #Seconds between charging again
SHOW_RATE = 10 #Amount of times a second to scan for drones when in multiplayer (used to save engine resources)

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.isNPC = True
        self.speed = 0.8
        self.health = 120
        self.NPCDist = 120
        self.size = [25,25]
        self.settings["attack"] = False #If this NPC should attack doors
        self.colisionType = 1
        self.Charge = [False,[0,0],[0,0],0,time.time()] #Charge attacking
        self.__first = True #First time this entity has spawned
        self.__lastScan = time.time() #Last time this NPC scanned for a drone
        self.__canSee = False #Drone can see this entity
        self.beingSucked = False #Make this entity suckable in a vacum
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the NPC is inside a room
        self.hintMessage = "A brute will charge at a player when spotted. They are less fearful but deal heavy damage. \nIt is also REALY slow"
    def takeDamage(self,dmg,reason=""):
        self.health -= dmg
        if self.health<0:
            self.health = 0
            self.alive = False
        return self.health == 0
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["brute",self.ID,self.pos,self.settings["attack"]]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["attack"] = data[3]
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def __ChangeAttack(self,LINK,state): #Changes the attack mode, if the NPC should attack doors or not
        self.settings["attack"] = state == True
    def SyncData(self,data): #Syncs the data with this brute
        self.pos[0] = ((self.pos[0]*3)+data["x"])/4
        self.pos[1] = ((self.pos[1]*3)+data["y"])/4
        self.angle = ((self.angle*3)+data["a"])/4
    def GiveSync(self): #Returns the synced data for this brute
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["a"] = int(self.angle)+0
        return res
    def NPCAttackLoop(self,dist): #Will only be called continuesly if there is a visual path between the target and that its chasing it.
        if dist<130 and not self.Charge[0] and time.time()>self.Charge[4]: #Target in range and charge is ready, charge!
            self.Charge[0] = True #Make this entity attack
            self.Charge[1] = [self.pos[0]+0,self.pos[1]+0]
            if type(self.NPCATTACK)==self.getEnt("door"): #Attacking object is a door
                #The following code is to find the charge position of the door (so it doesen't go through it)
                if self.NPCATTACK.settings["lr"]: #Door is left to right
                    self.Charge[2][1] = self.NPCATTACK.pos[1]+(self.NPCATTACK.size[1]/2)
                    if self.pos[0]<self.NPCATTACK.pos[0]: #Door is on the right side
                        self.Charge[2][0] = self.NPCATTACK.pos[0]-self.size[0]
                    else: #Door is on the left side
                        self.Charge[2][0] = self.NPCATTACK.pos[0]+self.NPCATTACK.size[0]+self.size[0]
                else: #Door is up to down
                    self.Charge[2][0] = self.NPCATTACK.pos[0]+(self.NPCATTACK.size[0]/2)
                    if self.pos[1]<self.NPCATTACK.pos[1]: #Door is below
                        self.Charge[2][1] = self.NPCATTACK.pos[1]-self.size[1]
                    else: #Door is above
                        self.Charge[2][1] = self.NPCATTACK.pos[1]+self.NPCATTACK.size[0]+self.size[1]
            else: #Attacking object is a normal target (drone or lure)
                self.Charge[2] = [self.NPCATTACK.pos[0]+0,self.NPCATTACK.pos[1]+0]
            self.Charge[3] = 0
            self.Charge[4] = time.time()+ATTACK_DELAY #Time until the brute can charge again
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            if self.__canSee or self.__first: #Only sync position if the player can see it.
                self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
                self.__first = False
            if time.time()>self.__lastScan:
                self.__lastScan = time.time()+(1/SHOW_RATE)
                self.__canSee = self.NPCDroneSee()
        if self.LINK["multi"]!=1: #Is not a client
            if self.alive:
                self.NPCloop()
                if self.settings["attack"] and self.NPCATTACK is None:
                    self.NPCDoorLoop()
            self.colisionType = 0 #Disable colisions, walls only
            self.movePath(lag)
            self.colisionType = 1 #Turn back to circle colision
            if self.Charge[0]: #Charging animation
                self.Charge[3] += lag/10 #Increase step count
                if self.Charge[3]>1: #Finished animation, stop charge and deal damage
                    self.Charge[0] = False
                    self.Charge[3] = 1
                    self.NPCATTACK.takeDamage(50)
                #Move brute into position
                self.pos[0] = self.Charge[1][0]+((self.Charge[2][0]-self.Charge[1][0])*self.Charge[3])
                self.pos[1] = self.Charge[1][1]+((self.Charge[2][1]-self.Charge[1][1])*self.Charge[3])
                pSav = [self.pos[0]+0,self.pos[1]+0]
                if self.applyPhysics(): #Colided with an entity that isn't a room or door, stop animation and deal damage
                    self.Charge[0] = False
                    self.NPCATTACK.takeDamage(50)
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,75)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Attack doors",self.settings["attack"],self.__ChangeAttack) #Attack checkbutton
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
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
        self.__check = None
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
            surf.blit(self.getImage("brute"),(x,y))
        elif edit:
            if (time.time()%0.5)>0.25:
                surf.blit(self.getImage("brute"),(x,y))
        if self.LINK["DEVDIS"] and self.findPosition()!=-1:
            scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
            for a in self.paths:
                lastPos = [((self.pos[0]+(self.size[0]/2))*scale)-scrpos[0],((self.pos[1]+(self.size[1]/2))*scale)-scrpos[1]]
                if a[0]==0:
                    col = (255,255,0)
                else:
                    col = (255,0,255)
                for b in a[1]:
                    pygame.draw.line(surf,col,lastPos,[(b[0]*scale)-scrpos[0],(b[1]*scale)-scrpos[1]],4)
                    lastPos = [(b[0]*scale)-scrpos[0],(b[1]*scale)-scrpos[1]]
            for a in self.LINK["drones"]:
                self.linePathVisual([self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2)],[a.pos[0]+(a.size[0]/2),a.pos[1]+(a.size[1]/2)],surf,scrpos,scale)
        if not edit and self.LINK["DEVDIS"]: #Display NPC when in development mode
            self.drawRotate(surf,x-((self.size[0]/2)*scale),y-((self.size[1]/2)*scale),self.getImage("brute"),self.angle)
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
