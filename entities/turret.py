#Do not run this file, it is a module!
import pygame, random, math, time
import entities.base as base

RANDOM_DIE = 30 #Percentage chance the turret will be destroyed when the room is vacuumed
SPARK_SIZE = 0.5 #Size length of a spark

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.settings["god"] = True #Turret is indestructable
        self.settings["power"] = [] #Contains a list of generators the turret is powered by
        self.settings["inter"] = [] #Contains a list of interfaces the turret is controlled by
        self.turretActive = False #Is the turret currently active
        self.powered = False #Is this turret powered?
        self.__activeChange = False #Used to detect changes in the turret being active
        self.__room = None #Room the turret is inside of
        self.__turretTarget = None #Entity the turret is shooting
        self.__bullets = [] #Used to render bullets
        #Syntax
        #0: Percentage path
        #1: Start pos
        #2: End pos
        self.__fireSide = False #Side the gun fires
        self.__fireAgain = time.time()+0.1 #Time until the turret fires again
        self.__particle = None #Particle effects
        self.__aliveChange = True #Detects changes in alive status (used in mutliplayer)
        self.__isVac = False #Used to detect change in air pressure inside the current room
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the turret is inside a room
        self.hintMessage = "A turret is a player controlled ship defence, the player can turn on/off turrets using an interface whilst the turret is powered. \nWhen active it will kill anything in the room (including the player)"
    def __renderParticle(self,x,y,scale,alpha,surf,a):
        pygame.draw.line(surf,(255,255,0),[x-(math.cos(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3]),y-(math.sin(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3])],[x+(math.cos(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3]),y+(math.sin(a[2]/180*math.pi)*SPARK_SIZE*scale*a[3])],int(1*scale))
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        pows = []
        for i,a in enumerate(self.settings["power"]):
            try:
                pows.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving power link "+str(i)+"(index) in turret "+str(self.ID)+"(ID) failed.")
        ints = []
        for i,a in enumerate(self.settings["inter"]):
            try:
                ints.append(a.ID)
            except:
                self.LINK["errorDisplay"]("Saving controll link "+str(i)+"(index) in turret "+str(self.ID)+"(ID) failed.")
        return ["turret",self.ID,self.pos,self.settings["god"],pows,ints]
    def loop2(self,lag): #Ran on single player or server
        self.powered = False #Make the turret unpowered
        if len(self.settings["power"])==0: #Check if either room is powered
            r = self.findPosition() #Get the position of this turret
            if r!=-1 and type(r)==self.getEnt("room"): #Is the room valid?
                self.powered = r.powered == True #Base turret's power on the room its in
        else: #Check all power connections if this turret is powered
            for a in self.settings["power"]: #Go through all generators this upgrade is linked to to find one that is active
                if a.active:
                    self.powered = True
                    break
        self.turretActive = False #Turret is active or not
        for a in self.settings["inter"]:
            if a.defence: #Interface is requesting this turret to turn on
                self.turretActive = True
                break
        if self.__room.air != self.__isVac and not self.__room is None: #Check wether the air pressure inside the room has changed
            self.__isVac = self.__room.air == True
            if not self.__isVac and random.randint(0,100)<RANDOM_DIE and not self.settings["god"]: #Destroy the turret
                self.alive = False
                self.LINK["outputCommand"]("Turret in R"+str(self.__room.number)+" has been destroyed due to outside exposure.",(255,0,0))
                if self.LINK["particles"]: #Generate particle effects
                    self.__particle = self.LINK["render"].ParticleEffect(self.LINK,self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2),0,360,12,0.9,10,0.5,1.5,1)
                    self.__particle.renderParticle = self.__renderParticle
        if self.turretActive and self.powered and self.alive and self.__turretTarget is None and not self.__room is None: #Active turret
            Ents = self.__room.EntitiesInside() #Get all entities in the rooms
            DroneObject = self.getEnt("drone") #Drone object
            self.angle += lag*5
            Ems = 0
            for a in Ents: #Go through every entity in the room
                if (a.isNPC or type(a)==DroneObject) and a.alive and not a.stealth: #Is an NPC or drone thats alive
                    if a.health>0: #Health is still above 0
                        self.__turretTarget = a
                    if type(a)==self.getEnt("swarm"): #Swarm NPC
                        Ems += random.randint(25,35)
                    else:
                        Ems += 1
            if not self.__activeChange: #The turrets first time turning on from its off state
                self.__activeChange = True
                if Ems==0:
                    self.LINK["outputCommand"]("Turret in R"+str(self.__room.number)+" activated",(0,255,0))
                else:
                    self.LINK["outputCommand"]("Turret in R"+str(self.__room.number)+" attacking "+str(Ems)+" objects",(255,255,0))
        elif not self.__turretTarget is None: #Fire at target
            self.angle+=90
            if time.time()>self.__fireAgain and self.LINK["multi"]!=2: #Is not a server and can fire a bullet
                self.__fireBullet()
                self.__fireAgain = time.time()+0.1
            if self.__turretTarget.takeDamage(lag,"turret"): #Damage targt, true if target is dead
                self.__turretTarget = None
                self.LINK["outputCommand"]("Turret in R"+str(self.__room.number)+" has killed an object",(255,255,0))
            elif self.__turretTarget.findPosition()!=self.__room: #Target ran away
                self.__turretTarget = None
            else: #Aim at target
                self.angle = math.atan2(self.pos[0]-self.__turretTarget.pos[0],self.pos[1]-self.__turretTarget.pos[1])*180/math.pi
                self.angle+=90
        else:
            self.__activeChange = False
    def __fireBullet(self): #Fires a visual bullet
        ang2 = -math.atan2(self.pos[0]+(self.size[0]/2)-(self.__turretTarget.pos[0]+(self.__turretTarget.size[0]/2)),self.pos[1]+(self.size[1]/2)-(self.__turretTarget.pos[1]+(self.__turretTarget.size[1]/2)))
        PS = [25+(math.sin(self.angle/180*math.pi)*4),25+(math.cos(self.angle/180*math.pi)*4)]
        if self.__fireSide: #Fire on the left cannon
            Start = [self.pos[0]+PS[0]+(math.cos(ang2-2)*8),self.pos[1]+PS[1]+(math.sin(ang2-2)*8)]
        else: #Fire on the right cannon
            Start = [self.pos[0]+PS[0]+(math.cos(ang2-1)*8),self.pos[1]+PS[1]+(math.sin(ang2-1)*8)]
        #Create and fire new bullet
        self.__bullets.append([0,Start,[self.__turretTarget.pos[0]+(self.__turretTarget.size[0]/2),self.__turretTarget.pos[1]+(self.__turretTarget.size[1]/2)]])
        self.__fireSide = not self.__fireSide #Switch cannon
    def SyncData(self,data): #Syncs the data with this drone
        if data["T"]==-1: #Turret is idle
            self.__turretTarget = None
        else: #Turret is attacking
            self.__turretTarget = self.LINK["IDs"][data["T"]]
        self.turretActive = data["A"] == True
        self.alive = data["L"] == True
        if self.alive != self.__aliveChange: #Alive status has changed
            self.__aliveChange = self.alive == True
            if not self.alive and self.LINK["particles"]: #Generate particle effects
                self.__particle = self.LINK["render"].ParticleEffect(self.LINK,self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2),0,360,12,0.9,10,0.5,1.5,1)
                self.__particle.renderParticle = self.__renderParticle
    def afterLoad(self): #Called when the map is first loaded
        self.__room = self.findPosition()
        if not type(self.__room)==self.getEnt("room") or self.__room==-1:
            self.__room = None
    def GiveSync(self): #Returns the synced data for this drone
        res = {}
        if self.__turretTarget is None: #No target
            res["T"] = -1
        else: #Targeting something
            res["T"] = self.__turretTarget.ID
        res["A"] = self.turretActive
        res["L"] = self.alive
        return res
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
            if not self.__turretTarget is None and self.alive: #Turret is targeting something that is alive
                self.angle+=90
                if time.time()>self.__fireAgain and self.LINK["multi"]!=2: #Is not a server and can fire a bullet
                    self.__fireBullet()
                    self.__fireAgain = time.time()+0.1
                self.angle = math.atan2(self.pos[0]-self.__turretTarget.pos[0],self.pos[1]-self.__turretTarget.pos[1])*180/math.pi
                self.angle+=90
            elif self.turretActive and self.alive: #Turret is idle
                self.angle+=lag*5
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=1: #Is not client, single player or server
            self.loop2(lag)
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
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["god"] = data[3]
        for a in data[4]:
            if a in idRef:
                self.settings["power"].append(idRef[a])
            else:
                self.LINK["errorDisplay"]("Loading power link "+str(a)+"(ID) failed in turret "+str(self.ID)+"(ID).")
        for a in data[5]:
            if a in idRef:
                self.settings["inter"].append(idRef[a])
                idRef[a].turrets.append(self)
            else:
                self.LINK["errorDisplay"]("Loading interface link "+str(a)+"(ID) failed in turret "+str(self.ID)+"(ID).")
    def __ChangeGod(self,LINK,state): #switches godmode on the turret
        self.settings["god"] = state == True
    def __LinkTo(self,LINK): #"Link to" button was pressed
        LINK["currentScreen"].linkItem(self,"power") #A bit bodgy but this can only be called in the map designer.
    def __LinkInterTo(self,LINK): #"Link to" button was pressed
        LINK["currentScreen"].linkItem(self,"inter") #A bit bodgy but this can only be called in the map designer.
    def __UnlinkAll(self,LINK): #Deletes all links on this entity
        self.settings["power"] = []
        self.settings["inter"] = []
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,180)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__check1 = self.LINK["screenLib"].CheckButton(5,40,self.LINK,"Indestructable",self.settings["god"],self.__ChangeGod) #Generator godmode checkbox
        self.__check3 = self.LINK["screenLib"].Button(5,75,self.LINK,"Link control",self.__LinkInterTo) #Link interface button
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
        self.__check3.render(self.__check3.pos[0],self.__check3.pos[1],1,1,self.__surface) #Render link button
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
    def editMove(self,ents): #Turret is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (turret)"
        elif len(self.settings["power"])==0:
            return "No power (turret)"
        elif len(self.settings["inter"])==0:
            return "No controll (turret)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit: #Draw all the power lines
            scrolPos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Calculate the scroll position
            #Power lines
            rem = [] #Items to remove because they where deleted
            for a in self.settings["power"]: #Loop through all the power lines to render them
                pygame.draw.line(surf,(100,0,100),[x+(self.size[0]*0.5*scale),y+(self.size[1]*0.5*scale)],
                                                    [((a.pos[0]+(a.size[0]/2))*scale)-scrolPos[0],((a.pos[1]+(a.size[1]/2))*scale)-scrolPos[1]],3)
                if a.REQUEST_DELETE: #Entity is has been deleted (this entity is keeping it alive with its pointer)
                    rem.append(a)
            for a in rem: #Loop through all the entities wanted to be deleted
                self.settings["power"].remove(a)
            #Controll lines
            rem = [] #Items to remove because they where deleted
            for a in self.settings["inter"]: #Loop through all the interface lines to render them
                pygame.draw.line(surf,(100,100,0),[x+(self.size[0]*0.5*scale),y+(self.size[1]*0.5*scale)],
                                                    [((a.pos[0]+(a.size[0]/2))*scale)-scrolPos[0],((a.pos[1]+(a.size[1]/2))*scale)-scrolPos[1]],3)
                if a.REQUEST_DELETE: #Entity is has been deleted (this entity is keeping it alive with its pointer)
                    rem.append(a)
            for a in rem: #Loop through all the entities wanted to be deleted
                self.settings["inter"].remove(a)
        if edit:
            if self.__inRoom:
                surf.blit(self.getImage("turret"),(x,y))
            else:
                surf.blit(self.getImage("turretDead"),(x,y))
        else:
            if not self.alive:
                surf.blit(self.getImage("turretDead"),(x,y))
            elif self.turretActive:
                surf.blit(self.getImage("turretActive"),(x,y))
            else:
                surf.blit(self.getImage("turret"),(x,y))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,Dview=False): #Should the turret render in scematic view
        return not Dview
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None,isActive=False): #Render turret in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        self.LINK["render"].renderModel(self.LINK["models"]["turretBase"],x+(25*scale),y+(12*scale),0,scale/1.75,surf,(0,204,255),ang,eAng,arcSiz)
        if self.LINK["simpleModels"]:
            self.LINK["render"].renderModel(self.LINK["models"]["turretSimple"],x+(25*scale),y+(25*scale),self.angle,scale/1.75,surf,(0,204,255),ang,eAng,arcSiz)
        else:
            self.LINK["render"].renderModel(self.LINK["models"]["turret"],x+(25*scale),y+(25*scale),self.angle,scale/1.75,surf,(0,204,255),ang,eAng,arcSiz)
        scrpos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position
        for a in self.__bullets: #Render all bullets
            #Draw a line to reprisent a bullet
            PS = [a[1][0]-((a[1][0]-a[2][0])*a[0]),a[1][1]-((a[1][1]-a[2][1])*a[0])]
            PS2 = [a[1][0]-((a[1][0]-a[2][0])*(a[0]+0.02)),a[1][1]-((a[1][1]-a[2][1])*(a[0]+0.02))]
            if ang is None:
                pygame.draw.line(surf,(0,255,255),[int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[int((PS2[0]*scale)-scrpos[0]),int((PS2[1]*scale)-scrpos[1])],int(2*scale))
            elif self.LINK["render"].insideArc([int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[sx/2,sy/2],ang):
                pygame.draw.line(surf,(0,255,255),[int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[int((PS2[0]*scale)-scrpos[0]),int((PS2[1]*scale)-scrpos[1])],int(2*scale))
            elif eAng is None:
                pass
            elif self.LINK["render"].insideArc([int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[sx/2,sy/2],eAng):
                pygame.draw.line(surf,(0,255,255),[int((PS[0]*scale)-scrpos[0]),int((PS[1]*scale)-scrpos[1])],[int((PS2[0]*scale)-scrpos[0]),int((PS2[1]*scale)-scrpos[1])],int(2*scale))
        if not self.__particle is None: #Particle effects for when the android dies
            self.__particle.render(x-((self.pos[0]-self.__particle.pos[0])*scale),y-((self.pos[1]-self.__particle.pos[1])*scale),scale,ang,eAng,surf)
