import upgrades.base as base
import math

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "tow"
        self.caller = ["tow"]
        self.displayName = "Tow" #Name of the upgrade (displayed)
        self.__inUse = False #Is the upgrade currently being used
        self.__pullDrone = None #The drone this entity is pulling
        self.damage = 0 #Damage to the upgrade.
        self.hitFunction = self.hitDrone #Function to call once hit a drone
    def beingUsed(self): #Return True if the upgrade is towing someting (used for tutorial progression)
        return not self.__pullDrone is None
    def hitDrone(self,dr): #Hit target drone
        self.__pullDrone = dr
        self.__inUse = True
        self.LINK["outputCommand"]("Started towing",(255,255,0),False)
    def loop(self,lag): #Called continuesly
        super().loop(lag)
        if self.__inUse: #Upgrade is currently towing a drone
            sp = [self.drone.pos[0]+(self.drone.size[0]/2),self.drone.pos[1]+(self.drone.size[1]/2)] #Self center position
            ep = [self.__pullDrone.pos[0]+(self.__pullDrone.size[0]/2),self.__pullDrone.pos[1]+(self.__pullDrone.size[1]/2)] #Towing center position
            angle = math.atan2(sp[0]-ep[0],sp[1]-ep[1])*180/math.pi #Angle of the target
            angle = int(angle) % 360 #Put into the range 0-360
            #Make the towing drone go behind the current drone
            self.__pullDrone.forcePos = [self.drone.pos[0]-math.sin(angle/180*math.pi)*32,self.drone.pos[1]-math.cos(angle/180*math.pi)*32]
            if self.__pullDrone.REQUEST_DELETE or self.drone.REQUEST_DELETE: #If the entity should be deleted then make sure we don't assosiate this upgrade with keeping it alive
                self.__inUse = False
                self.__pullDrone = None
    def commandAllowed(self,com): #Is the command allowed
        Droom = self.drone.findPosition() #Get the drones position
        if Droom==-1: #Drone is outside map
            return False
        elif self.__inUse: #Upgrade is being used
            return True
        else:
            Ents = Droom.EntitiesInside() #Get all entities in the room/door
            Objects = [self.getEnt("drone"),self.getEnt("ShipUpgrade")] #Entitiy we are expecting
            Err = "No disabled drones/non-permanent upgrades found in room"
            for a in Ents: #Loop through every entitiy in the room/door
                if type(a) in Objects and a!=self.drone: #Drone that is dead
                    if type(a)==Objects[1]:
                        return True
                    if a.number==-1 or not a.alive: #Dead drone
                        if a.health==0 and a.number==-1:
                            Err = "Drone is destroyed beyond salvagable"
                        else:
                            return True
            return Err
    def doCommand(self,com,usrObj=None): #Execute the tow upgrade
        if self.__inUse: #Upgrade allredey in use, stop towinng
            self.__inUse = False
            self.__pullDrone = None
            return "Stopped towing"
        else: #Upgrade is not in use
            self.used = True
            Droom = self.drone.findPosition() #Get the room the drone is inside of
            Ents = Droom.EntitiesInside() #Get all the entities in the room/door
            Finding = [self.getEnt("drone"),self.getEnt("ShipUpgrade")] #Entities we are looking for
            Closest = [-1,None] #The closest item
            for a in Ents: #Find the closest drone/upgrade to the current drone
                if type(a) in Finding and a!=self.drone: #Entity is a drone and is not alive
                    ALO = False
                    if type(a)==Finding[1]:
                        ALO = True
                    elif a.number==-1 or not a.alive:
                        ALO = True
                    if ALO: #Entity is not alive/willing to tow
                        dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(a.pos[0]+(a.size[0]/2)))**2) + 
                            ((self.drone.pos[1]+(self.drone.size[1]/2)-(a.pos[1]+(a.size[1]/2)) )**2) ) #Find distance
                        if Closest[0]==-1 or dist<Closest[0]: #Has distance not been mesured before or distance is less and prevously known
                            Closest[0] = dist+0
                            Closest[1] = a
            self.headTowards(Closest[1],40) #Head towards drone