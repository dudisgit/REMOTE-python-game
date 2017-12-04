#Do not run this file, it is a module!
import pygame, time, math, cmath
import entities.base as base

SHOW_RATE = 10 #Amount of times a second to scan for drones when in multiplayer (used to save engine resources)
SPARK_SIZE = 0.5 #Size length of a spark

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.isNPC = True
        self.discovered = True
        self.health = 80
        self.speed = 1.5
        self.colisionType = 1 #Circle colision
        self.NPCDist = 70 #NPC distance to target limit
        self.size = [25,25]
        self.beingSucked = False #Make this entity suckable in a vacum
        self.AllwaysRender = True #Make this android allways render in 3D view regardless of position in map (doesen't mean wallhacks)
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]:
                simp = "Simple"
            else:
                simp = ""
            self.__body = LINK["render"].Model(LINK,"android"+simp)
            self.__head = LINK["render"].Model(LINK,"androidHead")
        self.__bullets = [] #Used to render bullets
        #Syntax
        #0: Percentage path
        #1: Start pos
        #2: End pos
        self.__fireSide = False #Side the gun fires
        self.__barrelDist = 6 #Distance of the barrel
        self.__targetChange = -1 #Used to detect changes in target
        self.__UpdateFireChange = 0 #Used only by clients so that they display bullets being fired
        self.__sShow = True #Show in games scematic view
        self.__first = True #First time this entity has spawned
        self.__particle = None #Particle effects
        self.__lastScan = time.time() #Last time this NPC scanned for a drone
        self.__canSee = False #Drone can see this entity
        self.__seeBefore = False #Used to detect changes in self.__canSee
        self.__inRoom = False #Is true if the NPC is inside a room
        self.hintMessage = "An android is easy to deal with. It is slower than drones and deals minimal damage. \nIt cannot attack doors"
    def takeDamage(self,dmg,reason=""):
        if reason!="radiation": #Android is imune to radiation
            self.health -= dmg
        if self.health<0:
            self.health = 0
            if self.LINK["particles"]:
                self.__particle = self.LINK["render"].ParticleEffect(self.LINK,self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2),0,360,12,0.9,30,0.5,1.5,1)
                self.__particle.renderParticle = self.__renderParticle
            self.alive = False
            self.colisionType = 0 #Disable colision
            self.stopNavigation()
        return self.health == 0
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["android",self.ID,self.pos]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
    def SyncData(self,data,lag=1): #Syncs the data with this android
        self.pos[0] = ((self.pos[0]*3)+data["x"])/4
        self.pos[1] = ((self.pos[1]*3)+data["y"])/4
        self.alive = data["A"] == True
        if not data["A"]: #Android is dead
            self.colisionType = 0
            if self.LINK["particles"] and self.__particle is None:
                self.__particle = self.LINK["render"].ParticleEffect(self.LINK,self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2),0,360,12,0.9,30,0.5,1.5,1)
                self.__particle.renderParticle = self.__renderParticle
            else:
                self.__particle.pos = [self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2)]
        angle = data["a"]
        dist2 = 0 #Angular distance from the entities angle and the targets angle
        if angle > self.angle: #This is an algorithm for turning in a proper direction smothly
            if angle - self.angle > 180:
                dist2 = 180 - (angle - 180 - self.angle)
                self.angle-=lag*(dist2**0.7)
            else:
                dist2 = angle - self.angle
                self.angle+=lag*(dist2**0.7)
        else:
            if self.angle - angle > 180:
                dist2 = 180 - (self.angle - 180 - angle)
                self.angle+=lag*(dist2**0.7)
            else:
                dist2 = self.angle - angle
                self.angle-=lag*(dist2**0.7)
        try:
            self.angle = int(self.angle) % 360 #Make sure this entitys angle is not out of range
        except:
            self.angle = int(cmath.phase(self.angle)) % 360 #Do the same before but unconvert it from a complex number
        if data["T"]==0: #No target
            self.NPCATTACK = None
        elif not data["T"] in self.LINK["IDs"]: #Target doesen't exist
            self.LINK["errorDisplay"]("Server is trying to target entity that doesen't exist ",data["T"])
        elif self.alive: #Target valid
            self.NPCATTACK = self.LINK["IDs"][data["T"]]
            if time.time()>self.__UpdateFireChange: #Fire a bullet (visualy)
                self.__UpdateFireChange = time.time()+(1/5)
                dist = math.sqrt(( (self.pos[0]-self.NPCATTACK.pos[0])**2 ) + ( (self.pos[1]-self.NPCATTACK.pos[1])**2 ))
                self.NPCAttackLoop(dist)
    def GiveSync(self): #Returns the synced data for this android
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["a"] = int(self.angle)+0
        res["A"] = self.alive
        if self.NPCATTACK is None:
            res["T"] = 0
        else:
            res["T"] = self.NPCATTACK.ID+0
        return res
    def __renderParticle(self,x,y,scale,alpha,surf,a):
        pygame.draw.line(surf,(255,255,0),[x-(math.cos(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3]),y-(math.sin(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3])],[x+(math.cos(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3]),y+(math.sin(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3])],int(1*scale))
    def NPCAttackLoop(self,dist): #Will only be called continuesly if there is a visual path between the target and that its chasing it.
        if dist<200 and not self.NPCATTACK is None: #Target in range, fire!
            if self.LINK["multi"]!=1: #Is not a client (this can be called by a client to draw visual bullets on the android)
                self.NPCATTACK.takeDamage(1)
            if self.LINK["multi"]!=2: #Is not a server
                ang2 = -math.atan2(self.pos[0]+(self.size[0]/2)-(self.NPCATTACK.pos[0]+(self.NPCATTACK.size[0]/2)),self.pos[1]+(self.size[1]/2)-(self.NPCATTACK.pos[1]+(self.NPCATTACK.size[1]/2)))
                PS = [12+(math.sin(self.angle/180*math.pi)*8),12+(math.cos(self.angle/180*math.pi)*8)]
                if self.__fireSide: #Fire on the left cannon
                    Start = [self.pos[0]+PS[0]+(math.cos(ang2-2)*12),self.pos[1]+PS[1]+(math.sin(ang2-2)*12)]
                else: #Fire on the right cannon
                    Start = [self.pos[0]+PS[0]+(math.cos(ang2-1)*12),self.pos[1]+PS[1]+(math.sin(ang2-1)*12)]
                #Create and fire new bullet
                self.__bullets.append([0,Start,[self.NPCATTACK.pos[0]+(self.NPCATTACK.size[0]/2),self.NPCATTACK.pos[1]+(self.NPCATTACK.size[1]/2)]])
                self.__fireSide = not self.__fireSide #Switch cannon
                self.__barrelDist = 10 #Make the barrel shoot backwards
    def loop(self,lag):
        if self.LINK["multi"]!=2: #Is not a server
            rem = []
            if not self.NPCATTACK is None:
                dist = math.sqrt(((self.pos[0]-self.NPCATTACK.pos[0])**2)+((self.pos[1]-self.NPCATTACK.pos[1])**2))
            else:
                dist = 100
            for a in self.__bullets: #Go through all bullets and make them move forwards
                a[0]+=(lag/10)*(100/dist)
                if a[0]>=1: #Bullet has finished path, deleting
                    rem.append(a)
            for a in rem: #Delete bullets
                self.__bullets.remove(a)
            if not self.__particle is None: #Event loop for particle system if the android is dead
                self.__particle.loop(lag)
        if self.LINK["multi"]==1: #Client
            if "e"+str(self.ID) in self.LINK["cli"].SYNC:
                self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)],lag)
            else:
                self.REQUEST_DELETE = True
        elif self.LINK["multi"]==2: #Server
            if self.__canSee or self.__first: #Only sync position if the player can see it.
                self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
                self.__first = False
            if time.time()>self.__lastScan: #Check for NPC's seeing this drone
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
                GS = self.GiveSync()
                if GS["T"]!=self.LINK["serv"].SYNC["e"+str(self.ID)]["T"] and not self.__canSee: #Make sure the android isn't firing at the player when its out of range
                    self.__first = True
        if self.LINK["multi"]!=1: #Is not a client
            if self.alive:
                self.NPCloop()
            self.colisionType = 0 #Disable colisions, walls only
            self.movePath(lag)
            if self.alive: #If android is dead then make it uncolidable
                self.colisionType = 1 #Turn back to circle colision
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,40)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
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
            surf.blit(self.getImage("android"),(x,y))
        elif edit:
            if (time.time()%0.5)>0.25:
                surf.blit(self.getImage("android"),(x,y))
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
            self.drawRotate(surf,x-((self.size[0]/2)*scale),y-((self.size[1]/2)*scale),self.getImage("android"),self.angle)
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render android in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        if self.alive:
            col = (255,0,0)
        else:
            col = (150,0,0)
        self.__body.render(x+(12*scale),y+(12*scale),self.angle,scale/3,surf,col,ang,eAng,arcSiz)
        if self.NPCATTACK is None:
            ang2 = time.time() #Angle of the turret head
        else:
            ang2 = math.atan2(self.pos[0]+(self.size[0]/2)-(self.NPCATTACK.pos[0]+(self.NPCATTACK.size[0]/2)),self.pos[1]+(self.size[1]/2)-(self.NPCATTACK.pos[1]+(self.NPCATTACK.size[1]/2)))
        dist = self.__barrelDist #Distance the turret head is to the body
        PS = [12+math.sin(self.angle/180*math.pi),12+math.cos(self.angle/180*math.pi)]
        self.__barrelDist = (self.__barrelDist+4)/2 #Make barrel smothly move back into position
        if self.alive: #Android is alive
            ang3 = (self.angle/180*math.pi)+math.pi
            br = [math.sin(ang2+math.pi)*(dist-4)*scale,math.cos(ang2+math.pi)*(dist-4)*scale]
            self.__head.render(x+(PS[0]*scale)-(math.sin(ang3)*5*scale)-br[0],y+(PS[1]*scale)-(math.cos(ang3)*5*scale)-br[1],ang2*180/math.pi,scale/3,surf,(255,0,0),ang,eAng,arcSiz)
        scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
        for a in self.__bullets: #Render all bullets
            #Draw a line to reprisent a bullet
            PS = [a[1][0]-((a[1][0]-a[2][0])*a[0]),a[1][1]-((a[1][1]-a[2][1])*a[0])]
            PS2 = [a[1][0]-((a[1][0]-a[2][0])*(a[0]+0.1)),a[1][1]-((a[1][1]-a[2][1])*(a[0]+0.1))]
            if ang is None:
                pygame.draw.line(surf,(255,255,0),[int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[int((PS2[0]*scale)-scrpos[0]),int((PS2[1]*scale)-scrpos[1])],int(2*scale))
            elif self.LINK["render"].insideArc([int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[sx/2,sy/2],ang):
                pygame.draw.line(surf,(255,255,0),[int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[int((PS2[0]*scale)-scrpos[0]),int((PS2[1]*scale)-scrpos[1])],int(2*scale))
            elif eAng is None:
                pass
            elif self.LINK["render"].insideArc([int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[sx/2,sy/2],eAng):
                pygame.draw.line(surf,(255,255,0),[int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[int((PS2[0]*scale)-scrpos[0]),int((PS2[1]*scale)-scrpos[1])],int(2*scale))
        if not self.__particle is None: #Particle effects for when the android dies
            self.__particle.render(x-((self.pos[0]-self.__particle.pos[0])*scale),y-((self.pos[1]-self.__particle.pos[1])*scale),scale,ang,eAng,surf)
