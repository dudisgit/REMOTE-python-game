#Do not run this file, it is a module!
import pygame, math, time, random, cmath
import entities.base as base

DEFAULT_SIZE = 3 #Defualt upgrade slots for a drone
SUCK_SIZE = 1 #Air sucking particle effect size
DISCOVER_DIST = 140 #Discovery distance

class Main(base.Main):
    def __init__(self,x,y,LINK,ID,number=-1):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID # Id of the drone, -1 if the drone is player controlled.
        self.size = [25,25]
        self.number = number
        self.health = 100 #Changable health (is used for force setting on server for drone health)
        self.colision = False #Has the drone colided with anything?
        self.aliveShow = True #Alive status that is shown to the user
        self.forcePos = None #Force position (used to fix bugs with towing)
        if ID<0:
            self.settings["health"] = 100
            self.discovered = True
        else:
            self.settings["health"] = random.randint(10,40) #Health of the drone
            self.alive = False
        if LINK["multi"]==-1: #Map editor
            self.size = [50,50]
        self.renderSize = [-20,-20,70,70] #Used to have a bigger radius when rendering in 3D (does not effect scale)
        self.settings["maxHealth"] = 100 #Maximum health of the drone
        self.settings["angle"] = 0 #Angle of the drone
        self.settings["name"] = LINK["names"][random.randint(0,len(LINK["names"])-1)]+"" #Name of the drone
        self.settings["upgrades"] = [] #Default upgrades that should be loaded onto the drone for the first time it is spawned.
        for i in range(DEFAULT_SIZE): #Fill the upgrade slots with empty upgrades
            self.settings["upgrades"].append(["",0,-1])
        self.colisionType = 1 #Circle colision
        self.beingAttacked = False #Is the drone currently being attacked?
        self.controller = "" #The player controlling the drone
        self.__hullRotate = 0 #Rotation of the drones hull when in model 3
        self.allowed = True #Allowed to controll drone (client side)
        self.upgrades = [] #Upgrade objects inside the drone.
        self.PERM_UPG = [] #Permanant upgrades, this is only used for commands like "swap". This is not to be used for "special drones"
        self.PERM_UPG.append(LINK["upgrade"]["swap"].Main(LINK)) #Swap command
        self.PERM_UPG.append(LINK["upgrade"]["pickup"].Main(LINK))
        self.PERM_UPG.append(LINK["upgrade"]["info"].Main(LINK))
        self.PERM_UPG[0].drone = self
        self.PERM_UPG[1].drone = self
        self.PERM_UPG[2].drone = self
        self.pause = 0 #Pause the drone from moving
        self.__healthDrop = 0 #Used for "beingAttacked" so that the drone will know when its being attacked
        self.__healthBefore = 100 #Used to track health change in multiplayer
        self.__aliveChange = True #Detects changes in the alive status of this drone
        self.__sShow = True #Show in games scematic view
        self.__model = random.randint(1,3) #Model of the drone
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]: #Enable/disable simple models
                simp = "Simple"
            else:
                simp = ""
            self.__rModel = LINK["render"].Model(LINK,self.LINK["models"]["drone"+str(self.__model)+simp])
            if self.__model==3:
                self.__rModel2 = LINK["render"].Model(LINK,self.LINK["models"]["drone3Head"+simp])
        self.__SYNCChange = [] #Used to detect if the SYNC has changed
        self.__inRoom = False #Is true if the drone is inside a room
        self.__lastRoom = None #Last room this drone was found inside of
        self.__airParts = [] #Air particle effects when air is vacuumed
        self.beingSucked = False #Make this entity suckable in a vacum
        self.__suckChange = False #Change in air sucking
        self.hintMessage = "This is a disabled drone, you can add items, change health and name in the context/options menu."
    def canShow(self,Dview=False):
        return not Dview
    def discoverAround(self): #This will discover entities arround the current one
        RM = self.findPosition()
        if type(RM)!=-1 and self.ID<0: #Drone is in room and is valid
            ENTS = RM.EntitiesInside()
            RM.discovered2 = True
            RM.discovered = True
            for a in ENTS: #Go through every entity inside the room
                if not a.discovered:
                    dist = math.sqrt( ((self.pos[0]-a.pos[0])**2) + ((self.pos[1]-a.pos[1])**2) )
                    if dist<DISCOVER_DIST:
                        a.discovered = True
    def hasUpgrade(self,name): #Returns true if this drone has the specific upgrade
        for a in self.upgrades: #Loop through all the drones upgrades
            if a.name==name: #Found upgrade
                return True
        return False
    def takeDamage(self,dmg,reason=""): #Damage the drone
        self.health -= dmg
        if self.ID<0 and self.health<1: #Damage it as a player drone
            self.health = 1
            self.alive = False
        if self.health<0: #Damage it as a normal dead drone
            self.health = 0
            self.alive = False
        elif self.ID<0 and self.alive: #Notify about the damage in console
            self.__healthDrop = time.time()+2
            if not self.beingAttacked and self.LINK["multi"]!=2:
                if reason!="":
                    self.LINK["outputCommand"]("Drone is being damaged from "+reason+"!",(255,0,0),True,self)
                else:
                    self.LINK["outputCommand"]("Drone is being damaged!",(255,0,0),True,self)
            self.beingAttacked = True
        if self.ID<0: #Is player drone
            return self.health == 1
        else:
            return self.health == 0
    def loadUpgrades(self): #Loads all the upgrades into the drone
        self.upgrades = []
        for i,a in enumerate(self.settings["upgrades"]):
            if a[0]!="":
                if len(a)==2:
                    ID = -1
                else:
                    ID = a[2]
                if ID!=-1:
                    self.upgrades.append(self.LINK["upgrade"][a[0]].Main(self.LINK,ID))
                else:
                    self.upgrades.append(self.LINK["upgrade"][a[0]].Main(self.LINK,self.LINK["upgradeIDCount"]+0))
                    if len(a)>2:
                        self.settings["upgrades"][i][2] = self.LINK["upgradeIDCount"]+0
                    self.LINK["upgradeIDCount"] += 1
                if len(a)==4:
                    self.upgrades[-1].brakeprob = a[3]+0
                if len(a)==5:
                    self.upgrades[-1].openData(a[4])
                self.upgrades[-1].damage = a[1]
                self.upgrades[-1].drone = self #Link the upgrade to this drone
    def unloadUpgrades(self): #Imports all the upgrades into the drone for saving (used in multiplayer)
        for a in range(len(self.settings["upgrades"])):
            self.settings["upgrades"][a] = ["",0,-1,0,[]]
        for i,a in enumerate(self.upgrades):
            self.settings["upgrades"][i] = [a.name.lower(),a.damage+0,a.ID+0,a.brakeprob,a.saveData()]
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        if self.LINK["multi"]==2:
            self.unloadUpgrades()
        return ["drone",self.ID,self.pos,
            self.settings["angle"]+0,self.settings["health"]+0,self.settings["maxHealth"]+0,
            self.settings["name"]+"",self.settings["upgrades"],self.number,self.__model]
    def __forceRoom(self,lag): #Forces the drone back in a room if outside the map
        R = self.findPosition()
        O = False
        if R==-1 and not self.__lastRoom is None:
            O = True
        elif type(R)==self.getEnt("door") or type(R)==self.getEnt("airlock"):
            if not R.settings["open"] and not self.__lastRoom is None:
                O = True
        if O: #Outside the map
            if self.pos[0]>self.__lastRoom.pos[0]+(self.__lastRoom.size[0]/2):
                self.pos[0] -= 10*lag
            if self.pos[0]<self.__lastRoom.pos[0]+(self.__lastRoom.size[0]/2):
                self.pos[0] += 10*lag
            if self.pos[1]>self.__lastRoom.pos[1]+(self.__lastRoom.size[1]/2):
                self.pos[1] -= 10*lag
            if self.pos[1]<self.__lastRoom.pos[1]+(self.__lastRoom.size[1]/2):
                self.pos[1] += 10*lag
        elif R!=-1: #Inside map, mark position as last known inside a map
            self.__lastRoom = R
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.settings["angle"] = data[3]
        self.settings["health"] = data[4]+0
        self.health = data[4]+0
        self.__healthBefore = self.health+0
        self.settings["maxHealth"] = data[5]+0
        self.settings["name"] = data[6]+""
        self.settings["upgrades"] = data[7]
        if len(data)>8:
            self.number = data[8]+0
        if len(data)>9:
            self.__model = data[9]+0 #Model of this drone
            if self.LINK["multi"]!=2: #Is not a server
                if self.LINK["simpleModels"]: #Enable/disable simple models
                    simp = "Simple"
                else:
                    simp = ""
                self.__rModel = self.LINK["render"].Model(self.LINK,self.LINK["models"]["drone"+str(self.__model)+simp])
                if self.__model==3:
                    self.__rModel2 = self.LINK["render"].Model(self.LINK,self.LINK["models"]["drone3Head"+simp])
        self.loadUpgrades()
        if self.settings["angle"]==0:
            self.angle = random.randint(0,360)
        if self.LINK["multi"] == 2: #Is a server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
    def teleported(self): #This drone was teleported.
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync() #Upload the data about the drone in the world to SYNC
            #Sync this drones position over TCP
            send = []
            send.append(["s",int(self.pos[0]),"e"+str(self.ID),"x"]) #X position
            send.append(["s",int(self.pos[1]),"e"+str(self.ID),"y"]) #Y position
            for a in self.LINK["serv"].users: #Send data to all users
                self.LINK["serv"].users[a].sendTCP(send)
                self.LINK["serv"].users[a].tempIgnore.append(["e"+str(self.ID),"x"])
                self.LINK["serv"].users[a].tempIgnore.append(["e"+str(self.ID),"y"])
    def SyncData(self,data,lag=1): #Syncs the data with this drone
        if self.LINK["multi"]==2: #Is a server
            self.pos = [data["x"]+0,data["y"]+0]
            self.angle = data["a"]+0
        else: #Is a client/player
            self.discovered = data["D"]
            if self.allowed and self.controller==self.LINK["currentScreen"].name:
                self.pos = [data["x"]+0,data["y"]+0]
                self.angle = data["a"]+0
            else:
                self.pos[0] = ((self.pos[0]*3)+data["x"])/4
                self.pos[1] = ((self.pos[1]*3)+data["y"])/4
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
        self.settings["health"] = data["H"]+0
        self.aliveShow = data["L"] == True
        self.controller = data["C"]
        if self.LINK["multi"]==1: #Is a client
            self.alive = self.aliveShow == True
            self.health = int(self.settings["health"])+0
        self.__SYNCChange = [data["x"]+0,data["y"]+0,data["a"]+0]
    def GiveSync(self,posOnly=False): #Returns the synced data for this drone
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["a"] = int(self.angle)+0
        res["D"] = self.discovered
        res["C"] = self.controller
        if not posOnly: #Sync all settings
            res["H"] = int(self.settings["health"])+0
            res["L"] = self.aliveShow == True
        else: #Only sync drone position and not other data
            res["H"] = self.LINK["cli"].SYNC["e"+str(self.ID)]["H"]
            res["L"] = self.LINK["cli"].SYNC["e"+str(self.ID)]["L"]
        self.__SYNCChange = [res["x"]+0,res["y"]+0,res["a"]+0]
        return res
    def deleting(self): #This drone is being deleted
        if self.LINK["multi"]==2: #Is server
            for a in self.upgrades:
                a.upgradeDelete()
        if self in self.LINK["drones"]:
            self.LINK["drones"].remove(self) #Make this drone not the players drone anymore, marks it at command line tab
        if self.LINK["multi"]!=1 and self.ID<0: #Send a message to all saying the drone has died
            self.LINK["outputCommand"]("Drone "+str(self.number)+" was sucked out an airlock!",(255,0,0),False)
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def SyncChanged(self): #Has the sync for the drone changed (has server moved the drone)
        return self.__SYNCChange[0]!=self.LINK["cli"].SYNC["e"+str(self.ID)]["x"] or self.__SYNCChange[1]!=self.LINK["cli"].SYNC["e"+str(self.ID)]["y"] or self.__SYNCChange[2]!=self.LINK["cli"].SYNC["e"+str(self.ID)]["a"]
    def SyncChangedServer(self): #Has the sync for the drone changed (has server moved the drone)
        return self.__SYNCChange[0]!=self.LINK["serv"].SYNC["e"+str(self.ID)]["x"] or self.__SYNCChange[1]!=self.LINK["serv"].SYNC["e"+str(self.ID)]["y"] or self.__SYNCChange[2]!=self.LINK["serv"].SYNC["e"+str(self.ID)]["a"]
    def loop2(self,lag): #Used to effect the drone due to sorroundings (called by singple player or server, not client)
        if time.time()>self.pause or self.beingSucked:
            self.movePath(lag)
        if self.REQUEST_DELETE:
            return None
        for a in self.upgrades+self.PERM_UPG: #Do an event loop on all upgrades
            a.loop(lag)
        self.settings["health"] = self.health+0
        if not self.forcePos is None:
            bpos = [self.pos[0]+0,self.pos[1]+0]
            self.pos[0] = self.forcePos[0]+0
            self.pos[1] = self.forcePos[1]+0
            self.forcePos = None
            self.changeMesh(bpos)
            self.applyPhysics()
        if self.LINK["multi"]==2 and self.controller!="": #Is server and drone is being controlled
            for a in self.LINK["serv"].users:
                if self.controller==self.LINK["serv"].users[a].name:
                    break
            else:
                self.controller = ""
        self.aliveShow = self.alive == True
        self.__forceRoom(lag)
    def selectControll(self,cont,name): #Called when this drone is taken controll of or not
        if cont and self.LINK["multi"] == 1: #Drone is active and game is running as a client
            if self.controller!="":
                self.allowed=False
            else:
                self.controller = name+""
                self.allowed = True
                self.overide = True
        elif self.allowed:
            self.controller = ""
            self.overide = True
            self.allowed = True
    def loop(self,lag):
        self.__hullRotate = (self.pos[0]+self.pos[1])%360 #Make hull rotate when in model 3
        if self.ID<0:
            if self.settings["health"]!=self.__healthBefore:
                self.__healthBefore = self.settings["health"] + 0
                self.__healthDrop = time.time()+2
                if not self.beingAttacked and self.LINK["multi"]!=2:
                    self.LINK["outputCommand"]("Drone is being damaged!",(255,0,0),True,self)
                self.beingAttacked = True
            if time.time()>self.__healthDrop and self.__healthDrop!=0: #Stop stating the drone is being attacked
                self.__healthDrop = 0
                self.beingAttacked = False
            if self.alive!=self.__aliveChange:
                self.__aliveChange = self.alive == True
                if not self.alive:
                    self.LINK["outputCommand"]("Drone "+str(self.number)+" was disabled",(255,0,0),False)
                    self.stopNavigation(0)
        if self.overide and self.LINK["multi"] == 1 and not self.SyncChanged(): #Send our drone position to the server
            self.LINK["cli"].SYNC["e"+str(self.ID)] = self.GiveSync(True)
            self.overide = False
        elif self.LINK["multi"] == 2: #Server
            if self.SyncChangedServer(): #If drone has been moved by a client than cancel any navigation
                self.stopNavigation(0)
            bpos = [self.pos[0]+0,self.pos[1]+0]
            if self.number!=-1 and self.alive and time.time()>self.pause:
                self.SyncData(self.LINK["serv"].SYNC["e"+str(self.ID)]) #Sync the drones data to the world
            self.applyPhysics(lag)
            self.loop2(lag)
            self.changeMesh(bpos) #Move the drone to anouther MESH
            if self.REQUEST_DELETE:
                return None
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync() #Upload the data about the drone in the world to SYNC
        elif self.LINK["multi"]==1: #Sync our drone position with the servers version
            bpos = [self.pos[0]+0,self.pos[1]+0]
            if "e"+str(self.ID) in self.LINK["cli"].SYNC:
                self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)],lag)
            else:
                self.REQUEST_DELETE = True
            self.health = self.settings["health"]
            self.changeMesh(bpos) #Move the drone to anouther MESH
            for a in self.upgrades+self.PERM_UPG:
                a.clientLoop(lag)
            if not self.controller == "": #Fixes bug with player controlling multiple drones
                for a in self.LINK["drones"]:
                    if a!=self and a.controller == self.controller:
                        self.controller = ""
                        self.allowed = False
                        a.allowed = False
                        a.controller = ""
                        self.overide = True
                        a.overide = True
        elif self.LINK["multi"]==0: #Singple player
            self.loop2(lag)
            if self.LINK["currentScreen"].currentDrone!=self:
                self.discoverAround()
        if self.LINK["multi"]!=2: #Is not a server
            if self.beingSucked!=self.__suckChange: #Air vacuum status has changed
                self.__suckChange = self.beingSucked == True
                if self.beingSucked and self.LINK["particles"]: #IS being sucked out an airlock
                    self.__fillAirEffects() #Display particle effects
                else:
                    self.__airParts = [] #Remove all particle effects
            for a in self.__airParts: #Moving loop for all particle effects
                a.loop(lag)
        else: #Is a server
            if self.beingSucked!=self.__suckChange: #Air vacuum status has changed
                self.__suckChange = self.beingSucked == True
                if self.beingSucked: #Drone is being sucked out an airlock
                    AR = None
                    for a in self.paths: #Find airlock entity that the drone is being sucked towards
                        if a[0]==1:
                            if len(a[1])!=0:
                                AR = a[1][-1][2]
                    if not AR is None: #Found an airlock
                        self.LINK["Broadcast"]("duc",self.ID,AR.ID) #Make all clients know that this drone is being sucked out the airlock
                else: #Drone has stopped being sucked out an airlock
                    self.LINK["Broadcast"]("duc",self.ID,False)
    def __renderParticle(self,x,y,scale,alpha,surf,a): #Function to call when rendering an air strike
        pygame.draw.line(surf,(255,255,255),[x-(math.cos(a[2]/180*math.pi)*SUCK_SIZE*scale*a[3]),y-(math.sin(a[2]/180*math.pi)*SUCK_SIZE*scale*a[3])],[x+(math.cos(a[2]/180*math.pi)*SUCK_SIZE*scale*a[3]),y+(math.sin(a[2]/180*math.pi)*SUCK_SIZE*scale*a[3])],int(1*scale))
    def __fillAirEffects(self): #Creates particle effects for when drone is being sucked out the airlock
        for a in self.paths: #Go through all the paths of the drone and find one that is an airlock sucking type
            if a[0]==1: #Airlock sucktion path type
                last = [self.pos[0]+(self.size[0]/2),self.pos[1]+(self.size[1]/2)] #Used for particle positions
                for c in a[1]: #Go through every point of the path and add a particle effects for air strikes
                    ang = (math.atan2(last[1]-c[1],last[0]-c[0])*180/math.pi)+180 #Angle to last point
                    dist = math.sqrt(((last[0]-c[0])**2)+((last[1]-c[1])**2)) #Dist to last point
                    self.__airParts.append(self.LINK["render"].ParticleEffect(self.LINK,last[0],last[1],ang,0,10,0,10,0,None,dist/180,30,True)) #Add particle effect
                    self.__airParts[-1].renderParticle = self.__renderParticle #Particle render function
                    last = [c[0]+0,c[1]+0] #Make this point the last point for the next point
                break
    def aimTo(self,direction,lag): #Move in a direction
        dist2 = 0 #Angular distance from the entities angle and the targets angle
        if direction > self.angle: #This is an algorithm for turning in a proper direction smothly
            if direction - self.angle > 180:
                dist2 = 180 - (direction - 180 - self.angle)
                self.angle-=lag*(dist2**0.7)
            else:
                dist2 = direction - self.angle
                self.angle+=lag*(dist2**0.7)
        else:
            if self.angle - direction > 180:
                dist2 = 180 - (self.angle - 180 - direction)
                self.angle+=lag*(dist2**0.7)
            else:
                dist2 = self.angle - direction
                self.angle-=lag*(dist2**0.7)
        try:
            self.angle = int(self.angle) % 360 #Make sure this entitys angle is not out of range
        except:
            self.angle = int(cmath.phase(self.angle)) % 360 #Do the same before but unconvert it from a complex number
    def turn(self,DIR): #Turn the drone is a specific direction
        if self.aliveShow and self.allowed and time.time()>self.pause: #Drone is alive
            self.angle += DIR
            self.angle = self.angle%360 #Make sure the angle is between 0 and 360
            self.overide = True
            self.stopNavigation()
    def go(self,DIR): #Move forward/backward
        if self.aliveShow and self.allowed and time.time()>self.pause: #Drone is alive
            bpos = [self.pos[0]+0,self.pos[1]+0] #Before position
            self.overide = True
            self.pos[0]+=math.sin(self.angle/180*math.pi)*DIR*self.speed*-1
            self.pos[1]+=math.cos(self.angle/180*math.pi)*DIR*self.speed*-1
            pS = [self.pos[0]+0,self.pos[1]+0]
            self.applyPhysics() #Apply hit-box detection
            self.colision = pS!=self.pos #Tell anything outside this drone that it has colided with something (used in stealth upgrade)
            self.changeMesh(bpos) #Move the drone to anouther MESH
            self.stopNavigation()
    def __AddUpgrade(self,LINK): #Adds a new empty upgrade slot to the drone
        if len(self.__upgrades)>=5: #Maximum limit to the amount of upgrade slots allowed to be on a drone
            return 0
        self.settings["upgrades"].append(["",0,-1]) #Add the upgade to the default upgrade lists
        #Get all the upgrades availible
        adding = ["Empty"]
        for a in self.LINK["upgrade"]:
            if not a in ["base","swap","pickup","info"]:
                adding.append(a)
        if len(self.__upgrades)>=3: #Decide if it should put the Combo box left or right
            self.__upgrades.append(self.LINK["screenLib"].ComboBox(105,((len(self.__upgrades)-3)*35)+75,self.LINK,100,adding))
        else:
            self.__upgrades.append(self.LINK["screenLib"].ComboBox(5,(len(self.__upgrades)*35)+75,self.LINK,100,adding))
        self.__rightReload() #Reload the +, - and dmg buttons
    def __RemoveUpgrade(self,LINK): #Removes the last upgrade slot on a drone
        if len(self.__upgrades)<=1: #Needs to be atleast 1 upgrade slot left
            return 0
        self.settings["upgrades"].pop() #Remove the last item of the default upgrades
        self.__upgrades.pop() #Remove the last item of the upgrade combo box list.
        self.__rightReload() #Reload the +, - and dmg buttons
    def __damageUpgrade(self,LINK): #Damages the last upgrade
        self.settings["upgrades"][-1][1]+=1
        if self.settings["upgrades"][-1][1]>2:
            self.settings["upgrades"][-1][1] = 0
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,215)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
        self.__nameI = self.LINK["screenLib"].TextEntry(5,40,self.LINK,200,False,"Input name") #Name input feild
        self.__nameI.text = self.settings["name"]+"" #Put the name of the drone into the name feild
        self.__health = self.LINK["screenLib"].TextEntry(5,180,self.LINK,80,False,"HP") #Health input feild
        self.__health.text = str(self.settings["health"]) #Put the health of the drone into the input feild
        self.__label = self.LINK["screenLib"].Label(90,180,self.LINK,"/") #Put a label in between the two text feilds for drone health
        self.__maxHealth = self.LINK["screenLib"].TextEntry(120,180,self.LINK,80,False,"Max HP") #Maximum drone HP
        self.__maxHealth.text = str(self.settings["maxHealth"]) #Put the maximum drone HP in.
        self.__upgrades = [] #Used to store the upgrades widgets. This is a list of combo boxes
        #Get all the possible entities
        adding = ["Empty"]
        for a in self.LINK["upgrade"]:
            if not a in ["base","swap","pickup","info"]:
                adding.append(a)
        for i,a in enumerate(self.settings["upgrades"]):
            self.__upgrades.append(self.LINK["screenLib"].ComboBox(5+(int(i/3)*100),(i*35)+75-(int(i/3)*105),self.LINK,100,adding))
            if self.settings["upgrades"][i][0]!="":
                self.__upgrades[-1].select = adding.index(self.settings["upgrades"][i][0])
        del adding #Remove all the items to fix memory leaking.
        self.__rightReload() #Load the +, - and dmg button
    def __rightReload(self): #Reload some menu stuff
        if len(self.__upgrades)>=3: #Right
            self.__addButton = self.LINK["screenLib"].Button(105,((len(self.__upgrades)-3)*35)+75,self.LINK,"+",self.__AddUpgrade)
            self.__remButton = self.LINK["screenLib"].Button(125,((len(self.__upgrades)-3)*35)+75,self.LINK,"-",self.__RemoveUpgrade)
            self.__dmgButton = self.LINK["screenLib"].Button(150,((len(self.__upgrades)-3)*35)+75,self.LINK,"Dmg",self.__damageUpgrade)
        else: #Left
            self.__addButton = self.LINK["screenLib"].Button(5,(len(self.__upgrades)*35)+75,self.LINK,"+",self.__AddUpgrade)
            self.__remButton = self.LINK["screenLib"].Button(25,(len(self.__upgrades)*35)+75,self.LINK,"-",self.__RemoveUpgrade)
            self.__dmgButton = self.LINK["screenLib"].Button(50,(len(self.__upgrades)*35)+75,self.LINK,"Damage",self.__damageUpgrade)
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__nameI.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__addButton.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__remButton.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__dmgButton.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__health.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        self.__maxHealth.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
        for a in self.__upgrades: #Event loop for all the upgade widgets
            a.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-230:
            windowPos[1] = self.LINK["reslution"][1]-230
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        self.__nameI.render(self.__nameI.pos[0],self.__nameI.pos[1],1,1,self.__surface) #Render name input
        self.__addButton.render(self.__addButton.pos[0],self.__addButton.pos[1],1,1,self.__surface) #Render adding button
        self.__remButton.render(self.__remButton.pos[0],self.__remButton.pos[1],1,1,self.__surface) #Render remove button
        self.__dmgButton.render(self.__dmgButton.pos[0],self.__dmgButton.pos[1],1,1,self.__surface) #Render damage button
        self.__health.render(self.__health.pos[0],self.__health.pos[1],1,1,self.__surface) #Render health input area
        self.__label.render(self.__label.pos[0],self.__label.pos[1],1,1,self.__surface) #Render label
        self.__maxHealth.render(self.__maxHealth.pos[0],self.__maxHealth.pos[1],1,1,self.__surface) #Render max health input feild
        for i,a in enumerate(self.__upgrades): #Render all the upgrade widgets
            #Get a colour for the damage icon, some of these will flash
            if self.settings["upgrades"][i][1]==0: #Working
                col = (0,127+abs(math.cos(time.time()*3)*127),0)
            elif self.settings["upgrades"][i][1]==1: #Small damage
                col = (127+abs(math.cos(time.time()*3)*127),127+abs(math.cos(time.time()*3)*127),0)
            elif self.settings["upgrades"][i][1]==2: #Heavy damage
                col = (127+abs(math.cos(time.time()*3)*127),0,0)
            else:
                col = (255,255,255) #Error colour
            a.render(a.pos[0],a.pos[1],1,1,self.__surface) #Draw the widget
            #Draw the damage rating over the upgrade widget.
            if i>2:
                pygame.draw.rect(self.__surface,col,[105,((i-3)*35)+75,100,30],2)
            else:
                pygame.draw.rect(self.__surface,col,[5,(i*35)+75,100,32],2)
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
        if self.__nameI.text!="": #Replace the drones name if anything was entered
            self.settings["name"] = self.__nameI.text+""
        self.__nameI = None
        self.__addButton = None
        self.__remButton = None
        self.__dmgButton = None
        if self.__health.text.isnumeric(): #Replace the health of the drone if something numerical was entered
            self.settings["health"] = int(self.__health.text)
        self.__health = None
        if self.__maxHealth.text.isnumeric(): #Same as the IF statement before but for max health
            self.settings["maxHealth"] = int(self.__maxHealth.text)
        if self.settings["health"]>self.settings["maxHealth"]:
            self.settings["health"] = self.settings["maxHealth"]+0
        self.__maxHealth = None
        self.__label = None
        #Get all the possible entities
        adding = ["Empty"]
        for a in self.LINK["upgrade"]:
            if a!="base":
                adding.append(a)
        #Put the contents of all the upgrade widgets back into the default upgrade slots.
        for i,a in enumerate(self.__upgrades):
            if a.select==0:
                self.settings["upgrades"][i] = ["",0]
            else:
                self.settings["upgrades"][i][0] = adding[a.select]+""
        self.__upgrades = None
    def editMove(self,ents): #Fuel outlet is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (drone)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit:
            if self.__inRoom:
                if self.settings["health"] == 0:
                    surf.blit(self.getImage("droneDead"),(x,y))
                else:
                    surf.blit(self.getImage("droneNormal"),(x,y))
            else:
                surf.blit(self.getImage("droneDisabled"),(x,y))
        else:
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
            if self.settings["health"] == 0 or self.stealth:
                self.drawRotate(surf,x-((self.size[0]/2)*scale),y-((self.size[1]/2)*scale),self.getImage("droneDead"),self.angle)
            elif self.ID <= -1 and self.aliveShow: # Is a player drone
                self.drawRotate(surf,x-((self.size[0]/2)*scale),y-((self.size[1]/2)*scale),self.getImage("droneNormal"),self.angle)
                tex = self.LINK["font42"].render(str(self.number),16,(255,255,255))
                sx,sy = tex.get_size()
                tex = pygame.transform.scale(tex,(int(sx*scale*0.8),int(sy*scale*0.8)))
                sx,sy = tex.get_size()
                surf.blit(tex,(x+((self.size[0]/2)*scale)-(sx/3),y+((self.size[1]/2)*scale)-(sy/2)))
            else:
                self.drawRotate(surf,x-((self.size[0]/2)*scale),y-((self.size[1]/2)*scale),self.getImage("droneDisabled"),self.angle)
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def render(self,x,y,scale,Rang,surf=None,arcSiz=-1,eAng=None,isActive=False): #Render drone in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        if self.controller!="":
            if self.controller==self.LINK["currentScreen"].name: #Drone is this player and not others
                tex = self.LINK["font24"].render(self.controller,16,(0,255,0))
            else: #Drone is other player
                tex = self.LINK["font24"].render(self.controller,16,(0,255,255))
            sx2,sy2 = tex.get_size()
            surf.blit(tex,(x+(self.size[0]*scale*0.5)-(sx2/2),y-(20*scale)))
        ang = (self.angle+90)/180*math.pi #Used for centering model since its center is not exact
        if isActive: #Drone is the source of rendering, make it render despite arc
            Rang2 = None
            eAng2 = None
        else:
            Rang2 = Rang
            eAng2 = eAng
        PS = [x+(math.sin(ang)*0.5*scale)+(12*scale),y+(math.cos(ang)*0.5*scale)+(12*scale)]
        if self.LINK["simpleModels"]: #Enable/disable simple models
            simp = "Simple"
        else:
            simp = ""
        if self.__model!=3: #Is not model 3 (circle drone)
            modl = "drone"+str(self.__model)+simp
        if self.settings["health"]==0 or self.stealth: #Perminantly dead or in stealth mode
            col = (150,0,0)
        elif self.ID <= -1 and self.aliveShow: #Normal
            col = (255,255,255)
        else: #Disabled
            col = (255,255,0)
        if self.__model!=3: #Drone model is not 3
            self.__rModel.render(PS[0],PS[1],self.angle-90,scale/1.75,surf,col,Rang2,eAng2,arcSiz)
        else: #Drone model is 3
            self.__rModel.render(PS[0],PS[1],self.__hullRotate,scale/1.75,surf,col,Rang2,eAng2,arcSiz)
            self.__rModel2.render(PS[0],PS[1],self.angle-90,scale/1.75,surf,col,Rang2,eAng2,arcSiz)
        for a in self.__airParts: #Render all air particles
            a.render(x-((self.pos[0]-a.pos[0])*scale),y-((self.pos[1]-a.pos[1])*scale),scale,Rang,eAng,surf)

