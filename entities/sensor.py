#Do not run this file, it is a module!
import pygame, random, time, math
import entities.base as base

SCAN_RATE = 10 #Scan a room 10 times a second
SENSOR_COL = (0,204,255) #Colour of the sensor in 3D

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.discovered = True
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the lure is inside a room
        self.renderAnyway = True
        self.size = [40,40] #Size of the sensor
        self.health = 200 #Health of the sensor
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]: #Simple models is enabled
                self.__sensor = LINK["render"].Model(LINK,"sensorSimple")
            else:
                self.__sensor = LINK["render"].Model(LINK,"sensor")
        self.__healthChange = 200 #Used to detect changes in health for the sensor
        self.__lastDamage = 0 #Used to time when the sensor was last attacked (used so it doesen't spam console)
        self.__beingDamaged = 0 #Is upgrade being damaged
        self.__room = None #Room the sensor is currently in
        self.__scan = 0 # Scan type
        self.__scanChange = 1 #Used to detect changes in scanning a room (so it notifies in consoles)
        self.__updateRate = time.time()+(1/SCAN_RATE) #Used to scan a room a specific amount of times a second
        self.beingSucked = False #Make this entity suckable out of an airlock
        self.hintMessage = "This entity should not be spawned in map editor"
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["sensor",self.ID,self.pos,self.health]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.health = data[3]
    def SyncData(self,data): #Syncs the data with this sensor
        #Allot of the data received is checked by IF statements, this is because this entity is designed to be spawned in so data may not sync
        if "x" and "y" in data:
            self.pos[0] = data["x"]
            self.pos[1] = data["y"]
        if "D" in data:
            if data["D"]: #Sensor is being damaged
                self.__beingDamaged = time.time()+1.5
            else:
                self.__beingDamaged = 0
        if "A" in data: #Check if sensor is alive
            self.alive = data["A"]
    def takeDamage(self,dmg,reason=""):
        self.health -= dmg
        if self.health<0:
            self.health = 0
            self.alive = False
    def afterLoad(self):
        self.__room = self.findPosition()
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def GiveSync(self): #Returns the synced data for this sensor
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["D"] = time.time()<self.__beingDamaged #Is sensor being damaged
        res["A"] = self.alive
        return res
    def loop2(self,lag): #Ran by singple player or server
        if self.health!=self.__healthChange and self.alive: #Health has changed
            self.__healthChange = self.health+0
            self.__beingDamaged = time.time()+1.5 #Make icon flash
            if time.time()>self.__lastDamage: #Check if this sensor needs to output a line saying it was damaged
                ps = self.findPosition() #Find sensors position
                if ps==-1 or type(ps)!=self.getEnt("room"): #Is invalid or not in a room
                    R = "<no room>"
                else: #In a room
                    R = ps.reference()
                self.LINK["outputCommand"]("Sensor in "+R+" is being attacked",(255,0,0),True)
            self.__lastDamage = time.time()+6 #Don't notify any extra hits for 6 seconds (unless hit again then still don't post anything)
            if self.health<=0: #Sensor is dead
                self.health = 0
                ps = self.findPosition() #Find sensors position
                if ps==-1 or type(ps)!=self.getEnt("room"): #Is invalid or not in a room
                    R = "<no room>"
                else: #In a room
                    R = ps.reference()
                self.LINK["outputCommand"]("Sensor in "+R+" was destroyed",(255,0,0),False) #Notify the user the lure was destroyed
                self.alive = False
    def loop(self,lag): #Constatnly called to handle events with this entity
        if self.LINK["multi"]==1: #Client
            if "e"+str(self.ID) in self.LINK["cli"].SYNC:
                self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=1: #Is not a client
            self.loop2(lag)
            self.movePath(lag)
        if not self.__room is None and time.time()>self.__updateRate and self.alive:
            self.__updateRate = time.time()+(1/SCAN_RATE)
            Ents = self.__room.EntitiesInside() #Get all entities inside the room
            self.__scan = 1 #Safe
            for a in Ents: #Go through all entities in the room
                if a.isNPC and a.alive: #Entity is NPC and alive
                    self.__scan = 2 #Bad
                    break
            if self.__scan!=self.__scanChange: #Scanning has changed, notify user('s)
                self.__scanChange = self.__scan + 0
                if self.__scan==2: #Bad
                    self.LINK["outputCommand"]("Sensor triggered in "+self.__room.reference(),(255,0,0),False)
                else: #Safe
                    self.LINK["outputCommand"]("Sensor un-triggered in "+self.__room.reference(),(255,255,0),False)
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.alive: #Is the sensor alive
            if time.time()<self.__beingDamaged and ((time.time()-int(time.time()))*4)%1>0.5: #Make damage icon flickr when being damaged
                surf.blit(self.getImage("sensorDamage"),(x-(12*scale),y-(12*scale)))
            else: #Render normaly
                surf.blit(self.getImage("sensor"),(x-(12*scale),y-(12*scale)))
        else: #Sensor is dead
            surf.blit(self.getImage("sensorDead"),(x-(12*scale),y-(12*scale)))
        if self.__scan!=0 and not self.__room is None and self.alive: #Inside room and scan is valid
            if self.__scan==1: #Bad
                col = (0,255,0)
            elif self.__scan==2: #Safe
                col = (255,0,0)
            else: #Error colour
                col = (0,255,255)
            perc = abs(math.sin((time.time()-int(time.time()))*math.pi/2))
            scrolPos = [(self.pos[0]*scale)-x,(self.pos[1]*scale)-y] #Scroll position of the view
            rpos = [(self.__room.pos[0]*scale)-scrolPos[0],(self.__room.pos[1]*scale)-scrolPos[1]] #Room position in screen coordinates
            pygame.draw.rect(surf,col,[x-((x-rpos[0])*perc),y-((y-rpos[1])*perc),self.__room.size[0]*scale*perc,self.__room.size[1]*scale*perc],int(2*scale))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,Dview=False): #Should the sensor render in scematic view
        return True
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render sensor in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        self.__sensor.render(x,y,0,scale/2,surf,SENSOR_COL,ang,eAng,arcSiz)
