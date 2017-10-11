#Do not run this file, it is a module!
import pygame, random, time
import entities.base as base

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the lure is inside a room
        self.size = [40,40] #Size of the lure
        self.health = 200 #Health of the lure
        self.__healthChange = 200 #Used to detect changes in health for the lure
        self.__lastDamage = 0 #Used to time when the lure was last attacked (used so it doesen't spam console)
        self.__beingDamaged = 0 #Is upgrade being damaged
        self.beingSucked = False #Make this entity suckable out of an airlock
        self.hintMessage = "This entity should not be spawned in map editor"
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["lure",self.ID,self.pos,self.health]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
        self.health = data[3]
    def SyncData(self,data): #Syncs the data with this lure
        #Allot of the data received is checked by IF statements, this is because this entity is designed to be spawned in so data may not sync
        if "x" and "y" in data:
            self.pos[0] = data["x"]
            self.pos[1] = data["y"]
        if "D" in data:
            if data["D"]: #Lure is being damaged
                self.__beingDamaged = time.time()+1.5
            else:
                self.__beingDamaged = 0
        if "A" in data: #Check if lure is alive
            self.alive = data["A"]
    def GiveSync(self): #Returns the synced data for this lure
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["D"] = time.time()<self.__beingDamaged #Is drone being damaged
        res["A"] = self.alive
        return res
    def loop2(self,lag): #Ran by singple player or server
        if self.health!=self.__healthChange and self.alive: #Health has changed
            self.__healthChange = self.health+0
            self.__beingDamaged = time.time()+1.5 #Make icon flash
            if time.time()>self.__lastDamage: #Check if this lure needs to output a line saying it was damaged
                ps = self.findPosition() #Find lures position
                if ps==-1 or type(ps)!=self.getEnt("room"): #Is invalid or not in a room
                    R = "<no room>"
                else: #In a room
                    R = "R"+str(ps.number)
                self.LINK["outputCommand"]("Lure in "+R+" was damaged",(255,255,0))
            self.__lastDamage = time.time()+6 #Don't notify any extra hits for 6 seconds (unless hit again then still don't post anything)
            if self.health<=0: #Lure is dead
                self.health = 0
                ps = self.findPosition() #Find lures position
                if ps==-1 or type(ps)!=self.getEnt("room"): #Is invalid or not in a room
                    R = "<no room>"
                else: #In a room
                    R = "R"+str(ps.number)
                self.LINK["outputCommand"]("Lure in "+R+" was destroyed",(255,0,0)) #Notify the user the lure was destroyed
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
    def sRender(self,x,y,scale,surf=None,edit=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if self.alive or self.health<=0: #Is the lure alive
            if time.time()<self.__beingDamaged and time.time()-int(time.time())>0.5: #Make damage icon flickr when being damaged
                surf.blit(self.getImage("lureDamage"),(x,y))
            else: #Render normaly
                surf.blit(self.getImage("lure"),(x,y))
        else: #Lure is dead
            surf.blit(self.getImage("lureDead"),(x,y))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
