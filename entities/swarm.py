#Do not run this file, it is a module!
import pygame, time, math
import entities.base as base

SHOW_RATE = 10 #Amount of times a second to scan for drones when in multiplayer (used to save engine resources)

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["attack"] = False #If this NPC should attack doors
        self.health = 60
        self.speed = 2.5
        self.NPCDist = 30
        self.size = [25,25]
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]:
                simp = "Simple"
            else:
                simp = ""
            self.__fly = LINK["render"].Model(LINK,"fly"+simp) #Fly alive model
            self.__flyDead = LINK["render"].Model(LINK,"flyDead") #Fly dead pile model
        self.__sShow = True #Show in games scematic view
        self.__first = True #First time this entity has spawned
        self.__lastScan = time.time() #Last time this NPC scanned for a drone
        self.__canSee = False #Drone can see this entity
        self.__seeBefore = False #Used to detect changes in self.__canSee
        self.beingSucked = False #Make this entity suckable in a vacum
        self.isNPC = True
        self.__inRoom = False #Is true if the NPC is inside a room
        self.hintMessage = "A swarm is the most dangerous enemy in the game. Fast, quick and deadly. \nThey can travel through vents if in a room with them."
    def takeDamage(self,dmg,reason=""):
        self.health -= dmg
        if self.health<0:
            self.health = 0
            self.alive = False
            self.stopNavigation()
        return self.health == 0
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["swarm",self.ID,self.pos,self.settings["attack"]]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["attack"] = data[3]
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def __ChangeAttack(self,LINK,state): #Changes the attack mode, if the NPC should attack doors or not
        self.settings["attack"] = state == True
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,75)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Attack doors",self.settings["attack"],self.__ChangeAttack) #Attack checkbutton
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__check.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def SyncData(self,data): #Syncs the data with this swarm
        self.pos[0] = ((self.pos[0]*3)+data["x"])/4
        self.pos[1] = ((self.pos[1]*3)+data["y"])/4
        self.alive = data["A"] == True
        if data["T"]==0: #No target
            self.NPCATTACK = None
        elif not data["T"] in self.LINK["IDs"]: #Target doesen't exist
            self.LINK["errorDisplay"]("Server is trying to target entity that doesn't exist ",data["T"])
        else: #Target valid
            self.NPCATTACK = self.LINK["IDs"][data["T"]]
    def GiveSync(self): #Returns the synced data for this swarm
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["A"] = self.alive
        if self.NPCATTACK is None:
            res["T"] = 0
        else:
            res["T"] = self.NPCATTACK.ID+0
        return res
    def NPCAttackLoop(self,dist): #Will only be called continuesly if there is a visual path between the target and that its chasing it.
        if dist<60: #Target in range, damage!
            self.NPCATTACK.takeDamage(2)
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            if "e"+str(self.ID) in self.LINK["cli"].SYNC:
                self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
            else:
                self.REQUEST_DELETE = True
        elif self.LINK["multi"]==2: #Server
            if self.__canSee or self.__first: #Only sync position if the player can see it.
                self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
                self.__first = False
            if time.time()>self.__lastScan:
                self.__lastScan = time.time()+(1/SHOW_RATE)
                self.__canSee = self.NPCDroneSee()
                if self.__canSee != self.__seeBefore: #Notice changed
                    self.__seeBefore = self.__canSee == True
                    if self.__canSee: #Send NPC's position over TCP so player gets the correct position of the NPC
                        send = []
                        send.append(["s",int(self.pos[0]),"e"+str(self.ID),"x"]) #X position
                        send.append(["s",int(self.pos[1]),"e"+str(self.ID),"y"]) #Y position
                        send.append(["s",int(self.angle),"e"+str(self.ID),"a"]) #Angle
                        for a in self.LINK["serv"].users: #Send data to all users
                            self.LINK["serv"].users[a].sendTCP(send)
                            self.LINK["serv"].users[a].tempIgnore.append(["e"+str(self.ID),"x"])
                            self.LINK["serv"].users[a].tempIgnore.append(["e"+str(self.ID),"y"])
                            self.LINK["serv"].users[a].tempIgnore.append(["e"+str(self.ID),"a"])
        if self.LINK["multi"]!=1: #Is not a client
            if self.alive:
                self.NPCloop(True)
                if self.settings["attack"] and self.NPCATTACK is None:
                    self.NPCDoorLoop()
            self.movePath(lag)
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
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.__inRoom and edit:
            surf.blit(self.getImage("swarm"),(x,y))
        elif edit:
            if (time.time()%0.5)>0.25:
                surf.blit(self.getImage("swarm"),(x,y))
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
        if not edit and self.LINK["DEVDIS"] and (time.time()-int(time.time())>0.5 or self.NPCATTACK is None): #Display NPC when in development mode
            self.drawRotate(surf,x-((self.size[0]/2)*scale),y-((self.size[1]/2)*scale),self.getImage("swarm"),self.angle)
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def __drawAttackFly(self,x,y,Face,scale,surf,ang,ang2,arcSiz): #Draw a single fly but facing at a position (used for attacking)
        FaceAngle = math.atan2(x-Face[0],y-Face[1])*180/math.pi
        self.__fly.render(x,y,FaceAngle+180,scale,surf,(255,0,0),ang,ang2,arcSiz)
    def render(self,x,y,scale,ang2,surf=None,arcSiz=-1,eAng=None): #Render the swarm in 3D
        if surf is None:
            surf = self.LINK["main"]
        ang = time.time()
        if not self.alive: #Swarm is dead
            self.__flyDead.render(x+((self.size[0]/2)*scale),y+((self.size[1]/2)*scale),0,scale/1.5,surf,(150,0,0),ang2,eAng,arcSiz)
        elif self.NPCATTACK is None: #NPC is roaming, cause fly's to spin
            self.__fly.render(x+(math.cos(ang)*10*scale),y+(math.sin(ang)*10*scale),(ang*180),scale/6,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang/2)*7*scale),y+(math.sin(ang/2)*11*scale),(ang*120),scale/5,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*3)*18*scale),y+(math.sin(ang*1.4)*12*scale),(ang*190),scale/7,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*1.5)*14*scale),y+(math.sin(ang*2)*30*scale),(ang*140),scale/5,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*2)*12*scale),y+(math.sin(ang*3)*20*scale),(ang*200),scale/5,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*2.5)*5*scale),y+(math.sin(ang*2.5)*5*scale),(ang*130),scale/6,surf,(255,0,0),ang2,eAng,arcSiz)
            
            self.__fly.render(x+(math.cos(ang/1.2)*7*scale),y+(math.sin(ang/2)*11*scale),(ang*120),scale/5,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*2.3)*15*scale),y+(math.sin(ang*1.3)*15*scale),(ang*170),scale/7,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*1.8)*16*scale),y+(math.sin(ang*2.1)*21*scale),(ang*130),scale/5,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*2.2)*13*scale),y+(math.sin(ang*4)*12*scale),(ang*220),scale/5,surf,(255,0,0),ang2,eAng,arcSiz)
            self.__fly.render(x+(math.cos(ang*2.7)*4*scale),y+(math.sin(ang*3.2)*34*scale),(ang*110),scale/6,surf,(255,0,0),ang2,eAng,arcSiz)
        else: #NPC is attacking, cause fly's to aim at target
            scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
            Face = [((self.NPCATTACK.pos[0]+(self.NPCATTACK.size[0]/2))*scale)-scrpos[0],((self.NPCATTACK.pos[1]+(self.NPCATTACK.size[1]/2))*scale)-scrpos[1]]
            self.__drawAttackFly(x+(math.cos(ang)*10*scale),y+(math.sin(ang)*10*scale),Face,scale/6,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang/2)*7*scale),y+(math.sin(ang/2)*11*scale),Face,scale/5,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*3)*18*scale),y+(math.sin(ang*1.4)*12*scale),Face,scale/6,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*1.5)*14*scale),y+(math.sin(ang*2)*30*scale),Face,scale/5,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*2)*12*scale),y+(math.sin(ang*3)*20*scale),Face,scale/5,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*2.5)*5*scale),y+(math.sin(ang*2.5)*5*scale),Face,scale/6,surf,ang2,eAng,arcSiz)

            self.__drawAttackFly(x+(math.cos(ang/1.2)*7*scale),y+(math.sin(ang/2)*11*scale),Face,scale/5,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*2.3)*15*scale),y+(math.sin(ang*1.3)*15*scale),Face,scale/7,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*1.8)*16*scale),y+(math.sin(ang*2.1)*21*scale),Face,scale/5,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*2.2)*13*scale),y+(math.sin(ang*4)*12*scale),Face,scale/5,surf,ang2,eAng,arcSiz)
            self.__drawAttackFly(x+(math.cos(ang*2.7)*4*scale),y+(math.sin(ang*3.2)*34*scale),Face,scale/6,surf,ang2,eAng,arcSiz)
