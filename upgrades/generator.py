import upgrades.base as base
import math

class Main(base.Main):
    def __init__(self,LINK,ID=-1):
        self.init(LINK)
        self.ID = ID
        self.name = "generator"
        self.displayName = "Generator" #Name of the upgrade (displayed)
        self.damage = 0 #Damage to the upgrade.
        self.caller = ["generator"] #Commands this upgrade accepts
        self.__activeGenerator = None #The generator this upgrade is attached to
        self.hitFunction = self.GeneratorHit
    def commandAllowed(self,com): #Returns true if this command is allowed in the upgrade
        Droom = self.drone.findPosition()
        if Droom==-1: #Drone is not in anything
            return False
        elif type(Droom)!=self.getEnt("room"): #Drone is not inside a room
            return "Drone is not inside a room."
        elif not self.__activeGenerator is None: #Upgrade is allredey being used
            return "Allredey powering a generator"
        else: #Check if there are any generators in the room
            Ents = Droom.EntitiesInside()
            GeneratorObject = self.getEnt("generator")
            for a in Ents:
                if type(a)==GeneratorObject:
                    if a.alive:
                        if a.active:
                            return "Power inlet allredey powered"
                        else:
                            return True #Upgrade is valid
                    return "Power inlet is destroyed"
            return "No power inlet inside room"
    def moved(self,newDrone): #Upgrade was swapped
        if not self.__activeGenerator is None: #Is the upgade currently being used?
            self.__activeGenerator.active = False
            self.__activeGenerator = None
    def GeneratorHit(self,Gen): #Generator was hit, connecting...
        self.__activeGenerator = Gen
        Gen.active = True
        self.used = True
        if not "gen" in self.LINK["hintDone"]:
            self.LINK["hintDone"].append("gen")
    def loop(self,lag): #Event loop on this upgrade
        super().loop(lag)
        if not self.__activeGenerator is None: #Upgrade is currently in use and powering a generator
            dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(self.__activeGenerator.pos[0]+(self.__activeGenerator.size[0]/2)))**2) +
                            ((self.drone.pos[1]+(self.drone.size[1]/2)-(self.__activeGenerator.pos[1]+(self.__activeGenerator.size[1]/2)) )**2) )
            if dist>45 or not self.drone.alive: #Check distance to generator and disconnect if too far away
                self.__activeGenerator.active = False
                self.__activeGenerator = None
    def doCommand(self,com,usrObj=None): #Runs a command on this upgrade (only if sucsessful)
        Droom = self.drone.findPosition() #Get the drones room
        Ents = Droom.EntitiesInside() #Get all the entities inside the room the drone is in
        GeneratorObject = self.getEnt("generator")
        Closest = [-1,None]
        for a in Ents: #Go through all entities inside the room
            if type(a)==GeneratorObject: #Found a generator, calculating distance
                dist = math.sqrt( ((self.drone.pos[0]+(self.drone.size[0]/2)-(a.pos[0]+(a.size[0]/2)))**2) + 
                    ((self.drone.pos[1]+(self.drone.size[1]/2)-(a.pos[1]+(a.size[1]/2)) )**2) ) #Find distance
                if Closest[0]==-1 or dist<Closest[0]: #Has distance not been mesured before or distance is less and prevously known
                    Closest[0] = dist+0
                    Closest[1] = a
        self.headTowards(Closest[1])
        return "Navigating drone "+str(self.drone.number)+" to power inlet"
